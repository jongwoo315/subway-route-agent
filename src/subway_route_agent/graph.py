from collections import defaultdict

from subway_route_agent.data import Row

Node = tuple[str, int]  # (역, 호선)
Graph = dict[Node, list[tuple[Node, int]]]

# CSV는 지선을 표시 없이 이어 붙였다. 이 행은 바로 위 행이 아니라 값의 역에 붙는다
BRANCH_HEADS = {(2, "용답"): "성수", (2, "도림천"): "신도림", (5, "둔촌동"): "강동"}
# 노선마다 이름이 다른 같은 역
ALIASES = {"총신대입구": "이수"}
# ponytail: 환승 시간 stub. 실제 값은 data.go.kr 15044419(환승역 거리·소요시간)로 바꾼다
TRANSFER_SECONDS = 180


def build_graph(rows: list[Row]) -> Graph:
    g: defaultdict[Node, list[tuple[Node, int]]] = defaultdict(list)
    prev: Node | None = None
    for r in rows:
        node = (ALIASES.get(r.station, r.station), r.line)
        g[node]  # 이웃이 없어도 노드는 만든다
        head = BRANCH_HEADS.get((r.line, r.station))
        if head:
            prev = (head, r.line)
        if prev is not None and prev[1] == r.line and r.seconds > 0:
            g[prev].append((node, r.seconds))
            g[node].append((prev, r.seconds))
        prev = node
    by_station: defaultdict[str, list[Node]] = defaultdict(list)
    for node in list(g):
        by_station[node[0]].append(node)
    for nodes in by_station.values():
        for a in nodes:
            for b in nodes:
                if a != b:
                    g[a].append((b, TRANSFER_SECONDS))
    return dict(g)
