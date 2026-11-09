from dataclasses import dataclass, field

from subway_route_agent.answerers import Answer
from subway_route_agent.graph import Graph, Node
from subway_route_agent.route import Route


@dataclass
class Grade:
    answered: bool
    correct: bool
    invented_stations: int = 0
    invented_time: int = 0
    violations: list[str] = field(default_factory=list)


def path_seconds(g: Graph, path: list[Node]) -> int | None:
    total = 0
    for a, b in zip(path, path[1:], strict=False):
        w = next((w for n, w in g.get(a, []) if n == b), None)
        if w is None:
            return None
        total += w
    return total


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def grade(g: Graph, q: dict, ans: Answer, truth: Route | None) -> Grade:
    if not ans.path:
        return Grade(answered=False, correct=False)
    stations = {n[0] for n in g}
    path = [tuple(n) for n in ans.path]
    actual = path_seconds(g, path)
    v = []
    if path[0][0] != q["origin"]:
        v.append("출발역 다름")
    if path[-1][0] != q["dest"]:
        v.append("도착역 다름")
    if actual is None:
        v.append("경로 끊김")
    transfers = sum(a[1] != b[1] for a, b in zip(path, path[1:], strict=False))
    if q["max_transfers"] is not None and transfers > q["max_transfers"]:
        v.append("환승 초과")
    if actual is not None and q["arrive_by"] and q["depart"]:
        if _minutes(q["depart"]) * 60 + actual > _minutes(q["arrive_by"]) * 60:
            v.append("시한 초과")
    invented_time = int(
        ans.seconds is not None and actual is not None and abs(ans.seconds - actual) > 60
    )
    return Grade(
        answered=True,
        correct=not v and truth is not None and actual == truth.seconds,
        invented_stations=sum(s not in stations for s, _ in path),
        invented_time=invented_time,
        violations=v,
    )
