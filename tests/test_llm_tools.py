import json
from types import SimpleNamespace

import pytest

from subway_route_agent import answerers
from subway_route_agent.answerers import (
    ANSWERERS,
    SCHEMA,
    TOOL_CALL_LIMIT,
    TOOLS_SYSTEM,
    make_llm_tools,
)
from subway_route_agent.data import ROOT
from subway_route_agent.graph import TRANSFER_SECONDS
from subway_route_agent.tools import TOOLS

GOOD = json.dumps({
    "path": [{"station": "강남", "line": 2}, {"station": "홍대입구", "line": 2}],
    "seconds": 1740,
})


def call_item(call_id, name, args):
    return SimpleNamespace(type="function_call", call_id=call_id, name=name,
                           arguments=json.dumps(args, ensure_ascii=False))


def tool_outputs(items):
    return [i for i in items if isinstance(i, dict) and i.get("type") == "function_call_output"]


def response(output=(), text="", tokens=(10, 5), status="completed"):
    return SimpleNamespace(
        output=list(output), output_text=text, status=status,
        usage=SimpleNamespace(input_tokens=tokens[0], output_tokens=tokens[1]),
    )


class FakeClient:
    """미리 정한 응답을 차례로 돌려주는 가짜 client. API를 부르지 않는다."""

    def __init__(self, responses):
        self._queue = list(responses)
        self.calls: list[dict] = []
        self.responses = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        # 호출 시점의 입력을 복사해 둔다. 뒤에 이어 붙어도 이 호출의 입력은 그대로다
        self.calls.append({**kwargs, "input": list(kwargs["input"])})
        return self._queue.pop(0)


def test_two_tool_calls_then_final_answer_sums_tokens_and_returns_outputs():
    first = response([call_item("c1", "find_station", {"name": "강남"})], tokens=(100, 10))
    second = response([call_item("c2", "travel_seconds",
                                 {"line": 2, "from_station": "강남", "to_station": "홍대입구"})],
                      tokens=(200, 20))
    final = response([SimpleNamespace(type="message")], text=GOOD, tokens=(300, 30))
    client = FakeClient([first, second, final])
    ans = make_llm_tools(client)("질문")
    assert ans.tool_calls == 2
    assert ans.tokens == 110 + 220 + 330
    assert ans.path == [("강남", 2), ("홍대입구", 2)] and ans.seconds == 1740
    assert ans.raw == GOOD and ans.parse_error is None
    assert len(client.calls) == 3
    third_input = client.calls[2]["input"]
    outputs = tool_outputs(third_input)
    assert [o["call_id"] for o in outputs] == ["c1", "c2"]
    assert json.loads(outputs[0]["output"]) == {"found": True, "station": "강남", "lines": [2]}
    assert json.loads(outputs[1]["output"]) == {"seconds": 1740}
    # 응답의 output 항목이 그대로 입력에 이어 붙는다(호출 항목이 결과 앞에 온다)
    assert third_input[0] == {"role": "user", "content": "질문"}
    assert third_input[1] is first.output[0] and third_input[3] is second.output[0]


def test_tool_log_records_name_arguments_and_output_cut_to_200_chars():
    long_call = call_item("c2", "line_stations", {"line": 2})  # 결과가 200자를 넘는다
    client = FakeClient([
        response([call_item("c1", "find_station", {"name": "강남"})]),
        response([long_call]),
        response(text=GOOD),
    ])
    ans = make_llm_tools(client)("질문")
    assert [e["name"] for e in ans.tool_log] == ["find_station", "line_stations"]
    assert json.loads(ans.tool_log[0]["arguments"]) == {"name": "강남"}
    assert json.loads(ans.tool_log[0]["output"]) == {"found": True, "station": "강남", "lines": [2]}
    assert len(ans.tool_log[1]["output"]) == 200
    assert len(ans.tool_log) == ans.tool_calls == 2


@pytest.mark.parametrize("final", [response(text="JSON 아님"),
                                   response(text="", status="incomplete")])
def test_tool_log_is_kept_when_final_answer_fails(final):
    client = FakeClient([response([call_item("c1", "find_station", {"name": "강남"})]), final])
    ans = make_llm_tools(client)("질문")
    assert ans.parse_error and [e["name"] for e in ans.tool_log] == ["find_station"]


def test_tool_log_is_kept_when_limit_is_reached():
    looping = [response([call_item(f"c{i}", "find_station", {"name": "강남"})])
               for i in range(TOOL_CALL_LIMIT + 2)]
    ans = make_llm_tools(FakeClient(looping))("질문")
    assert len(ans.tool_log) == TOOL_CALL_LIMIT


def test_request_has_tools_instructions_and_same_schema_as_llm_alone():
    client = FakeClient([response(text=GOOD)])
    make_llm_tools(client)("서울역에서 잠실까지")
    (call,) = client.calls
    assert call["model"] == answerers.MODEL
    assert call["instructions"] == TOOLS_SYSTEM
    assert call["input"] == [{"role": "user", "content": "서울역에서 잠실까지"}]
    assert call["tools"] == TOOLS
    fmt = call["text"]["format"]
    assert fmt["type"] == "json_schema" and fmt["strict"] is True and fmt["schema"] is SCHEMA


def test_tool_call_limit_stops_with_fixed_parse_error():
    n = TOOL_CALL_LIMIT
    assert n == 25
    looping = [response([call_item(f"c{i}", "find_station", {"name": "강남"})], text=f"t{i}",
                        tokens=(1, 1)) for i in range(n + 5)]
    client = FakeClient(looping)
    ans = make_llm_tools(client)("질문")
    assert ans.parse_error == "도구 호출 상한(25)에 닿았다"
    assert ans.tool_calls == n and ans.path == [] and ans.seconds is None
    assert len(client.calls) == n + 1  # 26번째 호출은 실행하지 않고 멈춘다
    assert ans.tokens == 2 * (n + 1)
    assert ans.raw == f"t{n}"  # 마지막 응답의 output_text


def test_parallel_calls_in_one_response_are_all_executed_and_counted():
    both = response([call_item("a", "find_station", {"name": "강남"}),
                     call_item("b", "line_stations", {"line": 7})])
    client = FakeClient([both, response(text=GOOD)])
    ans = make_llm_tools(client)("질문")
    assert ans.tool_calls == 2
    ids = [i["call_id"] for i in tool_outputs(client.calls[1]["input"])]
    assert ids == ["a", "b"]


def test_bad_tool_arguments_go_back_to_model_as_error_json():
    bad = response([SimpleNamespace(type="function_call", call_id="x", name="travel_seconds",
                                    arguments="not json")])
    client = FakeClient([bad, response(text=GOOD)])
    ans = make_llm_tools(client)("질문")
    (out,) = tool_outputs(client.calls[1]["input"])
    assert "error" in json.loads(out["output"])
    assert ans.tool_calls == 1 and ans.parse_error is None


@pytest.mark.parametrize("bad", ["JSON 아님", json.dumps({"seconds": 10}),
                                 json.dumps({"path": [], "seconds": 1})])
def test_unreadable_final_answer_sets_parse_error(bad):
    ans = make_llm_tools(FakeClient([response(text=bad, tokens=(4, 1))]))("질문")
    assert ans.parse_error and ans.path == [] and ans.raw == bad and ans.tokens == 5


def test_unfinished_final_response_is_not_a_json_error():
    ans = make_llm_tools(FakeClient([response(text="", status="incomplete")]))("질문")
    assert "incomplete" in ans.parse_error and ans.path == []


def test_missing_usage_counts_zero_tokens():
    resp = response(text=GOOD)
    resp.usage = None
    assert make_llm_tools(FakeClient([resp]))("질문").tokens == 0


def test_tools_system_has_transfer_seconds_and_no_station_hints():
    assert f"{TRANSFER_SECONDS}초" in TOOLS_SYSTEM
    assert TOOLS_SYSTEM.startswith(answerers.SYSTEM)  # 답 형식 설명은 LLM 혼자와 같다
    for hint in ["동대문역사문화공원", "서울역", "잠실", "홍대입구", "강남", "마천", "방화"]:
        assert hint not in TOOLS_SYSTEM


def test_registry_has_llm_tools_without_building_client(monkeypatch):
    import openai

    def boom(*a, **k):
        raise AssertionError("OpenAI()가 불렸다")

    monkeypatch.setattr(openai, "OpenAI", boom)
    assert list(ANSWERERS) == ["stub", "llm", "llm-tools"]
    assert callable(ANSWERERS["llm-tools"])


# ---- 녹화한 응답 재생 (실제 키로 scripts/record_llm_tools.py가 녹화) ----

FIXTURE = ROOT / "tests" / "fixtures" / "llm_tools_responses.json"


def to_namespace(obj):
    if isinstance(obj, dict):
        return SimpleNamespace(**{k: to_namespace(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return [to_namespace(v) for v in obj]
    return obj


def test_replay_recorded_tool_calls_end_to_end(monkeypatch, tmp_path):
    from subway_route_agent.cli import main
    from test_llm import use_recorded_questions

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert list(fixture) == ["q4", "q10"]
    use_recorded_questions(monkeypatch, tmp_path, list(fixture))
    queue = [to_namespace(r) for rec in fixture.values() for r in rec["responses"]]
    seen = []

    class Replay:
        def __init__(self):
            self.responses = SimpleNamespace(create=self._create)

        def _create(self, **kwargs):
            seen.append(kwargs)
            return queue.pop(0)

    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setitem(ANSWERERS, "llm-tools", make_llm_tools(Replay()))
    out, raw = tmp_path / "llm-tools.md", tmp_path / "raw.json"
    assert main(["--answerer", "llm-tools", "--out", str(out), "--raw", str(raw)]) == 0
    assert queue == []  # 녹화한 응답을 모두 차례로 썼다
    text = out.read_text(encoding="utf-8")
    header = next(ln for ln in text.splitlines() if ln.startswith("| 질문"))
    cols = [c.strip() for c in header.strip("| ").split(" | ")]
    rows = {ln.strip("| ").split(" | ")[0]: [c.strip() for c in ln.strip("| ").split(" | ")]
            for ln in text.splitlines() if ln.startswith("| q")}
    saved = json.loads(raw.read_text(encoding="utf-8"))
    for qid, rec in fixture.items():
        assert rows[qid][cols.index("도구 호출")] == str(rec["tool_calls"])
        assert int(rec["tool_calls"]) > 0
        assert rows[qid][cols.index("토큰")] == str(rec["tokens"])
        assert len(saved[qid]["tool_log"]) == rec["tool_calls"]
    assert "- 파싱 실패 0/2" in text
    # 녹화 때 모델이 부른 도구가 모두 실제 도구 이름이다
    called = {i.name for r in (to_namespace(r) for rec in fixture.values()
                               for r in rec["responses"]) for i in r.output
              if i.type == "function_call"}
    assert called <= {t["name"] for t in TOOLS}
    assert json.loads(raw.read_text(encoding="utf-8"))["q10"]["parse_error"] is None
