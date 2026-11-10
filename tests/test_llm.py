import json
from types import SimpleNamespace

import pytest

from subway_route_agent import answerers
from subway_route_agent.answerers import ANSWERERS, Answer, make_llm
from subway_route_agent.cli import main
from subway_route_agent.data import ROOT


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
    ],
)
def test_unreadable_answer_sets_parse_error_without_raising(bad):
    ans = make_llm(FakeClient(bad, tokens=(7, 3)))("질문")
    assert ans.parse_error
    assert ans.path == [] and ans.seconds is None
    assert ans.raw == bad and ans.tokens == 10


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
    # 실제 호출(#186 raw-1)을 녹화한 원문을 재생한다. API는 부르지 않는다
    fixture = json.loads((ROOT / "tests" / "fixtures" / "llm_responses.json").read_text("utf-8"))
    questions = json.loads((ROOT / "data" / "questions.json").read_text("utf-8"))
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
    for q in questions:
        assert q["id"] in rows
        # 읽지 못한 행은 답 있음 X, 읽은 행은 O
        expect = "X" if fixture[q["id"]]["parse_error"] else "O"
        assert rows[q["id"]][3] == expect
