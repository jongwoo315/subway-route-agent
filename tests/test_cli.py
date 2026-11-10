import json

from subway_route_agent.answerers import Answer
from subway_route_agent.cli import QUESTIONS, main
from subway_route_agent.data import Row
from subway_route_agent.grade import Grade
from subway_route_agent.graph import build_graph
from subway_route_agent.report import Result, format_path, format_seconds, render
from subway_route_agent.route import Route, shortest

NO_TRUTH = {"q6", "q7"}


def test_main_runs_end_to_end(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)  # stub은 키 없이 끝까지 돈다
    out = tmp_path / "stub.md"
    assert main(["--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert capsys.readouterr().out.strip() == text.strip()
    rows = {line.split(" | ")[0].lstrip("| "): line.split(" | ") for line in text.splitlines()}
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    for q in questions:
        assert q["id"] in rows
        # 정답 없음 질문(q6 시한을 못 맞춘다, q7 환승 0회로 갈 길이 없다)만 정답이 없음이다
        none = q["id"] in NO_TRUTH
        assert (rows[q["id"]][1] == "없음") == none and (rows[q["id"]][2] == "없음") == none
    assert f"정답률 0/{len(questions)} (0%)" in text
    assert "- 손 계산으로 확인한 정답: 8/8" in text  # 정답이 있는 8개 모두 손 계산 값이 있다
    assert rows["q1"][1] == "강남(2) → 홍대입구(2)" and rows["q1"][2] == "29분 0초"


def test_render_counts_correct_and_answered_rows():
    # stub만 돌리면 정답률이 늘 0이라 hits 계산이 고장 나도 안 걸린다
    route = Route([("A", 1), ("C", 1)], 660, 0)
    hit = Result("q1", route, Answer(path=route.nodes, seconds=660), Grade(True, True), 1.0)
    miss = Result("q2", route, Answer(), Grade(False, False), 1.0)
    text = render("t", "d.csv", [hit, miss])
    assert "정답률 1/2 (50%)" in text
    rows = {line.split(" | ")[0].lstrip("| "): line.split(" | ") for line in text.splitlines()}
    assert rows["q1"][3:5] == ["O", "O"] and rows["q2"][3:5] == ["X", "X"]


def test_unknown_answerer_is_rejected(tmp_path):
    import pytest

    with pytest.raises(SystemExit):
        main(["--answerer", "gpt", "--out", str(tmp_path / "x.md")])


def test_format_seconds():
    assert format_seconds(1740) == "29분 0초"
    assert format_seconds(65) == "1분 5초"
    assert format_seconds(None) == "없음"


def test_format_path_shows_endpoints_and_transfer_stations_only():
    rows = [
        Row(1, "A", 0), Row(1, "B", 60), Row(1, "C", 600),
        Row(2, "B", 0), Row(2, "C", 60),
    ]
    g = build_graph(rows)
    assert format_path(shortest(g, "A", "C", max_transfers=0)) == "A(1) → C(1)"
    assert format_path(shortest(g, "A", "C")) == "A(1) → B(1→2) → C(2)"
    assert format_path(None) == "없음"


def test_default_report_path_follows_answerer(tmp_path, monkeypatch):
    from subway_route_agent import cli

    monkeypatch.setattr(cli, "REPORT_DIR", tmp_path)
    assert main([]) == 0
    assert (tmp_path / "stub.md").exists()


def test_render_counts_parse_failures_and_shows_tokens():
    route = Route([("A", 1), ("C", 1)], 660, 0)
    ok = Result("q1", route, Answer(path=route.nodes, tokens=120), Grade(True, True), 1.0)
    bad = Result("q2", route, Answer(parse_error="JSON 아님", tokens=80), Grade(False, False), 1.0)
    text = render("llm", "d.csv", [ok, bad], model="gpt-x")
    assert "- 파싱 실패 1/2" in text
    assert "- 답하는 쪽: llm (모델 gpt-x)" in text
    lines = text.splitlines()
    header = next(line for line in lines if line.startswith("| 질문"))
    assert header.split(" | ")[-1].strip(" |") == "토큰"
    assert lines[0] == "# 리포트"
    rows = {line.split(" | ")[0].lstrip("| "): line.split(" | ") for line in lines}
    assert rows["q1"][-1].strip(" |") == "120" and rows["q2"][-1].strip(" |") == "80"


def _question(qid, origin, dest, **kw):
    q = {"id": qid, "text": f"{origin}에서 {dest}까지", "origin": origin, "dest": dest,
         "max_transfers": None, "depart": None, "arrive_by": None}
    return {**q, **kw}


def _run_with(monkeypatch, tmp_path, questions):
    from subway_route_agent import cli

    qfile = tmp_path / "questions.json"
    qfile.write_text(json.dumps(questions, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(cli, "QUESTIONS", qfile)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    out = tmp_path / "stub.md"
    return main(["--out", str(out)]), out


def _rows(text):
    return {line.split(" | ")[0].lstrip("| "): line.split(" | ") for line in text.splitlines()}


def test_station_missing_from_graph_stops_before_running(monkeypatch, tmp_path, capsys):
    qs = [_question("q1", "강남", "홍대입구"), _question("q5", "강남", "무슨역")]
    code, out = _run_with(monkeypatch, tmp_path, qs)
    assert code == 2 and not out.exists()
    assert "질문 q5: 그래프에 없는 역 — 무슨역" in capsys.readouterr().err


def test_every_missing_station_is_reported(monkeypatch, tmp_path, capsys):
    qs = [_question("q1", "가나다", "라마바")]
    code, _ = _run_with(monkeypatch, tmp_path, qs)
    err = capsys.readouterr().err
    assert code == 2 and "가나다" in err and "라마바" in err


def test_alias_station_name_passes_the_check_and_is_found(monkeypatch, tmp_path):
    # 총신대입구는 그래프에서 이수다. 별칭을 바꾼 뒤 검사하고 정답도 같은 이름으로 찾는다
    code, out = _run_with(monkeypatch, tmp_path, [_question("q1", "총신대입구", "사당")])
    assert code == 0
    assert _rows(out.read_text(encoding="utf-8"))["q1"][1] != "없음"


def test_deadline_that_even_shortest_route_misses_has_no_truth(monkeypatch, tmp_path):
    # 건대입구→강남 최단은 15분인데 시한까지 10분이다
    missed = _question("q6", "건대입구", "강남", depart="08:40", arrive_by="08:50")
    kept = _question("q7", "건대입구", "강남", depart="08:40", arrive_by="09:00")
    code, out = _run_with(monkeypatch, tmp_path, [missed, kept])
    rows = _rows(out.read_text(encoding="utf-8"))
    assert code == 0
    assert rows["q6"][1] == "없음" and rows["q6"][2] == "없음"
    assert rows["q7"][1] != "없음" and rows["q7"][2] == "15분 0초"


def test_render_counts_hand_checked_answers_among_questions_with_truth():
    route = Route([("A", 1), ("C", 1)], 660, 0)
    g = Grade(False, False)
    checked = Result("q1", route, Answer(), g, 1.0, hand_checked=True)
    unchecked = Result("q2", route, Answer(), g, 1.0)
    no_truth = Result("q3", None, Answer(), g, 1.0, hand_checked=True)  # 정답 없음은 세지 않는다
    text = render("t", "d.csv", [checked, unchecked, no_truth])
    assert "- 손 계산으로 확인한 정답: 1/2" in text
    lines = text.splitlines()
    assert lines.index("- 파싱 실패 0/3") + 1 == lines.index("- 손 계산으로 확인한 정답: 1/2")
