from subway_route_agent.data import Row, load_rows
from subway_route_agent.graph import build_graph
from subway_route_agent.route import shortest

REAL = build_graph(load_rows())


def test_transfer_limit_forces_slower_route():
    rows = [
        Row(1, "A", 0), Row(1, "B", 60), Row(1, "C", 600),
        Row(2, "B", 0), Row(2, "C", 60),
    ]
    g = build_graph(rows)
    fast = shortest(g, "A", "C")
    assert fast.transfers == 1 and fast.seconds == 60 + 180 + 60
    direct = shortest(g, "A", "C", max_transfers=0)
    assert direct.transfers == 0 and direct.seconds == 660


def test_unknown_station_returns_none():
    assert shortest(REAL, "없는역", "강남") is None


def test_q1_matches_hand_count():
    r = shortest(REAL, "강남", "홍대입구", max_transfers=1)
    assert r.seconds == 1740 and r.transfers == 0


def test_q3_uses_macheon_branch():
    r = shortest(REAL, "방화", "마천", max_transfers=0)
    assert ("둔촌동", 5) in r.nodes and ("상일동", 5) not in r.nodes


def test_q2_needs_transfer():
    r = shortest(REAL, "서울역", "잠실")
    assert r.transfers >= 1
