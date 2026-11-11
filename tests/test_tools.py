import json

import pytest

from subway_route_agent.data import ROOT, load_rows
from subway_route_agent.tools import TOOLS, call_tool, find_station, line_stations, travel_seconds

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
    assert [t["name"] for t in TOOLS] == ["find_station", "line_stations", "travel_seconds"]
    for t in TOOLS:
        assert t["type"] == "function" and t["strict"] is True
        params = t["parameters"]
        assert params["additionalProperties"] is False
        assert set(params["required"]) == set(params["properties"])
        for word in ("최단", "추천", "가장 빠"):
            assert word not in t["description"]


def test_call_tool_runs_by_name_and_returns_json_string():
    out = call_tool("find_station", json.dumps({"name": "강남"}))
    assert json.loads(out) == {"found": True, "station": "강남", "lines": [2]}
    out = call_tool(
        "travel_seconds",
        json.dumps({"line": 2, "from_station": "강남", "to_station": "홍대입구"}),
    )
    assert json.loads(out) == {"seconds": 1740}
    assert json.loads(call_tool("line_stations", json.dumps({"line": 7})))["line"] == 7


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
    assert "error" in json.loads(call_tool(name, args))


def test_travel_seconds_does_not_use_transfer_edges():
    # 두 역이 같은 호선에 있고 다른 호선으로 갈아타면 더 빨라지는 쌍이다.
    # 환승 간선을 쓰면 이 값보다 작아진다(2호선 시청→교대 1200, 강남→시청 1470, 3호선 지축→오금 2900)
    assert travel_seconds(2, "시청", "교대") == {"seconds": 1830}
    assert travel_seconds(2, "강남", "시청") == {"seconds": 1740}
    assert travel_seconds(3, "지축", "오금") == {"seconds": 3090}
