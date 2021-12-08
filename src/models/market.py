import functools
from collections import deque
from dataclasses import dataclass

import database


class MarketMap:
    @dataclass(frozen=True)
    class VendorStall:
        """
        Stalls in the market map are identified as a bin belonging to a vendor.
        A connection in the MarketMap therefore is equivalent to two vertices:
        (vendor_id, bin_id) <-> (vendor_id, bin_id)
        """
        vendor_id: int
        bin_id: str

        def exists(self) -> bool:
            """
            Ensure that if a VendorStall was manually created, then modifications to
            the MarketMap will only be made if the stall is a valid stall.
            """
            return self.bin_id in MarketMap._vendor_stalls and self.vendor_id == MarketMap._vendor_stalls[self.bin_id].vendor_id

    @dataclass(frozen=True)
    class MapEdge:
        vendor_bin_id: str
        neighbor_bin_id: str
        distance: float

        @property
        def self_connecting(self) -> bool:
            return self.vendor_bin_id == self.neighbor_bin_id

        def __contains__(self, item) -> bool:
            return item == self.vendor_bin_id or item == self.neighbor_bin_id

    _vendor_stalls: dict[str, VendorStall] = {}
    """
    Values contained in this set are managed by the Vendor class as bins are created and removed.
    Ensures read-only access so bins are not modified in an unauthorized context.
    """

    def __init__(self, from_database: bool = True):
        self._market_map: dict[MarketMap.VendorStall, set[MarketMap.VendorStall]] = {}
        self._distance_map: dict[frozenset[MarketMap.VendorStall, MarketMap.VendorStall], float] = {}
        if from_database:
            for item in database.get_db().execute("""SELECT * FROM market_map"""):
                self.add_edge(MarketMap.MapEdge(*item))

    @property
    def edges(self):
        _edges = set()
        for stall, neighbors in self._market_map.items():
            for neighbor in neighbors:
                _edges.add(frozenset((stall.bin_id, neighbor.bin_id, self._distance_map[frozenset((stall, neighbor))])))
        return [MarketMap.MapEdge(*edge) for edge in _edges]

    @property
    def stalls(self) -> set[VendorStall]:
        """Returns a set containing all the stall nodes in the market map graph."""
        return set(self._market_map.keys())

    @functools.cache
    def calc_paths(self, from_stall: VendorStall) -> tuple[dict[VendorStall, float], dict[VendorStall, VendorStall]]:
        """
        An implementation of Dijkstra's algorithm made to work with the MarketMap graph implementation.
        Uses functools.cache to hopefully speed up results of the algorithm if a certain starting vendor stall
        is hit frequently.
        """
        stalls = self.stalls
        distance_to_stall: dict[MarketMap.VendorStall, float] = {stall: float('Inf') for stall in stalls}
        shortest_neighbor: dict[MarketMap.VendorStall, MarketMap.VendorStall] = {stall: None for stall in stalls}
        distance_to_stall[from_stall] = 0.0
        while len(stalls) > 0:
            min_stall = min(stalls, key=distance_to_stall.get)
            stalls.remove(min_stall)
            for neighbor in self._market_map[min_stall]:
                if neighbor not in stalls:
                    continue
                new_distance = distance_to_stall[min_stall] + self._distance_map[frozenset((neighbor, min_stall))]
                if new_distance < distance_to_stall[neighbor]:
                    distance_to_stall[neighbor] = new_distance
                    shortest_neighbor[neighbor] = min_stall
        return distance_to_stall, shortest_neighbor

    def path_to_bin(self, from_stall: VendorStall, to_stall: VendorStall) -> tuple[list[VendorStall], float]:
        """
        Returns a path from a stall to another stall and the total distance between the two stalls.
        Returns an empty list and float('inf') if there is no path between the stalls.
        """
        if not from_stall.exists() or not to_stall.exists():
            return [], float('inf')

        distance_to_stall, shortest_neighbor = self.calc_paths(from_stall)
        path_to = deque()
        current_stall = to_stall
        if shortest_neighbor[current_stall] is not None or current_stall == from_stall:
            while current_stall is not None:
                path_to.appendleft(current_stall)
                current_stall = shortest_neighbor[current_stall]
        total_dist = distance_to_stall[to_stall]
        if total_dist == float('inf'):
            path_to.clear()
        return list(path_to), total_dist

    def add_stall(self, stall: VendorStall) -> bool:
        """
        Add a stand-alone stall to the map. Can be connected with another stall via add_edge(...).
        Returns True if the stall was added to the map. Returns False if the stall is already in the map.
        """
        if stall in self._market_map:
            return False
        self._market_map[stall] = set()
        return True

    def remove_stall(self, stall: VendorStall) -> bool:
        """
        Removes a stall and all of its connecting edges from the market map graph.
        Returns True if the stall was removed from the map. Returns false if the stall is not in the map.
        """
        if stall not in self._market_map:
            return False
        # Remove all connections that reference stall since the graph is undirected.
        for neighbor in self._market_map[stall]:
            self._market_map[neighbor].remove(stall)
        self._market_map.pop(stall)
        return True

    def add_edge(self, edge: MapEdge) -> bool:
        """
        Adds a connecting edge to the market map graph.
        Returns True if the edge was added to the map.
        Returns False if the distance between the stalls is less than 0, either of the stalls were never created by an
        endpoint, or if the edge refers to a stall that connects to itself.
        """
        vendor_stall = MarketMap._vendor_stalls[edge.vendor_bin_id]
        neighbor_stall = MarketMap._vendor_stalls[edge.neighbor_bin_id]
        if edge.distance < 0 or not vendor_stall.exists() or not neighbor_stall.exists() or edge.self_connecting:
            return False
        if vendor_stall not in self._market_map:
            self._market_map[vendor_stall] = set()
        if neighbor_stall not in self._market_map:
            self._market_map[neighbor_stall] = set()
        self._market_map[vendor_stall].add(neighbor_stall)
        self._market_map[neighbor_stall].add(vendor_stall)
        self._distance_map[frozenset((vendor_stall, neighbor_stall))] = edge.distance
        return True

    @staticmethod
    def cache_stalls_from_database():
        """Refreshes _vendor_stalls with the current state of the database."""
        MarketMap._vendor_stalls.clear()
        for item in database.get_db().execute("""SELECT bin_id, vendor_id FROM bins"""):
            bin_id = item['bin_id']
            MarketMap._vendor_stalls[bin_id] = MarketMap.VendorStall(item['vendor_id'], bin_id)

    @staticmethod
    def cache_stall(bin_id: str, vendor_id: int):
        """Puts a vendor stall in the cache of vendor stall id pairs."""
        MarketMap._vendor_stalls[bin_id] = MarketMap.VendorStall(vendor_id, bin_id)

    @staticmethod
    def dump_stall(bin_id: str, *, update_map: 'MarketMap' = None):
        stall = MarketMap._vendor_stalls.pop(bin_id)
        if update_map is not None:
            update_map.remove_stall(stall)
