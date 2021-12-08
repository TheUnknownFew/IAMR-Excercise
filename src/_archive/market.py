from dataclasses import dataclass

import database

""" OLD: """
# _vendor_stalls: dict[str, 'VendorStall'] = {}
# """
# Gives read-only access so the system may know what data exists.
# Values contained in this set are managed by the Vendor class as bins are created and removed.
# """
#
#
# @dataclass(frozen=True)
# class VendorStall:
#     """
#     Stalls in the market map are identified as a bin belonging to a vendor.
#     A connection in the MarketMap therefore is equivalent to two vertices: (vendor_id, bin_id) <-> (vendor_id, bin_id)
#     """
#     vendor_id: int
#     bin_id: str
#
#     def exists(self) -> bool:
#         """
#         Ensure that if a VendorStall was manually created, then modifications to
#         the MarketMap will only be made if the stall is a valid stall.
#         """
#         return self.bin_id in _vendor_stalls and self.vendor_id == _vendor_stalls[self.bin_id].vendor_id
#
#
# def cache_stalls_from_database():
#     """Refreshes _vendor_stalls with the current state of the database."""
#     _vendor_stalls.clear()
#     for item in database.get_db().execute("""SELECT bin_id, vendor_id FROM bins"""):
#         bin_id = item['bin_id']
#         _vendor_stalls[bin_id] = VendorStall(item['vendor_id'], bin_id)
#
#
# @dataclass(frozen=True)
# class MapEdge:
#     vendor_bin_id: str
#     neighbor_bin_id: str
#     distance: float
#
#     @property
#     def self_connecting(self) -> bool:
#         return self.vendor_bin_id == self.neighbor_bin_id
#
#     def __contains__(self, item) -> bool:
#         return item == self.vendor_bin_id or item == self.neighbor_bin_id
#
#
# class MarketMap:
#     def __init__(self, from_database: bool = True):
#         self._market_map: dict[VendorStall, set[MapEdge]] = {}
#         if from_database:
#             for item in database.get_db().execute("""SELECT * FROM market_map"""):
#                 self.add_edge(MapEdge(*item))
#
#     @property
#     def stalls(self) -> set[VendorStall]:
#         return set(self._market_map.keys())
#
#     def remove_stall(self, stall: VendorStall) -> bool:
#         if stall not in self._market_map:
#             return False
#         # Remove all connections that reference stall since the graph is undirected.
#         for neighbor in self._market_map[stall]:
#             self._market_map[_vendor_stalls[neighbor.vendor_bin_id]].remove(neighbor)
#         self._market_map.pop(stall)
#         return True
#
#     def add_edge(self, edge: MapEdge) -> bool:
#         vendor_stall, neighbor_stall = _vendor_stalls[edge.vendor_bin_id], _vendor_stalls[edge.neighbor_bin_id]
#         if (edge.distance < 0 or not vendor_stall.exists() or not neighbor_stall.exists()) and edge.self_connecting:
#             return False
#         if vendor_stall not in self._market_map:
#             self._market_map[vendor_stall] = set()
#         if neighbor_stall not in self._market_map:
#             self._market_map[neighbor_stall] = set()
#         self._market_map[vendor_stall].add(edge)
#         self._market_map[neighbor_stall].add(edge)
#         return True

""" NEW: """
# class MarketMap:
#     @dataclass(frozen=True)
#     class VendorStall:
#         """
#         Stalls in the market map are identified as a bin belonging to a vendor.
#         A connection in the MarketMap therefore is equivalent to two vertices: (vendor_id, bin_id) <-> (vendor_id, bin_id)
#         """
#         vendor_id: int
#         bin_id: str
#
#         def exists(self) -> bool:
#             """
#             Ensure that if a VendorStall was manually created, then modifications to
#             the MarketMap will only be made if the stall is a valid stall.
#             """
#             return self.bin_id in MarketMap._vendor_stalls and self.vendor_id == MarketMap._vendor_stalls[self.bin_id].vendor_id
#
#     @dataclass(frozen=True)
#     class MapEdge:
#         vendor_bin_id: str
#         neighbor_bin_id: str
#         distance: float
#
#         @property
#         def self_connecting(self) -> bool:
#             return self.vendor_bin_id == self.neighbor_bin_id
#
#         def __contains__(self, item) -> bool:
#             return item == self.vendor_bin_id or item == self.neighbor_bin_id
#
#     _vendor_stalls: dict[str, VendorStall] = {}
#     """
#     Gives read-only access so the system may know what data exists.
#     Values contained in this set are managed by the Vendor class as bins are created and removed.
#     """
#
#     def __init__(self, from_database: bool = True):
#         self._market_map: dict[MarketMap.VendorStall, set[MarketMap.MapEdge]] = {}
#         if from_database:
#             for item in database.get_db().execute("""SELECT * FROM market_map"""):
#                 self.add_edge(MarketMap.MapEdge(*item))
#
#     @property
#     def stalls(self) -> set[VendorStall]:
#         return set(self._market_map.keys())
#
#     def remove_stall(self, stall: VendorStall) -> bool:
#         if stall not in self._market_map:
#             return False
#         # Remove all connections that reference stall since the graph is undirected.
#         for neighbor in self._market_map[stall]:
#             self._market_map[MarketMap._vendor_stalls[neighbor.vendor_bin_id]].remove(neighbor)
#         self._market_map.pop(stall)
#         return True
#
#     def add_edge(self, edge: MapEdge) -> bool:
#         vendor_stall, neighbor_stall = MarketMap._vendor_stalls[edge.vendor_bin_id], MarketMap._vendor_stalls[edge.neighbor_bin_id]
#         if (edge.distance < 0 or not vendor_stall.exists() or not neighbor_stall.exists()) and edge.self_connecting:
#             return False
#         if vendor_stall not in self._market_map:
#             self._market_map[vendor_stall] = set()
#         if neighbor_stall not in self._market_map:
#             self._market_map[neighbor_stall] = set()
#         self._market_map[vendor_stall].add(edge)
#         self._market_map[neighbor_stall].add(edge)
#         return True
#
#     @staticmethod
#     def cache_stalls_from_database():
#         """Refreshes _vendor_stalls with the current state of the database."""
#         MarketMap._vendor_stalls.clear()
#         for item in database.get_db().execute("""SELECT bin_id, vendor_id FROM bins"""):
#             bin_id = item['bin_id']
#             MarketMap._vendor_stalls[bin_id] = MarketMap.VendorStall(item['vendor_id'], bin_id)
