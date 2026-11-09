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
    assert _edges(g, ("이수", 4))[("이수", 7)] == TRANSFER_SECONDS


def test_first_row_of_line_does_not_link_to_previous_line():
    rows = [Row(1, "청량리", 0), Row(2, "시청", 0), Row(2, "을지로입구", 90)]
    g = build_graph(rows)
    assert _edges(g, ("시청", 2)) == {("을지로입구", 2): 90}


def test_real_graph_branch_heads_and_alias_attach():
    # 연결만 보는 테스트는 BRANCH_HEADS·ALIASES를 비워도 통과한다. 이웃을 정확히 고정한다
    g = build_graph(load_rows())
    assert _edges(g, ("용답", 2)) == {("성수", 2): 180, ("신답", 2): 90}
    assert _edges(g, ("도림천", 2)) == {("신도림", 2): 90, ("양천구청", 2): 150}
    assert _edges(g, ("이수", 4))[("이수", 7)] == TRANSFER_SECONDS
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
