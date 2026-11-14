"""LLM에게 주는 도구 셋. 정보만 주고, 여러 호선을 거치는 경로나 소요 시간은 계산해 주지 않는다."""

import heapq
import json
from functools import cache
from itertools import pairwise

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


def transfer_seconds(station: str, from_line: int, to_line: int) -> dict:
    """한 역에서 from_line에서 to_line으로 갈아타는 시간(초). 그래프의 환승 간선 값 그대로다."""
    g = _graph()
    name = _name(station)
    a, b = (name, from_line), (name, to_line)
    for line, node in ((from_line, a), (to_line, b)):
        if node not in g:
            return {"error": f"{station}은 {line}호선에 없다"}
    for nxt, w in g[a]:
        if nxt == b:
            return {"seconds": w}
    return {"error": f"{station}에서 {from_line}호선과 {to_line}호선을 갈아탈 수 없다"}


def route_seconds(path: list[dict]) -> dict:
    """고른 경로 [{station, line}]의 전체 소요 시간(환승 포함)과 환승 수. 경로는 돌려주지 않는다."""
    # grade → answerers → tools 순환을 피하려고 여기서 import한다
    from subway_route_agent.grade import fill_path, path_seconds

    if not path:
        return {"error": "경로가 비어 있다"}
    g = _graph()
    nodes: list[Node] = []
    for step in path:
        station, line = step["station"], step["line"]
        found = find_station(station)
        if not found["found"]:
            return {"error": f"{station}은 데이터에 없다", "candidates": found["candidates"]}
        if line not in found["lines"]:
            return {"error": f"{station}은 {line}호선에 없다", "lines": found["lines"]}
        nodes.append((found["station"], line))
    for i, pair in enumerate(pairwise(nodes), start=1):
        if fill_path(g, list(pair)) is None:
            return {"error": f"{i}번째와 {i + 1}번째를 이을 수 없다"}
    filled = fill_path(g, nodes)
    seconds = path_seconds(g, filled[0]) if filled else None
    if filled is None or seconds is None:
        return {"error": "경로를 이을 수 없다"}
    return {"seconds": seconds, "transfers": sum(a[1] != b[1] for a, b in pairwise(filled[0]))}


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

# route_seconds의 path는 answerers.SCHEMA의 path와 같은 구조다(answerers를 import하지 않는다)
_PATH = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {"station": _STR, "line": _INT},
        "required": ["station", "line"],
        "additionalProperties": False,
    },
}

# 잘게 나눈 도구: 일 하나씩 따로 부른다
FINE_TOOLS = [
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
    _tool(
        "transfer_seconds",
        "한 역에서 앞 호선에서 뒤 호선으로 갈아타는 시간(초)을 돌려준다. "
        "그 역이 두 호선에 없으면 오류를 돌려준다.",
        {"station": _STR, "from_line": _INT, "to_line": _INT},
    ),
]

# 크게 묶은 도구: 고른 경로를 통째로 재 준다. 경로는 돌려주지 않는다
COARSE_TOOLS = [
    _tool(
        "route_seconds",
        "고른 경로(역과 호선의 순서)의 전체 소요 시간(초, 환승 포함)과 환승 횟수를 돌려준다. "
        "중간 역은 빼도 된다. 데이터에 없는 역이면 이름이 비슷한 역 후보를, 그 호선에 없는 "
        "역이면 그 역이 지나는 호선을, 이을 수 없으면 몇 번째 역 사이인지를 돌려준다.",
        {"path": _PATH},
    ),
]

_FUNCS = {"find_station": find_station, "line_stations": line_stations,
          "travel_seconds": travel_seconds, "transfer_seconds": transfer_seconds,
          "route_seconds": route_seconds}
_TYPES = {"name": str, "from_station": str, "to_station": str, "station": str,
          "line": int, "from_line": int, "to_line": int}


def _valid_path(value) -> bool:
    return isinstance(value, list) and all(
        isinstance(s, dict) and set(s) == {"station", "line"} and isinstance(s["station"], str)
        and isinstance(s["line"], int) and not isinstance(s["line"], bool) for s in value)


def call_tool(name: str, arguments: str, tools: list[dict]) -> str:
    """도구 이름과 JSON 인자를 받아 결과를 JSON 문자열로 돌려준다. 실패는 예외 대신 error다.

    tools에 없는 이름은 다른 도구 구성의 도구라도 모르는 도구다.
    """
    spec_tool = next((t for t in tools if t["name"] == name), None)
    if spec_tool is None:
        return _dump({"error": f"모르는 도구: {name}"})
    try:
        args = json.loads(arguments)
    except json.JSONDecodeError:
        return _dump({"error": "인자가 JSON이 아니다"})
    spec = spec_tool["parameters"]["required"]
    if not isinstance(args, dict) or set(args) != set(spec):
        return _dump({"error": f"인자는 {', '.join(spec)}이어야 한다"})
    for key, value in args.items():
        if key == "path":
            ok = _valid_path(value)
        else:
            ok = isinstance(value, _TYPES[key]) and not isinstance(value, bool)
        if not ok:
            return _dump({"error": f"{key}의 형식이 다르다"})
    return _dump(_FUNCS[name](**args))


def _dump(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False)
