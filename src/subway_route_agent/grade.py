import heapq
from dataclasses import dataclass, field
from itertools import pairwise

from subway_route_agent.answerers import Answer
from subway_route_agent.graph import Graph, Node
from subway_route_agent.route import Route


@dataclass
class Grade:
    answered: bool
    correct: bool
    invented_stations: int = 0
    invented_time: int = 0
    filled: int = 0  # 채점이 채운 역 수. 못 채우면 0
    violations: list[str] = field(default_factory=list)


def path_seconds(g: Graph, path: list[Node]) -> int | None:
    total = 0
    for a, b in pairwise(path):
        w = next((w for n, w in g.get(a, []) if n == b), None)
        if w is None:
            return None
        total += w
    return total


def _on_line(g: Graph, start: Node, goal: Node) -> list[Node] | None:
    """start와 goal(같은 호선) 사이, 그 호선 간선만으로 가는 가장 짧은 길. 환승 간선은 안 쓴다."""
    line = start[1]
    best = {start: 0}
    prev: dict[Node, Node] = {}
    pq = [(0, start)]
    while pq:
        sec, node = heapq.heappop(pq)
        if node == goal:
            path = [node]
            while path[-1] != start:
                path.append(prev[path[-1]])
            return path[::-1]
        if sec > best[node]:
            continue
        for nxt, w in g.get(node, []):
            if nxt[1] == line and sec + w < best.get(nxt, float("inf")):
                best[nxt] = sec + w
                prev[nxt] = node
                heapq.heappush(pq, (sec + w, nxt))
    return None


def fill_path(g: Graph, path: list[Node]) -> tuple[list[Node], int] | None:
    """답 경로에서 이웃하지 않게 붙은 두 노드 사이의 빠진 역을 채운다. (채운 경로, 채운 역 수).

    규칙 1: 같은 호선이면 그 호선 간선만으로 가장 짧은 길. 순환선은 짧은 쪽이다.
    규칙 2: 호선이 다르고 뒤 역이 앞 호선에도 있으면 갈아타는 역을 한 번만 쓴 것이다.
    그 밖이거나 데이터에 없는 노드가 있으면 못 채우고 None이다.
    """
    out = [path[0]]
    filled = 0
    for a, b in pairwise(path):
        if any(n == b for n, _ in g.get(a, [])):
            out.append(b)
            continue
        if a not in g or b not in g or a == b:
            return None
        if a[1] == b[1]:
            seg = _on_line(g, a, b)
        else:
            via = (b[0], a[1])  # 갈아타는 역을 앞 호선으로 한 번 더 쓴다
            seg = _on_line(g, a, via) if via in g else None
            if seg is not None:
                seg.append(b)
        if seg is None:
            return None
        out += seg[1:-1] + [b]
        filled += len(seg) - 2
    return out, filled


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def grade(g: Graph, q: dict, ans: Answer, truth: Route | None) -> Grade:
    if not ans.path:
        return Grade(answered=False, correct=False)
    stations = {n[0] for n in g}
    given = [tuple(n) for n in ans.path]
    fill = fill_path(g, given)
    path, filled = fill if fill else (given, 0)
    actual = path_seconds(g, path)
    v = []
    if path[0][0] != q["origin"]:
        v.append("출발역 다름")
    if path[-1][0] != q["dest"]:
        v.append("도착역 다름")
    if actual is None:
        v.append("경로 끊김")
    transfers = sum(a[1] != b[1] for a, b in pairwise(path))
    if q.get("max_transfers") is not None and transfers > q["max_transfers"]:
        v.append("환승 초과")
    if actual is not None and q.get("arrive_by") and q.get("depart"):
        if _minutes(q["depart"]) * 60 + actual > _minutes(q["arrive_by"]) * 60:
            v.append("시한 초과")
    invented_time = int(
        ans.seconds is not None and actual is not None and abs(ans.seconds - actual) > 60
    )
    return Grade(
        answered=True,
        correct=not v and truth is not None and actual == truth.seconds,
        invented_stations=sum(s not in stations for s, _ in given),
        invented_time=invented_time,
        filled=filled,
        violations=v,
    )
