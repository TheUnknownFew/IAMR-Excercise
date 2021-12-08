import functools
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Union, Optional

from flask_login import current_user, login_required

import database
from errors import UniquenessError


class PriceCode(Enum):
    """
    Notes & Considerations:
    These price codes can be expanded manually here in the PriceCode enum class, or price codes
    could be added to a 'codes' table within the database.
    The former would allow for theoretical administration access to expand the supported codes on
    the fly by the web applications.

    For the time being, an enum is being used for time's sake.
    """

    USD = 'USD'
    EURO = 'EUR'
    YEN = 'YEN'


def price_codes() -> list[str]:
    """Convenience function for accessing all the PriceCode enums as a list of strings."""
    return [c.value for c in PriceCode]


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
    Gives read-only access so the system may know what data exists.
    Values contained in this set are managed by the Vendor class as bins are created and removed.
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


cache_stalls_from_database = MarketMap.cache_stalls_from_database


@dataclass
class Bin:
    bin_id: str
    vendor_id: int
    product_name: str
    stock: float
    unit_price: float
    price_code: Union[PriceCode, str]

    def __post_init__(self):
        if isinstance(self.price_code, str):
            self.price_code = PriceCode[self.price_code]


@dataclass
class Vendor:
    vendor_id: int
    vendor_name: str
    vendor_email: str

    @login_required
    def create_bin(
            self,
            product_name: str,
            initial_stock: float,
            unit_price: float,
            price_code: PriceCode
    ) -> Optional[Bin]:
        """
        Adds a new bin for the vendor to the database. Returns the bin created or None if current vendor
        is unauthorized to create a bin.
        """
        # Owner Required in order to perform this transaction.
        if self.vendor_id != Vendor.current_user().vendor_id:
            return None

        bin_id = database.gen_uuid()
        params = (bin_id, self.vendor_id, product_name, initial_stock, unit_price, price_code.name)
        db = database.get_db()
        db.execute(
            """INSERT INTO bins(bin_id, vendor_id, product_name, stock, unit_price, price_code)
               VALUES (?, ?, ?, ?, ?, ?)""",
            params
        )
        db.commit()
        MarketMap.cache_stall(bin_id, self.vendor_id)
        return Bin(*params)

    def update_bin(
            self,
            bin_id: str, *,
            product_name: str = None,
            stock: float = None,
            price: tuple[float, PriceCode] = None
    ) -> Optional[Bin]:
        """
        Updates a bin a vendor owns with specified values to be replaced with.
        Returns the updated bin.
        Returns None if no update was made or the current vendor was not authorized to update a bin.
        """
        _bin = self.get_bin(bin_id)
        if _bin is None or not any((product_name, stock, price)):
            return None

        db = database.get_db()
        if product_name is not None:
            _bin.product_name = product_name
            db.execute(
                """UPDATE bins SET product_name = ? WHERE bin_id = ? AND vendor_id = ?""",
                (product_name, bin_id, self.vendor_id)
            )
        if stock is not None:
            _bin.stock = stock
            db.execute(
                """UPDATE bins SET stock = ? WHERE bin_id = ? AND vendor_id = ?""",
                (stock, bin_id, self.vendor_id)
            )
        if price is not None:
            unit_price, price_code = price
            _bin.unit_price = unit_price
            _bin.price_code = price_code
            db.execute(
                """UPDATE bins SET unit_price = ?, price_code = ? WHERE bin_id = ? AND vendor_id = ?""",
                (unit_price, price_code.name, bin_id, self.vendor_id)
            )
        db.commit()
        return _bin

    def remove_bin(self, bin_id: str) -> Optional[Bin]:
        _bin = self.get_bin(bin_id)
        if _bin is None:
            return None

        db = database.get_db()
        db.execute("""DELETE FROM bins WHERE bin_id = ? AND vendor_id = ?""", (_bin.bin_id, self.vendor_id))
        db.commit()
        MarketMap.dump_stall(_bin.bin_id)
        return _bin

    def get_bin(self, bin_id: str) -> Optional[Bin]:
        """Gets a bin belonging to vendor from given bin id. This method implicitly checks for login context."""
        bins = self.bins
        if bins is None:
            return None

        _bin = [b for b in bins if b.bin_id == bin_id]
        if len(_bin) == 0:
            return None
        if len(_bin) == 1:
            return _bin[0]
        # This should not be reached. Most likely handled by the database since bin_id is a primary key.
        raise UniquenessError(_bin, 'Queried for a single bin. Got multiple bins with the same id.')

    @property
    @login_required
    def bins(self) -> Optional[list[Bin]]:
        """
        Returns a list of bins belonging to the vendor.
        This method should only ever be called from methods decorated with @login_required, ensuring
        that the caller is authorized to view all bins from a given vendor.
        Returns None is current user is not authorized to view bins.
        """
        # Owner Required in order to perform this transaction.
        if self.vendor_id != Vendor.current_user().vendor_id:
            return None

        bins = database.get_db().execute("""SELECT * FROM bins WHERE vendor_id = ?""", (self.vendor_id,)).fetchall()
        return [Bin(*data) for data in bins]

    # ---------------------------------------
    # Flask-Login Required Definitions
    # ---------------------------------------

    @property
    def is_authenticated(self):
        """Flask-Login required implementation."""
        # Owner Required in order to perform this transaction.
        if self.vendor_id != Vendor.current_user().vendor_id:
            return False
        return True

    @property
    def is_active(self):
        """Flask-Login required implementation."""
        return True

    @property
    def is_anonymous(self):
        """Flask-Login required implementation."""
        return False

    def get_id(self) -> str:
        """Flask-Login required implementation."""
        return str(self.vendor_id)

    # ---------------------------------------
    # General Convenience methods.
    # ---------------------------------------

    @classmethod
    def get(cls, vendor_id: Optional[Union[str, int]]) -> Optional['Vendor']:
        """
        Gets vendor information from the database and serializes into a Vendor object.
        If no vendor exists with a given vendor id, None is returned.
        vendor_id: The vendor to access from the database.
        Returns A Vendor object or None if no vendor was found with a given Vendor id.
        """
        if vendor_id is None:
            return None
        vendor_data = database.get_db().execute(
            """SELECT vendor_id, vendor_name, vendor_email FROM vendors WHERE vendor_id = ?""", (int(vendor_id),)
        ).fetchone()
        return cls(*vendor_data) if vendor_data is not None else None

    @classmethod
    def current_user(cls) -> Optional['Vendor']:
        """Convenience function for accessing the current logged in vendor."""
        return cls.get(current_user.get_id())
