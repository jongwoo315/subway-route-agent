"""LLM에게 주는 도구 셋. 정보만 주고, 여러 호선을 거치는 경로나 소요 시간은 계산해 주지 않는다."""

import heapq
import json
from functools import cache

from subway_route_agent.data import load_rows
from subway_route_agent.graph import ALIASES, BRANCH_HEADS, ONE_WAY, Graph, Node, build_graph

LINES = range(1, 9)
LINE_ERROR = "1~8호선만 있다"


@cache
def _rows():
    return load_rows()


@cache
def _graph() -> Graph:
    return build_graph(_rows())


def _name(station: str) -> str:
    return ALIASES.get(station, station)


def find_station(name: str) -> dict:
    station = _name(name)
    lines = sorted({n[1] for n in _graph() if n[0] == station})
    if lines:
        return {"found": True, "station": station, "lines": lines}
    names = sorted({n[0] for n in _graph() if name in n[0]})
    return {"found": False, "candidates": names[:10]}


def line_stations(line: int) -> dict:
    if line not in LINES:
        return {"error": LINE_ERROR}
    segments = []
    prev: Node | None = None
    for r in _rows():
        if r.line != line:
            continue
        node = (_name(r.station), line)
        head = BRANCH_HEADS.get((line, r.station))
        if head:
            prev = (head, line)
        if prev is not None and r.seconds > 0:
            segments.append({
                "from": prev[0], "to": node[0], "seconds": r.seconds,
                "one_way": node in ONE_WAY or prev in ONE_WAY,
            })
        prev = node
    return {"line": line, "segments": segments}


def travel_seconds(line: int, from_station: str, to_station: str) -> dict:
    """한 호선 안에서만, 갈아타지 않고 두 역 사이를 갈 때의 소요 시간(초)."""
    if line not in LINES:
        return {"error": LINE_ERROR}
    g = _graph()
    start, goal = (_name(from_station), line), (_name(to_station), line)
    for station, node in ((from_station, start), (to_station, goal)):
        if node not in g:
            return {"error": f"{station}은 {line}호선에 없다"}
    best = {start: 0}
    pq = [(0, start)]
    while pq:
        sec, node = heapq.heappop(pq)
        if node == goal:
            return {"seconds": sec}
        if sec > best[node]:
            continue
        for nxt, w in g[node]:
            if nxt[1] != line:  # 환승 간선은 쓰지 않는다
                continue
            if sec + w < best.get(nxt, float("inf")):
                best[nxt] = sec + w
                heapq.heappush(pq, (sec + w, nxt))
    return {"error": f"{from_station}에서 {to_station}까지 {line}호선만으로 갈 수 없다"}


def _tool(name: str, description: str, properties: dict) -> dict:
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        },
        "strict": True,
    }


_STR = {"type": "string"}
_INT = {"type": "integer"}

TOOLS = [
    _tool(
        "find_station",
        "역 이름으로 그 역을 지나는 호선 목록을 돌려준다. 없는 이름이면 이름에 그 글자가 "
        "들어간 역 후보를 돌려준다.",
        {"name": _STR},
    ),
    _tool(
        "line_stations",
        "호선 하나의 구간 목록을 돌려준다. 구간마다 출발 역, 도착 역, 소요 시간(초), "
        "한 방향으로만 가는 구간인지가 들어 있다.",
        {"line": _INT},
    ),
    _tool(
        "travel_seconds",
        "한 호선 안에서 갈아타지 않고 두 역 사이를 갈 때의 소요 시간(초)을 돌려준다. "
        "두 역이 그 호선에 없으면 오류를 돌려준다.",
        {"line": _INT, "from_station": _STR, "to_station": _STR},
    ),
]

_FUNCS = {"find_station": find_station, "line_stations": line_stations,
          "travel_seconds": travel_seconds}
_TYPES = {"name": str, "from_station": str, "to_station": str, "line": int}


def call_tool(name: str, arguments: str) -> str:
    """도구 이름과 JSON 인자를 받아 결과를 JSON 문자열로 돌려준다. 실패는 예외 대신 error다."""
    func = _FUNCS.get(name)
    if func is None:
        return _dump({"error": f"모르는 도구: {name}"})
    try:
        args = json.loads(arguments)
    except json.JSONDecodeError:
        return _dump({"error": "인자가 JSON이 아니다"})
    spec = next(t for t in TOOLS if t["name"] == name)["parameters"]["required"]
    if not isinstance(args, dict) or set(args) != set(spec):
        return _dump({"error": f"인자는 {', '.join(spec)}이어야 한다"})
    for key, value in args.items():
        if not isinstance(value, _TYPES[key]) or isinstance(value, bool):
            return _dump({"error": f"{key}의 형식이 다르다"})
    return _dump(func(**args))


def _dump(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False)
