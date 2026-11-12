from subway_route_agent.data import Row, load_rows
from subway_route_agent.graph import TRANSFER_SECONDS, build_graph


def _edges(g, node):
    return {n: w for n, w in g[node]}


def test_branch_head_attaches_to_named_station():
    rows = [Row(5, "강동", 0), Row(5, "길동", 90), Row(5, "둔촌동", 110), Row(5, "올림픽공원", 100)]
    g = build_graph(rows)
    assert ("길동", 5) not in _edges(g, ("둔촌동", 5))
    assert _edges(g, ("둔촌동", 5))[("강동", 5)] == 110


def test_alias_and_transfer():
    rows = [Row(4, "사당", 0), Row(4, "총신대입구", 120), Row(7, "이수", 0), Row(7, "내방", 90)]
    g = build_graph(rows)
    assert ("총신대입구", 4) not in g
    assert _edges(g, ("이수", 4))[("이수", 7)] == _data_seconds(4, 7, "총신대입구", "이수")


def test_first_row_of_line_does_not_link_to_previous_line():
    rows = [Row(1, "청량리", 0), Row(2, "시청", 0), Row(2, "을지로입구", 90)]
    g = build_graph(rows)
    assert _edges(g, ("시청", 2)) == {("을지로입구", 2): 90}


def test_real_graph_branch_heads_and_alias_attach():
    # 연결만 보는 테스트는 BRANCH_HEADS·ALIASES를 비워도 통과한다. 이웃을 정확히 고정한다
    g = build_graph(load_rows())
    assert _edges(g, ("용답", 2)) == {("성수", 2): 180, ("신답", 2): 90}
    assert _edges(g, ("도림천", 2)) == {("신도림", 2): 90, ("양천구청", 2): 150}
    assert _edges(g, ("이수", 4))[("이수", 7)] == _data_seconds(4, 7, "총신대입구", "이수")
    assert ("총신대입구", 4) not in g


def test_real_graph_is_connected():
    g = build_graph(load_rows())
    seen, stack = {("서울역", 1)}, [("서울역", 1)]
    while stack:
        for n, _ in g[stack.pop()]:
            if n not in seen:
                seen.add(n)
                stack.append(n)
    assert seen == set(g)


def _data_seconds(line_from: int, line_to: int, *names: str) -> int:
    """환승 CSV를 csv 모듈로 직접 읽어 그 행의 소요 시간(초)을 구한다."""
    import csv

    from subway_route_agent.data import TRANSFER_DATA

    with open(TRANSFER_DATA, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if (r["환승역명"] in names and r["호선"] == str(line_from)
                    and r["환승노선"] == f"{line_to}호선"):
                m, s = r["환승소요시간"].split(":")
                return int(m) * 60 + int(s)
    raise AssertionError(f"{names} {line_from}→{line_to}호선 행이 환승 CSV에 없다")


def test_real_transfer_edge_uses_data_value():
    g = build_graph(load_rows())
    # 데이터의 역 이름은 총신대입구(4호선 쪽)와 이수(7호선 쪽) 둘이다. 둘 다 이수로 맞춘다
    assert _edges(g, ("이수", 4))[("이수", 7)] == _data_seconds(4, 7, "총신대입구", "이수")
    assert _edges(g, ("이수", 7))[("이수", 4)] == _data_seconds(7, 4, "총신대입구", "이수")


def test_real_transfer_edge_falls_back_to_opposite_direction():
    g = build_graph(load_rows())
    # 데이터에는 까치산 5→2호선 14초뿐이다. 2→5호선은 반대 방향 값을 쓴다
    assert _data_seconds(5, 2, "까치산") == 14
    assert _edges(g, ("까치산", 2))[("까치산", 5)] == 14
    assert _edges(g, ("까치산", 5))[("까치산", 2)] == 14


def test_transfer_without_data_stays_180():
    rows = [Row(1, "A", 0), Row(1, "B", 60), Row(2, "B", 0), Row(2, "C", 60)]
    g = build_graph(rows)  # 데이터에 없는 역
    assert _edges(g, ("B", 1))[("B", 2)] == TRANSFER_SECONDS
    real = [Row(4, "사당", 0), Row(4, "총신대입구", 120), Row(7, "이수", 0), Row(7, "내방", 90)]
    assert _edges(build_graph(real, transfers={}), ("이수", 4))[("이수", 7)] == TRANSFER_SECONDS


def test_count_transfers_on_real_graph():
    from subway_route_agent.data import load_transfers
    from subway_route_agent.graph import count_transfers

    g = build_graph(load_rows())
    c = count_transfers(g, load_transfers())
    assert c.directions == 78
    assert (c.direct, c.reverse, len(c.default), len(c.mismatch)) == (77, 1, 0, 0)
    assert (c.data_stations, len(c.default_stations)) == (35, 0)
    assert len(c.unused_rows) == 9
    unused = {(n, a, b) for n, a, b in c.unused_rows}
    assert ("성수", 2, 2) in unused and ("창동", 4, 1) in unused


def test_count_transfers_flags_default_and_mismatch():
    from subway_route_agent.graph import count_transfers

    rows = [Row(1, "A", 0), Row(1, "B", 60), Row(2, "B", 0), Row(2, "C", 60)]
    g = build_graph(rows, transfers={})
    c = count_transfers(g, {})
    assert (c.directions, c.direct, c.reverse, len(c.default)) == (2, 0, 0, 2)
    assert c.default_stations == ["B"] and c.data_stations == 0
    # 데이터에 값이 있는데 그래프가 180초를 쓰면 (라)다
    c2 = count_transfers(g, {("B", 1, 2): 50})
    assert len(c2.mismatch) == 2 and c2.reverse == 0 and len(c2.default) == 0
    assert c2.data_stations == 0  # 값이 다른 방향이 있는 환승역은 데이터 환승 시간을 쓴 역이 아니다
