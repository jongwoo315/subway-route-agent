import heapq
from dataclasses import dataclass

from subway_route_agent.graph import Graph, Node


@dataclass
class Route:
    nodes: list[Node]
    seconds: int
    transfers: int


def shortest(g: Graph, origin: str, dest: str, max_transfers: int | None = None) -> Route | None:
    """상태를 (노드, 환승 횟수)로 늘린 다익스트라. 환승 상한이 있어도 최단을 구한다."""
    pq = [(0, 0, n, (n,)) for n in g if n[0] == origin]
    heapq.heapify(pq)
    done: set[tuple[Node, int]] = set()
    while pq:
        sec, tr, node, path = heapq.heappop(pq)
        if node[0] == dest:
            return Route(list(path), sec, tr)
        if (node, tr) in done:
            continue
        done.add((node, tr))
        for nxt, w in g[node]:
            ntr = tr + (nxt[1] != node[1])
            if max_transfers is not None and ntr > max_transfers:
                continue
            heapq.heappush(pq, (sec + w, ntr, nxt, path + (nxt,)))
    return None
