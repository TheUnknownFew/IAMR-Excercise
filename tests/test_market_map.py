import database
from models import MarketMap


def test_map_creation(mock_map):
    with mock_map.app_context():
        m_map = MarketMap()
        assert len(m_map.edges) == 7
        assert len(m_map.stalls) == 7


def test_connections(mock_map):
    with mock_map.app_context():
        m_map = MarketMap()
        path, distance = m_map.path_to_bin(
            MarketMap.VendorStall(2, database.gen_uuid(4)),     # From Vendor b: rice
            MarketMap.VendorStall(1, database.gen_uuid(3))      # To Vendor a: grape
        )
        assert distance == 13.0
        assert path == [
            MarketMap.VendorStall(2, database.gen_uuid(4)),     # Vendor b: rice
            MarketMap.VendorStall(1, database.gen_uuid(1)),     # Vendor a: apple
            MarketMap.VendorStall(2, database.gen_uuid(5)),     # Vendor b: soy sauce
            MarketMap.VendorStall(1, database.gen_uuid(3))      # Vendor a: grape
        ]
        print(path)


def test_remove_stall(mock_map):
    with mock_map.app_context():
        m_map = MarketMap()
        assert m_map.remove_stall(MarketMap.VendorStall(1, database.gen_uuid(2)))
        assert not m_map.remove_stall(MarketMap.VendorStall(1, database.gen_uuid(2)))
        assert len(m_map.edges) == 5
        assert len(m_map.stalls) == 6
        assert MarketMap.VendorStall(3, database.gen_uuid(6)) in m_map.stalls

        path, distance = m_map.path_to_bin(
            MarketMap.VendorStall(2, database.gen_uuid(4)),     # From Vendor b: rice
            MarketMap.VendorStall(3, database.gen_uuid(6))      # To Vendor c: carrot
        )
        assert len(path) == 0
        assert distance == float('inf')

        path, distance = m_map.path_to_bin(
            MarketMap.VendorStall(2, database.gen_uuid(4)),
            MarketMap.VendorStall(1, database.gen_uuid(3))
        )
        assert distance == 13.0
        assert path == [
            MarketMap.VendorStall(2, database.gen_uuid(4)),     # Vendor b: rice
            MarketMap.VendorStall(1, database.gen_uuid(1)),     # Vendor a: apple
            MarketMap.VendorStall(2, database.gen_uuid(5)),     # Vendor b: soy sauce
            MarketMap.VendorStall(1, database.gen_uuid(3))      # Vendor a: grape
        ]
