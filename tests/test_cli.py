import json

from subway_route_agent.answerers import Answer
from subway_route_agent.cli import QUESTIONS, main
from subway_route_agent.data import Row
from subway_route_agent.grade import Grade
from subway_route_agent.graph import build_graph
from subway_route_agent.report import (
    COMPARE_COLUMNS,
    Result,
    format_path,
    format_seconds,
    render,
    render_compare,
)
from subway_route_agent.route import Route, shortest

NO_TRUTH = {"q6", "q7"}


def _cells(text):
    """리포트 표를 {질문: {열 이름: 값}}으로 읽는다. 열 위치에 기대지 않는다."""
    lines = [ln for ln in text.splitlines() if ln.startswith("| ")]
    cols = [c.strip() for c in lines[0].strip("| ").split(" | ")]
    return {row.strip("| ").split(" | ")[0]: dict(zip(cols, [c.strip() for c in
            row.strip("| ").split(" | ")], strict=True))
            for row in lines[2:]}


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
    assert "- 직접 계산으로 확인한 정답: 8/8" in text
    # 환승 시간 머리: 출처 한 줄, 환승역 수 한 줄. 실제 그래프는 35개 모두 데이터 값이다
    assert ("- 환승 시간: 서울교통공사 환승역 거리·소요시간 (data.go.kr 15044419, 2026-08-31 기준, "
            "최단 환승거리 ÷ 초당 1.2m)") in text
    assert ("- 데이터 환승 시간을 쓴 환승역 35개 · 180초가 남은 환승역 0개 "
            "(갈아타는 방향 78개 중 반대 방향 값 1개). 기다리는 시간은 0으로 본다") in text
    assert "고정한 stub" not in text  # 정답이 있는 8개 모두 직접 계산한 값이 있다
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


def test_arriving_exactly_at_the_deadline_keeps_truth(monkeypatch, tmp_path):
    # 건대입구→강남 최단은 900초. 8시 40분 + 15분 = 8시 55분에 딱 맞으면 정답이 있다.
    # 1분 모자라면 없다
    on_time = _question("a", "건대입구", "강남", depart="08:40", arrive_by="08:55")
    one_minute_short = _question("b", "건대입구", "강남", depart="08:40", arrive_by="08:54")
    code, out = _run_with(monkeypatch, tmp_path, [on_time, one_minute_short])
    rows = _rows(out.read_text(encoding="utf-8"))
    assert code == 0
    assert rows["a"][2] == "15분 0초" and rows["b"][2] == "없음"


def test_render_counts_hand_checked_answers_among_questions_with_truth():
    route = Route([("A", 1), ("C", 1)], 660, 0)
    g = Grade(False, False)
    checked = Result("q1", route, Answer(), g, 1.0, hand_checked=True)
    unchecked = Result("q2", route, Answer(), g, 1.0)
    no_truth = Result("q3", None, Answer(), g, 1.0, hand_checked=True)  # 정답 없음은 세지 않는다
    text = render("t", "d.csv", [checked, unchecked, no_truth])
    assert "- 직접 계산으로 확인한 정답: 1/2" in text
    lines = text.splitlines()
    assert lines.index("- 파싱 실패 0/3") + 1 == lines.index("- 직접 계산으로 확인한 정답: 1/2")


# ---- 여러 답하는 쪽 · 비교 리포트 (#188) ----

_Q1 = json.loads(QUESTIONS.read_text(encoding="utf-8"))[0]
# q1 직접 계산한 경로
GOOD_PATH = [(st, seg["line"]) for seg in _Q1["hand_path"] for st in seg["stations"]]


def _fake_answerers(monkeypatch, tmp_path):
    """API 없이 도는 가짜 답하는 쪽. good은 q1 직접 계산한 경로를 모든 질문에 말한다."""
    from subway_route_agent import cli
    from subway_route_agent.answerers import ANSWERERS

    monkeypatch.setattr(cli, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setitem(ANSWERERS, "good", lambda text: Answer(
        path=GOOD_PATH, seconds=1740, tool_calls=2, tokens=50, raw="g"))
    monkeypatch.setitem(ANSWERERS, "broken", lambda text: Answer(
        path=[("강남", 2), ("홍대입구", 5)], tool_calls=0, tokens=7, raw="b"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    return tmp_path / "reports"


def test_single_answerer_writes_no_compare_report(monkeypatch, tmp_path):
    reports = _fake_answerers(monkeypatch, tmp_path)
    assert main(["--answerer", "stub"]) == 0
    assert (reports / "stub.md").exists() and not (reports / "compare.md").exists()


def test_duplicate_answerer_name_runs_once_without_compare(monkeypatch, tmp_path):
    reports = _fake_answerers(monkeypatch, tmp_path)
    assert main(["--answerer", "stub", "stub"]) == 0
    assert not (reports / "compare.md").exists()


def test_two_answerers_write_each_report_and_compare_with_one_row_per_question(
    monkeypatch, tmp_path
):
    reports = _fake_answerers(monkeypatch, tmp_path)
    assert main(["--answerer", "stub", "good"]) == 0
    assert (reports / "stub.md").exists() and (reports / "good.md").exists()
    text = (reports / "compare.md").read_text(encoding="utf-8")
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    table = [line for line in text.splitlines() if line.startswith("| q")]
    assert len(table) == len(questions) == 10
    header = next(line for line in text.splitlines() if line.startswith("| 질문"))
    for name in ("stub", "good"):
        for col in ("맞음", "채운 역", "답 경로 소요 시간", "답이 말한 시간"):
            assert f"{name} {col}" in header
    assert header.startswith("| 질문 | 정답 시간 |")
    assert "지시문에만" not in text  # llm-tools를 돌리지 않았으면 지시문 차이 줄도 없다
    # 질문마다 두 답하는 쪽 값이 다 있다(열 수 = 2 + 4 × 2)
    assert all(len(row.strip("| ").split(" | ")) == 10 for row in table)


def test_compare_marks_broken_path_and_empty_answer_and_times(monkeypatch, tmp_path):
    reports = _fake_answerers(monkeypatch, tmp_path)
    assert main(["--answerer", "stub", "broken", "good"]) == 0
    text = (reports / "compare.md").read_text(encoding="utf-8")
    q1 = _cells(text)["q1"]
    assert [q1[f"stub {c}"] for c in COMPARE_COLUMNS] == ["X", "0", "답 없음", "없음"]
    assert [q1[f"broken {c}"] for c in COMPARE_COLUMNS] == ["X", "0", "끊김", "없음"]
    assert [q1[f"good {c}"] for c in COMPARE_COLUMNS] == ["O", "0", "29분 0초", "29분 0초"]
    assert "good" in text and "- good: 정답률 1/10" in text


def test_compare_shows_filled_path_time_not_broken_for_filled_correct_answer(
    monkeypatch, tmp_path
):
    from subway_route_agent.answerers import ANSWERERS

    reports = _fake_answerers(monkeypatch, tmp_path)
    monkeypatch.setitem(ANSWERERS, "gap", lambda text: Answer(
        path=[("강남", 2), ("홍대입구", 2)], seconds=1740, raw="g"))
    assert main(["--answerer", "stub", "gap"]) == 0
    q1 = _cells((reports / "compare.md").read_text(encoding="utf-8"))["q1"]
    assert [q1[f"gap {c}"] for c in COMPARE_COLUMNS] == ["O", "16", "29분 0초", "29분 0초"]


def test_compare_head_counts_calls_tokens_seconds_match_and_limit(monkeypatch, tmp_path):
    from subway_route_agent import cli
    from subway_route_agent.answerers import ANSWERERS, LIMIT_REACHED

    reports = _fake_answerers(monkeypatch, tmp_path)
    monkeypatch.setattr(cli, "QUESTIONS", _write_questions(tmp_path, [
        _question("a", "강남", "홍대입구", max_transfers=1),
        _question("b", "강남", "홍대입구", max_transfers=1)]))  # q1과 같은 조건
    answers = iter([Answer(path=GOOD_PATH, seconds=1740, tool_calls=3, tokens=10),
                    Answer(parse_error=LIMIT_REACHED, tool_calls=25, tokens=90)])
    monkeypatch.setitem(ANSWERERS, "capped", lambda text: next(answers))
    assert main(["--answerer", "stub", "capped"]) == 0
    text = (reports / "compare.md").read_text(encoding="utf-8")
    line = next(ln for ln in text.splitlines() if ln.startswith("- capped:"))
    assert "정답률 1/2" in line and "파싱 실패 1/2" in line
    assert "도구 호출 28" in line and "토큰 100" in line
    assert "답이 말한 시간이 정답과 같은 질문 1/2" in line
    assert "도구 호출 상한에 닿은 질문 1" in line


def _write_questions(tmp_path, questions):
    qfile = tmp_path / "questions.json"
    qfile.write_text(json.dumps(questions, ensure_ascii=False), encoding="utf-8")
    return qfile


def test_out_with_two_answerers_is_the_compare_path_and_raw_is_split(monkeypatch, tmp_path):
    reports = _fake_answerers(monkeypatch, tmp_path)
    out, raw = tmp_path / "x" / "cmp.md", tmp_path / "r" / "raw.json"
    assert main(["--answerer", "stub", "good", "--out", str(out), "--raw", str(raw)]) == 0
    assert out.exists() and (reports / "stub.md").exists() and (reports / "good.md").exists()
    assert not (reports / "compare.md").exists()
    assert json.loads((tmp_path / "r" / "raw-good.json").read_text("utf-8"))["q1"]["raw"] == "g"
    assert (tmp_path / "r" / "raw-stub.json").exists() and not raw.exists()


def test_raw_with_one_answerer_keeps_the_given_path(monkeypatch, tmp_path):
    _fake_answerers(monkeypatch, tmp_path)
    raw = tmp_path / "raw.json"
    assert main(["--answerer", "good", "--raw", str(raw)]) == 0
    assert raw.exists()


def test_llm_tools_without_key_exits_2_before_any_report(monkeypatch, tmp_path, capsys):
    reports = _fake_answerers(monkeypatch, tmp_path)
    assert main(["--answerer", "stub", "llm-tools"]) == 2
    assert "OPENAI_API_KEY가 없다" in capsys.readouterr().err
    assert not reports.exists()


def test_llm_tools_report_names_model_and_tools(monkeypatch, tmp_path):
    from subway_route_agent import answerers
    from subway_route_agent.answerers import ANSWERERS

    reports = _fake_answerers(monkeypatch, tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setitem(ANSWERERS, "llm-tools", lambda text: Answer(tool_calls=4))
    assert main(["--answerer", "llm-tools"]) == 0
    text = (reports / "llm-tools.md").read_text(encoding="utf-8")
    assert f"- 답하는 쪽: llm-tools (모델 {answerers.MODEL})" in text
    assert "- 도구: find_station, line_stations, travel_seconds (호출 상한 25)" in text
    assert _cells(text)["q1"]["도구 호출"] == "4"


def test_api_error_in_second_answerer_keeps_first_raw_and_writes_no_report(
    monkeypatch, tmp_path
):
    import openai

    from subway_route_agent.answerers import ANSWERERS

    reports = _fake_answerers(monkeypatch, tmp_path)

    def fail(text):
        raise openai.APIError("연결 실패", request=None, body=None)

    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setitem(ANSWERERS, "llm-tools", fail)
    raw = tmp_path / "raw.json"
    assert main(["--answerer", "good", "llm-tools", "--raw", str(raw)]) == 1
    assert (tmp_path / "raw-good.json").exists()
    assert not reports.exists()


def test_render_compare_unit_head_and_rows():
    g = build_graph([Row(1, "A", 0), Row(1, "B", 60), Row(1, "C", 600)])
    truth = Route([("A", 1), ("C", 1)], 660, 0)
    path = [("A", 1), ("B", 1), ("C", 1)]
    hit = Result("q1", truth, Answer(path=path, seconds=660, tool_calls=1, tokens=5),
                 Grade(True, True), 2000.0)
    miss = Result("q1", truth, Answer(), Grade(False, False), 500.0)
    text = render_compare("d.csv", {"x": [hit], "y": [miss]}, {"x": "m1", "y": None}, g)
    assert "- x (모델 m1): 정답률 1/1" in text and "- y: 정답률 0/1" in text
    assert "응답 시간 합 2.0초" in text and "응답 시간 합 0.5초" in text
    row = next(line for line in text.splitlines() if line.startswith("| q1"))
    assert [c.strip(" |") for c in row.split(" | ")][1:] == [
        "11분 0초", "O", "0", "11분 0초", "11분 0초", "X", "0", "답 없음", "없음"]


def test_render_heads_name_stations_that_keep_180_seconds():
    from subway_route_agent.graph import count_transfers

    g = build_graph([Row(1, "A", 0), Row(1, "B", 60), Row(2, "B", 0), Row(2, "C", 60)],
                    transfers={})
    counts = count_transfers(g, {})
    r = Result("q1", None, Answer(), Grade(False, False), 0.0)
    line = ("- 데이터 환승 시간을 쓴 환승역 0개 · 180초가 남은 환승역 1개(B) "
            "(갈아타는 방향 2개 중 반대 방향 값 0개). 기다리는 시간은 0으로 본다")
    assert line in render("t", "d.csv", [r], counts=counts)
    assert line in render_compare("d.csv", {"x": [r]}, {}, g, counts=counts)


def test_render_compare_shows_instruction_difference_only_with_llm_tools():
    g = build_graph([Row(1, "A", 0), Row(1, "B", 60)])
    r = Result("q1", None, Answer(), Grade(False, False), 0.0)
    with_tools = render_compare("d.csv", {"stub": [r], "llm-tools": [r]}, {}, g)
    assert ("- LLM + 도구 지시문에만 도구 사용 안내와 「환승 시간은 역과 호선마다 다르다」 "
            "문장이 있다") in with_tools
    without = render_compare("d.csv", {"stub": [r], "llm": [r]}, {}, g)
    assert "지시문에만" not in without


def test_render_compare_does_not_count_empty_answer_as_matching_no_truth_question():
    # 정답 없음 질문(truth=None)에서 말한 시간도 None이어도 「정답과 같은 질문」으로 세지 않는다
    g = build_graph([Row(1, "A", 0), Row(1, "B", 60)])
    r = Result("q6", None, Answer(), Grade(False, False), 0.0)
    text = render_compare("d.csv", {"stub": [r], "llm": [r]}, {}, g)
    assert "답이 말한 시간이 정답과 같은 질문 0/1" in text


def test_report_has_filled_column_right_after_correct():
    route = Route([("A", 1), ("C", 1)], 660, 0)
    r = Result("q1", route, Answer(path=route.nodes), Grade(True, True, filled=3), 1.0)
    text = render("t", "d.csv", [r])
    header = next(ln for ln in text.splitlines() if ln.startswith("| 질문"))
    cols = [c.strip() for c in header.strip("| ").split(" | ")]
    assert cols[cols.index("맞음") + 1] == "채운 역"
    assert _cells(text)["q1"]["채운 역"] == "3"


def test_compare_head_counts_correct_answers_without_filling():
    g = build_graph([Row(1, "A", 0), Row(1, "B", 60), Row(1, "C", 600)])
    truth = Route([("A", 1), ("C", 1)], 660, 0)
    full = Result("q1", truth, Answer(), Grade(True, True, filled=0), 1.0)
    filled = Result("q2", truth, Answer(), Grade(True, True, filled=2), 1.0)
    wrong = Result("q3", truth, Answer(), Grade(True, False, filled=0), 1.0)
    text = render_compare("d.csv", {"x": [full, filled, wrong]}, {}, g)
    line = next(ln for ln in text.splitlines() if ln.startswith("- x:"))
    assert "정답률 2/3" in line and "채우지 않고도 맞은 질문 1/3" in line
    assert _cells(text)["q2"]["x 채운 역"] == "2"


def test_raw_file_has_tool_log(monkeypatch, tmp_path):
    from subway_route_agent.answerers import ANSWERERS

    reports = _fake_answerers(monkeypatch, tmp_path)
    log = [{"name": "find_station", "arguments": "{}", "output": "{}"}]
    monkeypatch.setitem(ANSWERERS, "logged", lambda text: Answer(raw="x", tool_log=log))
    raw = tmp_path / "raw.json"
    assert main(["--answerer", "logged", "--raw", str(raw)]) == 0
    assert json.loads(raw.read_text("utf-8"))["q1"]["tool_log"] == log
    assert reports.exists()
