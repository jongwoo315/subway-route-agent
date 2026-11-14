import csv
import json
from itertools import pairwise

import pytest

from subway_route_agent.data import ROOT, TRANSFER_DATA, load_rows, load_transfers, parse_mmss
from subway_route_agent.tools import (
    COARSE_TOOLS,
    FINE_TOOLS,
    call_tool,
    find_station,
    line_stations,
    route_seconds,
    transfer_seconds,
    travel_seconds,
)

QUESTIONS = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))


def test_find_station_returns_lines_ascending():
    assert find_station("강남") == {"found": True, "station": "강남", "lines": [2]}
    res = find_station("서울역")
    assert res["found"] and res["lines"] == [1, 4]


def test_find_station_applies_alias_to_graph_name():
    assert find_station("총신대입구") == {"found": True, "station": "이수", "lines": [4, 7]}


def test_find_station_unknown_name_lists_candidates_sorted_and_capped():
    res = find_station("없는역")
    assert res == {"found": False, "candidates": []}
    res = find_station("대")  # 이름에 '대'가 든 역은 10개를 넘는다
    assert res["found"] is False
    assert len(res["candidates"]) == 10
    assert res["candidates"] == sorted(res["candidates"])
    assert all("대" in c for c in res["candidates"])
    assert find_station("홍대")["candidates"] == ["홍대입구"]


def test_line_stations_segment_count_and_branches():
    rows2 = [r for r in load_rows() if r.line == 2]
    res = line_stations(2)
    segs = res["segments"]
    assert res["line"] == 2 and len(segs) == len(rows2) - 1
    assert set(segs[0]) == {"from", "to", "seconds", "one_way"}
    by_to = {s["to"]: s for s in segs}
    assert by_to["용답"]["from"] == "성수"
    assert by_to["도림천"]["from"] == "신도림"
    assert segs[[s["to"] for s in segs].index("용답") - 1]["to"] == "시청"
    last_main = next(s for s in segs if s["to"] == "시청" and s["from"] == "충정로")
    assert last_main["seconds"] == 90
    assert not any(s["one_way"] for s in segs)


def test_line_stations_line5_branch_and_line6_one_way_loop():
    assert {s["to"]: s["from"] for s in line_stations(5)["segments"]}["둔촌동"] == "강동"
    one_way = {(s["from"], s["to"]) for s in line_stations(6)["segments"] if s["one_way"]}
    assert ("응암", "역촌") in one_way and ("구산", "응암") in one_way
    assert ("역촌", "불광") in one_way


def test_line_stations_rejects_other_lines():
    for bad in (0, 9):
        assert line_stations(bad) == {"error": "1~8호선만 있다"}


def test_travel_seconds_matches_hand_values():
    q1 = next(q for q in QUESTIONS if q["id"] == "q1")
    q3 = next(q for q in QUESTIONS if q["id"] == "q3")
    assert q1["hand_seconds"] == 1740
    assert travel_seconds(2, "강남", "홍대입구") == {"seconds": 1740}
    assert travel_seconds(5, "방화", "마천") == {"seconds": q3["hand_seconds"]}


def test_travel_seconds_uses_alias_and_branch():
    assert "seconds" in travel_seconds(4, "총신대입구", "사당")
    assert "seconds" in travel_seconds(2, "용답", "성수")


def test_travel_seconds_never_crosses_lines():
    # 서울역(1·4호선) → 잠실(2·8호선): 한 호선에 같이 없다. 갈아타는 길을 계산하면 안 된다
    for line in (1, 2, 4, 8):
        res = travel_seconds(line, "서울역", "잠실")
        assert "error" in res and "seconds" not in res
    assert travel_seconds(2, "서울역", "잠실")["error"] == "서울역은 2호선에 없다"


def test_travel_seconds_follows_one_way_loop_direction():
    # 응암순환은 응암→역촌→불광→독바위→연신내→구산→응암 한 방향이다
    assert travel_seconds(6, "응암", "역촌") == {"seconds": 100}
    assert travel_seconds(6, "역촌", "응암") == {"seconds": 80 + 80 + 130 + 80 + 120}


def test_travel_seconds_same_station_is_zero_and_unknown_station_is_error():
    assert travel_seconds(2, "강남", "강남") == {"seconds": 0}
    assert travel_seconds(2, "강남", "없는역") == {"error": "없는역은 2호선에 없다"}
    assert "error" in travel_seconds(9, "강남", "홍대입구")


def test_tools_module_does_not_import_shortest():
    src = (ROOT / "src" / "subway_route_agent" / "tools.py").read_text(encoding="utf-8")
    assert "shortest" not in src


def test_tools_definitions_are_strict_function_tools_without_recommendation_words():
    assert [t["name"] for t in FINE_TOOLS] == [
        "find_station", "line_stations", "travel_seconds", "transfer_seconds"]
    assert [t["name"] for t in COARSE_TOOLS] == ["route_seconds"]
    for t in [*FINE_TOOLS, *COARSE_TOOLS]:
        assert t["type"] == "function" and t["strict"] is True
        params = t["parameters"]
        assert params["additionalProperties"] is False
        assert set(params["required"]) == set(params["properties"])
        for word in ("최단", "추천", "가장 빠"):
            assert word not in t["description"]


def test_call_tool_runs_by_name_and_returns_json_string():
    out = call_tool("find_station", json.dumps({"name": "강남"}), FINE_TOOLS)
    assert json.loads(out) == {"found": True, "station": "강남", "lines": [2]}
    out = call_tool(
        "travel_seconds",
        json.dumps({"line": 2, "from_station": "강남", "to_station": "홍대입구"}),
        FINE_TOOLS,
    )
    assert json.loads(out) == {"seconds": 1740}
    assert json.loads(call_tool("line_stations", json.dumps({"line": 7}), FINE_TOOLS))["line"] == 7


@pytest.mark.parametrize(
    "name,args",
    [
        ("없는도구", "{}"),
        ("travel_seconds", "not json"),
        ("find_station", "{}"),
        ("find_station", json.dumps({"name": 3})),
        ("line_stations", json.dumps({"line": "2"})),
        ("travel_seconds", json.dumps({"line": 2, "from_station": "강남"})),
        ("find_station", json.dumps([1])),
    ],
)
def test_call_tool_bad_name_or_arguments_returns_error_json(name, args):
    assert "error" in json.loads(call_tool(name, args, FINE_TOOLS))


def test_travel_seconds_does_not_use_transfer_edges():
    # 두 역이 같은 호선에 있고 다른 호선으로 갈아타면 더 빨라지는 쌍이다.
    # 환승 간선을 쓰면 값이 작아진다: 시청→교대 1200, 강남→시청 1470, 지축→오금 2900
    assert travel_seconds(2, "시청", "교대") == {"seconds": 1830}
    assert travel_seconds(2, "강남", "시청") == {"seconds": 1740}
    assert travel_seconds(3, "지축", "오금") == {"seconds": 3090}


def test_line_stations_matches_graph_edges_for_every_line():
    from subway_route_agent.tools import _graph

    g = _graph()
    for line in range(1, 9):
        expected = {(a[0], b[0], w) for a, edges in g.items() if a[1] == line
                    for b, w in edges if b[1] == line}
        got = set()
        for s in line_stations(line)["segments"]:
            got.add((s["from"], s["to"], s["seconds"]))
            if not s["one_way"]:
                got.add((s["to"], s["from"], s["seconds"]))
        assert got == expected, line


# ---- #190: 환승 시간 도구와 경로 소요 시간 도구 ----

COARSE_KEYS = {"seconds", "transfers", "error", "candidates", "lines"}


def _csv_transfer(station, a, b):
    """환승 CSV에서 (역, 앞 호선 a → 뒤 호선 b) 초를 읽는다. 테스트가 기대값을 직접 읽는다."""
    with open(TRANSFER_DATA, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["환승역명"].strip() == station and r["호선"] == str(a) \
                    and r["환승노선"].strip() == f"{b}호선":
                return parse_mmss(r["환승소요시간"])
    raise AssertionError((station, a, b))


def test_transfer_seconds_matches_transfer_csv_in_both_directions():
    assert transfer_seconds("총신대입구", 4, 7) == {"seconds": _csv_transfer("총신대입구", 4, 7)}
    assert transfer_seconds("이수", 7, 4) == {"seconds": _csv_transfer("이수", 7, 4)}
    # 까치산 2→5는 CSV에 5→2만 있다. 그래프가 반대 방향 값을 쓴다
    assert transfer_seconds("까치산", 2, 5) == {"seconds": _csv_transfer("까치산", 5, 2)}
    assert "seconds" in transfer_seconds("이수", 4, 7)  # 별칭을 거치지 않은 이름도 같은 역이다


def test_transfer_seconds_errors_when_not_a_transfer_or_line_missing():
    assert "error" in transfer_seconds("강남", 2, 3)  # 강남은 3호선에 없다
    assert transfer_seconds("강남", 2, 3) == {"error": "강남은 3호선에 없다"}
    assert "error" in transfer_seconds("없는역", 2, 3)
    assert "error" in transfer_seconds("강남", 2, 2)  # 같은 호선은 갈아타는 것이 아니다
    assert "seconds" not in transfer_seconds("서울역", 1, 8)  # 두 호선 다 있는 역이 아니다


def test_transfer_seconds_equals_graph_edge_for_every_transfer():
    from subway_route_agent.tools import _graph

    g = _graph()
    for a, edges in g.items():
        for b, w in edges:
            if a[0] == b[0]:
                assert transfer_seconds(a[0], a[1], b[1]) == {"seconds": w}


def _q2_path():
    """q2 정답 경로에서 출발·갈아타는 역·도착만 남긴 입력."""
    from subway_route_agent.cli import QUESTIONS, truth_for
    from subway_route_agent.graph import build_graph

    q = next(q for q in json.loads(QUESTIONS.read_text(encoding="utf-8")) if q["id"] == "q2")
    g = build_graph(load_rows(), load_transfers())
    truth = truth_for(g, q)
    nodes = truth.nodes
    keep = [nodes[0]]
    for a, b in pairwise(nodes):
        if a[1] != b[1]:
            keep += [a, b]
    keep.append(nodes[-1])
    return truth, [{"station": s, "line": ln} for s, ln in keep]


def test_route_seconds_of_q2_truth_path_equals_truth_seconds_and_transfers():
    truth, path = _q2_path()
    assert len(path) < len(truth.nodes)  # 중간 역은 빠져 있다
    assert route_seconds(path) == {"seconds": truth.seconds, "transfers": truth.transfers}


def test_route_seconds_single_station_is_zero():
    assert route_seconds([{"station": "강남", "line": 2}]) == {"seconds": 0, "transfers": 0}


def test_route_seconds_unknown_station_returns_candidates():
    res = route_seconds([{"station": "강남", "line": 2}, {"station": "홍대", "line": 2}])
    assert res == {"error": "홍대은 데이터에 없다", "candidates": ["홍대입구"]}


def test_route_seconds_station_on_wrong_line_returns_lines():
    res = route_seconds([{"station": "강남", "line": 3}, {"station": "홍대입구", "line": 2}])
    assert res == {"error": "강남은 3호선에 없다", "lines": [2]}


def test_route_seconds_names_which_pair_cannot_be_joined():
    res = route_seconds([{"station": "서울역", "line": 1}, {"station": "잠실", "line": 8}])
    assert res == {"error": "1번째와 2번째를 이을 수 없다"}
    res = route_seconds([{"station": "서울역", "line": 1}, {"station": "시청", "line": 1},
                         {"station": "잠실", "line": 8}])
    assert res == {"error": "2번째와 3번째를 이을 수 없다"}
    assert "error" in route_seconds([])


def test_route_seconds_output_keys_are_fixed_and_never_contain_a_route():
    truth, path = _q2_path()
    outputs = [
        route_seconds(path),
        route_seconds([{"station": "홍대", "line": 2}]),
        route_seconds([{"station": "강남", "line": 3}]),
        route_seconds([{"station": "서울역", "line": 1}, {"station": "잠실", "line": 8}]),
        route_seconds([]),
    ]
    for out in outputs:
        assert set(out) <= COARSE_KEYS
    for word in ("path", "stations", "route", "nodes"):
        assert all(word not in out for out in outputs)


def test_route_seconds_tool_schema_path_has_same_shape_as_answer_schema():
    from subway_route_agent.answerers import SCHEMA

    (tool,) = COARSE_TOOLS
    assert tool["parameters"]["properties"]["path"] == SCHEMA["properties"]["path"]


def test_call_tool_rejects_name_from_the_other_tool_set():
    for name, args, tools in [
        ("route_seconds", json.dumps({"path": []}), FINE_TOOLS),
        ("find_station", json.dumps({"name": "강남"}), COARSE_TOOLS),
        ("transfer_seconds", json.dumps({"station": "이수", "from_line": 4, "to_line": 7}),
         COARSE_TOOLS),
    ]:
        assert json.loads(call_tool(name, args, tools)) == {"error": f"모르는 도구: {name}"}


def test_call_tool_runs_new_tools_by_name():
    out = call_tool("transfer_seconds",
                    json.dumps({"station": "이수", "from_line": 4, "to_line": 7}), FINE_TOOLS)
    assert json.loads(out) == {"seconds": _csv_transfer("총신대입구", 4, 7)}
    out = call_tool("route_seconds", json.dumps({"path": [
        {"station": "강남", "line": 2}, {"station": "홍대입구", "line": 2}]}), COARSE_TOOLS)
    assert json.loads(out) == {"seconds": 1740, "transfers": 0}


@pytest.mark.parametrize("path", [
    "강남",
    ["강남"],
    [{"station": "강남"}],
    [{"station": "강남", "line": "2"}],
    [{"station": 3, "line": 2}],
    [{"station": "강남", "line": True}],
    [{"station": "강남", "line": 2, "extra": 1}],
])
def test_call_tool_rejects_malformed_path(path):
    res = json.loads(call_tool("route_seconds", json.dumps({"path": path}), COARSE_TOOLS))
    assert list(res) == ["error"] and "path" in res["error"]
