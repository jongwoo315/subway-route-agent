import json

import pytest

from subway_route_agent.answerers import Answer
from subway_route_agent.cli import QUESTIONS, truth_for
from subway_route_agent.data import Row, load_rows
from subway_route_agent.grade import fill_path, grade, path_seconds
from subway_route_agent.graph import build_graph
from subway_route_agent.route import shortest

ROWS = [
    Row(1, "A", 0), Row(1, "B", 60), Row(1, "C", 600),
    Row(2, "B", 0), Row(2, "C", 60),
]
G = build_graph(ROWS)


def _q(**kw):
    q = {"origin": "A", "dest": "C", "max_transfers": None, "depart": None, "arrive_by": None}
    q.update(kw)
    return q


def test_correct_answer():
    q = _q()
    truth = shortest(G, "A", "C")
    ans = Answer(path=truth.nodes, seconds=truth.seconds)
    g = grade(G, q, ans, truth)
    assert g.answered and g.correct and g.violations == []


def test_empty_answer_is_unanswered_and_not_correct():
    q = _q()
    g = grade(G, q, Answer(), shortest(G, "A", "C"))
    assert not g.answered and not g.correct
    assert g.invented_stations == 0 and g.invented_time == 0 and g.violations == []


def test_invented_station_and_broken_path():
    q = _q()
    ans = Answer(path=[("A", 1), ("Z", 1), ("C", 1)])
    g = grade(G, q, ans, shortest(G, "A", "C"))
    assert g.invented_stations == 1
    assert "경로 끊김" in g.violations
    assert not g.correct


def test_invented_time():
    q = _q(max_transfers=0)
    truth = shortest(G, "A", "C", max_transfers=0)
    ans = Answer(path=truth.nodes, seconds=truth.seconds + 61)
    g = grade(G, q, ans, truth)
    assert g.invented_time == 1
    assert g.correct  # 경로는 맞다. 말한 시간만 틀렸다
    ok = grade(G, q, Answer(path=truth.nodes, seconds=truth.seconds + 60), truth)
    assert ok.invented_time == 0


def test_transfer_limit_violation():
    q = _q(max_transfers=0)
    ans = Answer(path=[("A", 1), ("B", 1), ("B", 2), ("C", 2)])
    g = grade(G, q, ans, shortest(G, "A", "C", max_transfers=0))
    assert "환승 초과" in g.violations
    assert not g.correct


def test_deadline_violation():
    q = _q(depart="08:20", arrive_by="08:30")  # 10분 = 600초
    truth = shortest(G, "A", "C", max_transfers=0)  # 660초
    ans = Answer(path=truth.nodes, seconds=truth.seconds)
    g = grade(G, q, ans, truth)
    assert "시한 초과" in g.violations
    assert not g.correct


def test_wrong_endpoints():
    q = _q()
    ans = Answer(path=[("B", 1), ("C", 1)])
    g = grade(G, q, ans, shortest(G, "A", "C"))
    assert "출발역 다름" in g.violations and "도착역 다름" not in g.violations
    ans = Answer(path=[("A", 1), ("B", 1)])
    g = grade(G, q, ans, shortest(G, "A", "C"))
    assert "도착역 다름" in g.violations


def test_deadline_needs_both_depart_and_arrive_by():
    truth = shortest(G, "A", "C", max_transfers=0)  # 660초
    ans = Answer(path=truth.nodes, seconds=truth.seconds)
    # 출발 시각만, 도착 시한만 있으면 시한을 잴 수 없다. 지금 동작을 고정한다
    for kw in ({"depart": "23:59"}, {"arrive_by": "00:01"}):
        g = grade(G, _q(max_transfers=0, **kw), ans, truth)
        assert "시한 초과" not in g.violations and g.correct


def test_answer_to_question_without_truth_is_answered_but_never_correct():
    # 정답 없음 질문(truth=None)에 경로를 말하면 답은 했지만 맞을 수 없다. 죽지 않아야 한다
    path = shortest(G, "A", "C", max_transfers=0).nodes
    g = grade(G, _q(max_transfers=0), Answer(path=path, seconds=660), None)
    assert g.answered and not g.correct and g.violations == []
    g = grade(G, _q(max_transfers=0), Answer(), None)
    assert not g.answered and not g.correct


# --- #193 빠진 중간 역 채우기 ---------------------------------------------------


REAL = build_graph(load_rows())
QS = {q["id"]: q for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))}


def _hand_nodes(q):
    return [(s, seg["line"]) for seg in q["hand_path"] for s in seg["stations"]]


HAND_CASES = [
    # (이름, 질문, 답 경로, 맞음, 채운 역, 실제 소요 시간, 조건 어김, 지어낸 역)
    ("A", "q2", [("서울역", 4), ("동대문역사문화공원", 4), ("동대문역사문화공원", 2), ("잠실", 2)],
     True, 13, 1440, [], 0),
    ("B", "q2", [("서울역", 4), ("동대문역사문화공원", 2), ("잠실", 2)],
     True, 14, 1440, [], 0),
    ("C", "q2", [("서울역", 1), ("시청", 1), ("시청", 2), ("잠실", 2)],
     False, 14, 1530, [], 0),
    ("D", "q2", [("서울역", 1), ("잠실", 2)], False, 0, None, ["경로 끊김"], 0),
    ("F", "q1", [("강남", 2), ("홍대입구", 2)], True, 16, 1740, [], 0),
    ("G", "q2", [("서울역", 4), ("없는역", 4), ("잠실", 2)], False, 0, None, ["경로 끊김"], 1),
]


@pytest.mark.parametrize("name,qid,path,correct,filled,actual,violations,invented", HAND_CASES)
def test_hand_cases(name, qid, path, correct, filled, actual, violations, invented):
    q = QS[qid]
    g = grade(REAL, q, Answer(path=path), truth_for(REAL, q))
    assert g.correct is correct
    assert g.filled == filled
    assert g.violations == violations
    assert g.invented_stations == invented
    fill = fill_path(REAL, path)
    assert (path_seconds(REAL, fill[0]) if fill else None) == actual


def test_hand_case_E_full_path_is_unchanged():
    for qid in ("q1", "q2", "q3"):
        q = QS[qid]
        g = grade(REAL, q, Answer(path=_hand_nodes(q)), truth_for(REAL, q))
        assert g.correct and g.filled == 0, qid


def test_fill_path_rule2_counts_transfer_node():
    filled, n = fill_path(REAL, [("서울역", 4), ("동대문역사문화공원", 2)])
    assert n == 4  # 회현 명동 충무로 + (동대문역사문화공원, 4)
    assert filled[-2:] == [("동대문역사문화공원", 4), ("동대문역사문화공원", 2)]


def test_fill_path_unfillable_returns_none():
    assert fill_path(REAL, [("서울역", 1), ("잠실", 2)]) is None
    assert fill_path(REAL, [("서울역", 4), ("없는역", 4)]) is None
    assert fill_path(REAL, [("서울역", 4), ("서울역", 4)]) is None  # 같은 노드 반복


def test_fill_path_small_graph_fills_same_line_stop():
    # 작은 그래프: 1호선 A-B-C에서 A→C는 B를 채운다. 이전에는 경로 끊김이었다
    q = _q(max_transfers=0)
    truth = shortest(G, "A", "C", max_transfers=0)
    g = grade(G, q, Answer(path=[("A", 1), ("C", 1)]), truth)
    assert g.filled == 1 and g.violations == [] and g.correct
