from collections import defaultdict
from dataclasses import dataclass, field

from subway_route_agent.data import Row, load_transfers

Node = tuple[str, int]  # (역, 호선)
Graph = dict[Node, list[tuple[Node, int]]]

# CSV는 지선을 표시 없이 이어 붙였다. 이 행은 바로 위 행이 아니라 값의 역에 붙는다
BRANCH_HEADS = {(2, "용답"): "성수", (2, "도림천"): "신도림", (5, "둔촌동"): "강동"}
# 6호선 응암순환은 CSV 행 순서(응암→역촌→…→구산→응암) 한 방향으로만 달린다.
# 이 역에 닿거나 이 역에서 떠나는 간선은 CSV 방향으로만 만든다
ONE_WAY = {(s, 6) for s in ("역촌", "불광", "독바위", "연신내", "구산")}
# 노선마다 이름이 다른 같은 역
ALIASES = {"총신대입구": "이수"}
# 데이터에 양방향 다 없는 환승에만 쓴다
TRANSFER_SECONDS = 180


Transfers = dict[tuple[str, int, int], int]


def _by_graph_name(transfers: Transfers) -> Transfers:
    return {(ALIASES.get(n, n), a, b): s for (n, a, b), s in transfers.items()}


def build_graph(rows: list[Row], transfers: Transfers | None = None) -> Graph:
    """transfers: (역, 앞 호선, 뒤 호선) → 초. None이면 환승 데이터를 읽고, {}면 전부 180초다."""
    seconds = _by_graph_name(load_transfers() if transfers is None else transfers)
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
            if node not in ONE_WAY and prev not in ONE_WAY:
                g[node].append((prev, r.seconds))
        prev = node
    by_station: defaultdict[str, list[Node]] = defaultdict(list)
    for node in list(g):
        by_station[node[0]].append(node)
    for station, nodes in by_station.items():
        for a in nodes:
            for b in nodes:
                if a != b:
                    w = seconds.get((station, a[1], b[1]), seconds.get((station, b[1], a[1])))
                    g[a].append((b, TRANSFER_SECONDS if w is None else w))
    return dict(g)


@dataclass
class TransferCounts:
    directions: int = 0  # 갈아타는 방향 (역, 앞 호선 → 뒤 호선)
    direct: int = 0  # (가) 그 방향의 데이터 값을 쓴 방향
    reverse: int = 0  # (나) 반대 방향의 데이터 값을 쓴 방향
    # (다) 데이터에 양쪽 다 없어 180초가 남은 방향
    default: list[tuple[str, int, int]] = field(default_factory=list)
    # (라) 데이터에 값이 있는데 그래프 간선이 다른 값인 방향
    mismatch: list[tuple[str, int, int]] = field(default_factory=list)
    data_stations: int = 0  # 모든 방향이 (가)·(나)인 환승역
    default_stations: list[str] = field(default_factory=list)  # 방향 하나라도 (다)인 환승역
    # 그래프에 안 쓰인 데이터 행
    unused_rows: list[tuple[str, int, int]] = field(default_factory=list)


def count_transfers(g: Graph, transfers: Transfers) -> TransferCounts:
    """갈아타는 간선을 환승 데이터와 맞춰 방향 수, 환승역 수, 안 쓰인 데이터 행을 센다."""
    seconds = _by_graph_name(transfers)
    c = TransferCounts()
    bad: set[str] = set()  # 180초가 남은 환승역
    off: set[str] = set()  # 방향 하나라도 (다)·(라)인 환승역
    stations: set[str] = set()
    for (station, a), edges in g.items():
        for (to_station, b), w in edges:
            if to_station != station or a == b:
                continue
            stations.add(station)
            c.directions += 1
            fwd, rev = seconds.get((station, a, b)), seconds.get((station, b, a))
            if fwd is None and rev is None:
                c.default.append((station, a, b))
                bad.add(station)
                off.add(station)
            elif w != (fwd if fwd is not None else rev):
                c.mismatch.append((station, a, b))
                off.add(station)
            elif fwd is not None:
                c.direct += 1
            else:
                c.reverse += 1
    c.default_stations = sorted(bad)
    c.data_stations = len(stations - off)
    c.unused_rows = [k for k in transfers
                     if k[1] == k[2] or (ALIASES.get(k[0], k[0]), k[1]) not in g
                     or (ALIASES.get(k[0], k[0]), k[2]) not in g]
    return c
