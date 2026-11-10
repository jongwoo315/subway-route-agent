import json
from itertools import pairwise

import pytest

from subway_route_agent.cli import truth_for
from subway_route_agent.data import ROOT, Row, load_rows
from subway_route_agent.graph import TRANSFER_SECONDS, build_graph
from subway_route_agent.route import shortest

ROWS = load_rows()
REAL = build_graph(ROWS)
QUESTIONS = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
# 노선도 지식: CSV는 지선을 표시 없이 앞 구간 끝 행 바로 뒤에 이어 붙였다.
# 지선 첫 역의 실제 앞 역은 분기역이다. (호선, 지선 첫 역) → 분기역.
# graph.BRANCH_HEADS를 쓰지 않는다. 손 계산은 그래프 코드와 따로다
JUNCTIONS = {(2, "용답"): "성수", (2, "도림천"): "신도림", (5, "둔촌동"): "강동"}


def _hop_seconds(line: int, a: str, b: str) -> int:
    """CSV 행만 보고 같은 호선의 이웃한 두 역 사이 소요시간(초)을 구한다. 없으면 실패한다."""
    heads = {h for (ln, h) in JUNCTIONS if ln == line}
    eungam = [i for i, r in enumerate(ROWS) if r.line == 6 and r.station == "응암"]
    for i in range(1, len(ROWS)):
        prev, cur = ROWS[i - 1], ROWS[i]
        if cur.line != line or prev.line != line or cur.seconds == 0 or cur.station in heads:
            continue
        if (prev.station, cur.station) == (a, b):
            return cur.seconds
        # 거꾸로 달리는 것은 응암순환(첫 응암 행 뒤 ~ 둘째 응암 행)만 막혀 있다
        one_way = line == 6 and eungam[0] < i <= eungam[1]
        if (prev.station, cur.station) == (b, a) and not one_way:
            return cur.seconds
    for (ln, head), junction in JUNCTIONS.items():
        if ln == line and {a, b} == {head, junction}:
            return next(r.seconds for r in ROWS if r.line == ln and r.station == head)
    raise AssertionError(f"{line}호선에 {a}-{b} 이웃이 CSV에 없다")


def _csv_seconds(hand_path: list[dict]) -> int:
    """`build_graph`·`shortest` 없이 CSV 행만으로 hand_path의 소요 시간을 더한다."""
    total = 0
    for k, seg in enumerate(hand_path):
        if k and hand_path[k - 1]["stations"][-1] != seg["stations"][0]:
            raise AssertionError(f"환승역이 이어지지 않는다: {seg['stations'][0]}")
        if k:
            total += TRANSFER_SECONDS
        total += sum(_hop_seconds(seg["line"], a, b) for a, b in pairwise(seg["stations"]))
    return total


HAND_CHECKED = [q for q in QUESTIONS if "hand_path" in q]


@pytest.mark.parametrize("q", HAND_CHECKED, ids=lambda q: q["id"])
def test_hand_seconds_matches_csv_sum_and_dijkstra(q):
    r = shortest(REAL, q["origin"], q["dest"], q["max_transfers"])
    assert _csv_seconds(q["hand_path"]) == q["hand_seconds"] == r.seconds
    assert q["hand_path"][0]["stations"][0] == q["origin"]
    assert q["hand_path"][-1]["stations"][-1] == q["dest"]
    assert len(q["hand_path"]) - 1 <= (q["max_transfers"] if q["max_transfers"] is not None else 99)


def one(line: int, *stations: str) -> int:
    return _csv_seconds([{"line": line, "stations": list(stations)}])


def test_hand_sum_follows_loop_branch_and_one_way_rules():
    assert one(2, "충정로", "시청", "을지로입구") == 90 + 90  # 시청이 두 번 나오는 2호선
    assert one(5, "강동", "둔촌동") == 110  # CSV에서 떨어져 있는 지선 첫 역
    assert one(6, "구산", "응암", "새절") == 120 + 80  # 응암순환 정방향, 순환 밖으로 나가기
    assert one(2, "도림천", "신도림") == 90
    with pytest.raises(AssertionError):
        one(6, "응암", "구산")  # 응암순환은 거꾸로 못 간다
    with pytest.raises(AssertionError):
        one(2, "시청", "용답")  # CSV에서 바로 아래 행이지만 이웃이 아니다
    with pytest.raises(AssertionError):
        _csv_seconds([{"line": 1, "stations": ["서울역", "종각"]},
                      {"line": 2, "stations": ["시청", "을지로입구"]}])


def test_transfer_limit_forces_slower_route():
    rows = [
        Row(1, "A", 0), Row(1, "B", 60), Row(1, "C", 600),
        Row(2, "B", 0), Row(2, "C", 60),
    ]
    g = build_graph(rows)
    fast = shortest(g, "A", "C")
    assert fast.transfers == 1 and fast.seconds == 60 + 180 + 60
    direct = shortest(g, "A", "C", max_transfers=0)
    assert direct.transfers == 0 and direct.seconds == 660


def test_unknown_station_returns_none():
    assert shortest(REAL, "없는역", "강남") is None


def test_q3_uses_macheon_branch():
    r = shortest(REAL, "방화", "마천", max_transfers=0)
    assert ("둔촌동", 5) in r.nodes and ("상일동", 5) not in r.nodes


def test_q2_needs_transfer():
    r = shortest(REAL, "서울역", "잠실")
    assert r.transfers >= 1


def test_circular_lines_close_on_repeated_station():
    # 2호선은 시청이 두 번, 6호선 응암순환은 응암이 두 번 나와서 고리가 닫힌다
    assert shortest(REAL, "충정로", "시청", max_transfers=0).seconds == 90
    assert shortest(REAL, "구산", "새절", max_transfers=0).nodes == [
        ("구산", 6), ("응암", 6), ("새절", 6)
    ]


def test_eungam_loop_is_one_way():
    # 응암순환은 응암→역촌→불광→독바위→연신내→구산→응암 한 방향만 달린다
    # 역촌→구산: 응암을 거치는 역방향(220초)이 아니라 불광·독바위·연신내를 도는 370초
    assert shortest(REAL, "역촌", "구산", max_transfers=0).seconds == 370
    # 연신내→역촌: 구산·응암을 거쳐 300초
    assert shortest(REAL, "연신내", "역촌", max_transfers=0).seconds == 300


def test_unknown_destination_returns_none_without_cap():
    assert shortest(REAL, "강남", "없는역") is None


def _question(qid: str) -> dict:
    return next(q for q in QUESTIONS if q["id"] == qid)


def test_q6_has_no_truth_because_even_fastest_route_misses_deadline():
    q = _question("q6")
    fastest = shortest(REAL, q["origin"], q["dest"], q["max_transfers"])
    assert fastest is not None and fastest.seconds == q["hand_seconds"]
    late = (8 * 60 + 40) * 60 + fastest.seconds - (8 * 60 + 50) * 60
    assert late == 300  # 5분 늦다
    assert truth_for(REAL, q) is None


def test_q7_has_no_truth_because_no_single_line_connects_the_stations():
    q = _question("q7")
    assert shortest(REAL, q["origin"], q["dest"], 0) is None
    # 환승 상한 때문이지 역이 없어서가 아니다
    assert shortest(REAL, q["origin"], q["dest"]) is not None
    assert truth_for(REAL, q) is None


def test_every_question_has_hand_note_and_hand_path_pairs_with_seconds():
    for q in QUESTIONS:
        assert q["hand_note"], q["id"]
        assert ("hand_path" in q) == ("hand_seconds" in q), q["id"]
        if "hand_path" not in q:
            assert truth_for(REAL, q) is None, q["id"]  # 손 계산이 없는 질문은 정답 없음이다


def test_questions_cover_the_cases_the_ticket_names():
    by_id = {q["id"]: q for q in QUESTIONS}
    assert by_id["q4"]["depart"] and not by_id["q4"]["arrive_by"]
    assert by_id["q5"]["arrive_by"] and not by_id["q5"]["depart"]
    assert by_id["q7"]["max_transfers"] == 0 and by_id["q9"]["max_transfers"] == 1
    assert len(by_id["q8"]["hand_path"]) - 1 >= 2  # 환승 2회 이상
    assert truth_for(REAL, by_id["q8"]).transfers >= 2
