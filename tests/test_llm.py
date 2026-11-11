import json
from types import SimpleNamespace

import pytest

from subway_route_agent import answerers
from subway_route_agent.answerers import ANSWERERS, Answer, make_llm
from subway_route_agent.cli import main
from subway_route_agent.data import ROOT


def use_recorded_questions(monkeypatch, tmp_path, ids):
    """녹화 fixture에 있는 질문만 든 질문 파일로 바꾼다. 재생은 녹화한 질문 순서대로만 답한다."""
    from subway_route_agent import cli

    allq = json.loads((ROOT / "data" / "questions.json").read_text("utf-8"))
    chosen = [q for q in allq if q["id"] in ids]
    qfile = tmp_path / "recorded_questions.json"
    qfile.write_text(json.dumps(chosen, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(cli, "QUESTIONS", qfile)
    return chosen


class FakeClient:
    """output_text와 usage만 가진 응답을 돌려주는 가짜 client. API를 부르지 않는다."""

    def __init__(self, output_text: str, tokens=(10, 5)):
        self.calls: list[dict] = []
        self._resp = SimpleNamespace(
            output_text=output_text,
            usage=SimpleNamespace(input_tokens=tokens[0], output_tokens=tokens[1]),
        )
        self.responses = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return self._resp


GOOD = json.dumps({
    "path": [{"station": "강남", "line": 2}, {"station": "홍대입구", "line": 2}],
    "seconds": 1740,
})


def test_good_json_fills_path_seconds_tokens():
    ans = make_llm(FakeClient(GOOD, tokens=(100, 20)))("질문")
    assert ans.path == [("강남", 2), ("홍대입구", 2)]
    assert ans.seconds == 1740
    assert ans.tokens == 120
    assert ans.raw == GOOD
    assert ans.parse_error is None


@pytest.mark.parametrize(
    "bad",
    [
        "이건 JSON이 아니다",
        json.dumps({"seconds": 10}),
        json.dumps({"path": [{"station": "강남", "line": "2"}], "seconds": None}),
        json.dumps({"path": [{"station": "강남"}], "seconds": None}),
        json.dumps({"path": "강남", "seconds": None}),
        json.dumps([1, 2]),
        json.dumps({"path": [], "seconds": 300}),
    ],
)
def test_unreadable_answer_sets_parse_error_without_raising(bad):
    ans = make_llm(FakeClient(bad, tokens=(7, 3)))("질문")
    assert ans.parse_error
    assert ans.path == [] and ans.seconds is None
    assert ans.raw == bad and ans.tokens == 10


def test_missing_usage_and_unfinished_status_do_not_crash():
    client = FakeClient(GOOD)
    client._resp.usage = None
    ans = make_llm(client)("질문")
    assert ans.tokens == 0 and ans.parse_error is None

    client = FakeClient("", tokens=(4, 1))
    client._resp.status = "incomplete"
    ans = make_llm(client)("질문")
    assert "incomplete" in ans.parse_error and ans.path == [] and ans.tokens == 5


def test_request_uses_instructions_and_json_schema_without_hints():
    client = FakeClient(GOOD)
    make_llm(client)("서울역에서 잠실까지")
    (call,) = client.calls
    assert call["input"] == "서울역에서 잠실까지"
    assert call["instructions"] == answerers.SYSTEM
    fmt = call["text"]["format"]
    assert fmt["type"] == "json_schema" and fmt["strict"] is True
    # 시스템 지시에 정답 역 이름(힌트)이 없다
    for hint in ["동대문역사문화공원", "서울역", "잠실", "홍대입구", "강남", "마천", "방화"]:
        assert hint not in answerers.SYSTEM


def test_registry_has_stub_and_llm_without_building_client(monkeypatch):
    import openai

    def boom(*a, **k):
        raise AssertionError("OpenAI()가 불렸다")

    monkeypatch.setattr(openai, "OpenAI", boom)
    assert list(ANSWERERS) == ["stub", "llm"]
    assert isinstance(ANSWERERS["stub"]("x"), Answer)


def test_llm_without_key_exits_2(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert main(["--answerer", "llm", "--out", str(tmp_path / "x.md")]) == 2
    assert "OPENAI_API_KEY가 없다" in capsys.readouterr().err
    assert not (tmp_path / "x.md").exists()


def test_api_error_exits_1_without_report(monkeypatch, tmp_path, capsys):
    import openai

    def fail(text):
        raise openai.APIError("연결 실패", request=None, body=None)

    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setitem(ANSWERERS, "llm", fail)
    out = tmp_path / "x.md"
    assert main(["--answerer", "llm", "--out", str(out)]) == 1
    assert "API 오류" in capsys.readouterr().err
    assert not out.exists()


def test_replay_recorded_responses_end_to_end(monkeypatch, tmp_path):
    # tests/fixtures/llm_responses.json에 녹화한 실제 응답 원문을 재생한다. API는 부르지 않는다
    fixture = json.loads((ROOT / "tests" / "fixtures" / "llm_responses.json").read_text("utf-8"))
    questions = use_recorded_questions(monkeypatch, tmp_path, fixture)
    queue = [fixture[q["id"]] for q in questions]

    class Replay:
        def __init__(self):
            self.responses = SimpleNamespace(create=self._create)

        def _create(self, **kwargs):
            rec = queue.pop(0)
            usage = SimpleNamespace(input_tokens=rec["tokens"], output_tokens=0)
            return SimpleNamespace(output_text=rec["raw"], usage=usage)

    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setitem(ANSWERERS, "llm", make_llm(Replay()))
    out = tmp_path / "llm.md"
    assert main(["--answerer", "llm", "--out", str(out)]) == 0
    rows = {
        line.split(" | ")[0].lstrip("| "): line.split(" | ")
        for line in out.read_text(encoding="utf-8").splitlines()
    }
    text = out.read_text(encoding="utf-8")
    assert "- 파싱 실패 0/3" in text and f"(모델 {answerers.MODEL})" in text
    for q in questions:
        assert q["id"] in rows
        # 읽지 못한 행은 답 있음 X, 읽은 행은 O
        expect = "X" if fixture[q["id"]]["parse_error"] else "O"
        assert rows[q["id"]][3] == expect
    # 녹화한 응답은 모두 정답과 다르다(경로 끊김). 지어낸 역 열은 q1 1, q2 4, q3 0이었다
    assert [rows[q["id"]][4] for q in questions] == ["X", "X", "X"]


def test_replay_with_unreadable_response_marks_row_x_and_counts_failure(monkeypatch, tmp_path):
    fixture = json.loads((ROOT / "tests" / "fixtures" / "llm_responses.json").read_text("utf-8"))
    use_recorded_questions(monkeypatch, tmp_path, fixture)
    raws = [fixture["q1"]["raw"], "이건 JSON이 아니다", fixture["q3"]["raw"]]

    class Replay:
        def __init__(self):
            self.responses = SimpleNamespace(create=lambda **kw: SimpleNamespace(
                output_text=raws.pop(0),
                usage=SimpleNamespace(input_tokens=1, output_tokens=1)))

    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setitem(ANSWERERS, "llm", make_llm(Replay()))
    out = tmp_path / "llm.md"
    assert main(["--answerer", "llm", "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "- 파싱 실패 1/3" in text
    rows = {line.split(" | ")[0].lstrip("| "): line.split(" | ") for line in text.splitlines()}
    assert [rows[q][3] for q in ("q1", "q2", "q3")] == ["O", "X", "O"]


def test_api_error_midway_keeps_raw_of_answered_questions(monkeypatch, tmp_path):
    import openai

    calls = []

    def flaky(text):
        calls.append(text)
        if len(calls) == 2:
            raise openai.APIError("연결 실패", request=None, body=None)
        return Answer(raw=GOOD, tokens=7)

    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setitem(ANSWERERS, "llm", flaky)
    raw, out = tmp_path / "raw.json", tmp_path / "x.md"
    assert main(["--answerer", "llm", "--out", str(out), "--raw", str(raw)]) == 1
    saved = json.loads(raw.read_text(encoding="utf-8"))
    assert list(saved) == ["q1"] and saved["q1"] == {"raw": GOOD, "tokens": 7, "parse_error": None}
    assert not out.exists()


def test_api_error_propagates_out_of_make_llm():
    import openai

    client = FakeClient(GOOD)

    def fail(**kwargs):
        raise openai.APIError("연결 실패", request=None, body=None)

    client.responses = SimpleNamespace(create=fail)
    with pytest.raises(openai.APIError):
        make_llm(client)("질문")
