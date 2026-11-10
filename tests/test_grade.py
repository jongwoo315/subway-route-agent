from subway_route_agent.answerers import Answer
from subway_route_agent.data import Row
from subway_route_agent.grade import grade
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
