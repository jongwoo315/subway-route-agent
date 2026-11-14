import json
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cache

from subway_route_agent.tools import COARSE_TOOLS, FINE_TOOLS, call_tool


@dataclass
class Answer:
    path: list[tuple[str, int]] = field(default_factory=list)  # [(역, 호선)]
    seconds: int | None = None
    tool_calls: int = 0
    parse_error: str | None = None  # LLM 원문을 답 형식으로 읽지 못한 이유
    tokens: int = 0  # 입력 + 출력 토큰
    raw: str | None = None  # LLM 원문
    tool_log: list[dict] = field(default_factory=list)  # 도구 호출마다 {name, arguments, output}


def stub(question_text: str) -> Answer:
    """LLM 없이 고정된 답. 모든 질문에 빈 답을 돌려준다.

    키 없이 끝까지 도는 기본 답하는 쪽이다. LLM 혼자는 `llm`, LLM + 도구는 `llm-tools`가 맡는다.
    """
    return Answer()


MODEL = os.environ.get("OPENAI_MODEL") or "gpt-5.4-mini"

# LLM 혼자: 역 목록·정답·질문별 힌트를 넣지 않는다. 답 형식만 설명한다
SYSTEM = (
    "서울 지하철 1~8호선만 써서 질문에 답한다. "
    "출발역부터 도착역까지 지나는 역을 빠짐없이 순서대로 path에 쓰고, "
    "역마다 그 구간에서 탄 호선 번호(1~8)를 line에 쓴다. "
    "갈아타는 역은 내리는 호선으로 한 번, 타는 호선으로 한 번, 같은 역을 두 번 쓴다. "
    "seconds는 전체 소요 시간을 초 단위 정수로 쓴다. 모르면 null이다."
)

SCHEMA = {
    "type": "object",
    "properties": {
        "path": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"station": {"type": "string"}, "line": {"type": "integer"}},
                "required": ["station", "line"],
                "additionalProperties": False,
            },
        },
        "seconds": {"type": ["integer", "null"]},
    },
    "required": ["path", "seconds"],
    "additionalProperties": False,
}


def _parse(raw: str) -> tuple[list[tuple[str, int]], int | None]:
    """원문을 (path, seconds)로 읽는다. 읽지 못하면 ValueError(이유 한 줄)."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON이 아니다: {e.msg}") from e
    if not isinstance(data, dict) or not isinstance(data.get("path"), list):
        raise ValueError("path 목록이 없다")
    if not data["path"]:
        raise ValueError("path가 비어 있다")
    path = []
    for i, step in enumerate(data["path"]):
        st, ln = (step.get("station"), step.get("line")) if isinstance(step, dict) else (None, None)
        if not isinstance(st, str) or not isinstance(ln, int) or isinstance(ln, bool):
            raise ValueError(f"path[{i}]가 (station: str, line: int)가 아니다")
        path.append((st, ln))
    sec = data.get("seconds")
    if sec is not None and (not isinstance(sec, int) or isinstance(sec, bool)):
        raise ValueError("seconds가 정수나 null이 아니다")
    return path, sec


def make_llm(client=None) -> Callable[[str], Answer]:
    """질문 문장만 LLM에 보내는 답하는 쪽. client를 안 주면 openai.OpenAI()를 쓴다."""
    if client is None:
        import openai

        client = openai.OpenAI()

    def llm(question_text: str) -> Answer:
        resp = client.responses.create(
            model=MODEL,
            instructions=SYSTEM,
            input=question_text,
            text={"format": {"type": "json_schema", "name": "route", "schema": SCHEMA,
                             "strict": True}},
        )
        raw = resp.output_text
        usage = resp.usage
        tokens = usage.input_tokens + usage.output_tokens if usage else 0
        status = getattr(resp, "status", "completed")
        if status != "completed":  # 거절·토큰 한도로 끊긴 응답은 JSON 오류와 구분한다
            return Answer(parse_error=f"응답이 끝나지 않았다({status})", raw=raw, tokens=tokens)
        try:
            path, seconds = _parse(raw)
        except ValueError as e:
            return Answer(parse_error=str(e), raw=raw, tokens=tokens)
        return Answer(path=path, seconds=seconds, raw=raw, tokens=tokens)

    return llm


TOOL_CALL_LIMIT = 25
LIMIT_REACHED = f"도구 호출 상한({TOOL_CALL_LIMIT})에 닿았다"  # 리포트가 이 문자열로 센다

# LLM + 도구: 답 형식 설명은 SYSTEM 그대로. 역 목록·정답·질문별 힌트는 넣지 않는다.
# 두 도구 구성의 지시문은 도구 안내 한 문장만 다르다
_TOOLS_TAIL = " 환승 시간은 역과 호선마다 다르다. 경로는 직접 고른다."
TOOLS_SYSTEM = (
    SYSTEM + " 도구로 역·노선·한 호선 안 소요 시간·환승 시간을 확인할 수 있다." + _TOOLS_TAIL
)
COARSE_SYSTEM = SYSTEM + " 도구로 고른 경로의 전체 소요 시간을 확인할 수 있다." + _TOOLS_TAIL


def make_llm_tools(
    client=None, tools: list[dict] = FINE_TOOLS, system: str = TOOLS_SYSTEM,
) -> Callable[[str], Answer]:
    """질문 문장과 도구 구성을 LLM에 주고, 도구 호출 없는 응답이 올 때까지 되풀이하는 답하는 쪽."""
    if client is None:
        import openai

        client = openai.OpenAI()

    def llm_tools(question_text: str) -> Answer:
        items: list = [{"role": "user", "content": question_text}]
        tokens = tool_calls = 0
        tool_log: list[dict] = []
        while True:
            resp = client.responses.create(
                model=MODEL,
                instructions=system,
                input=items,
                tools=tools,
                text={"format": {"type": "json_schema", "name": "route", "schema": SCHEMA,
                                 "strict": True}},
            )
            usage = resp.usage
            tokens += usage.input_tokens + usage.output_tokens if usage else 0
            calls = [i for i in resp.output if i.type == "function_call"]
            if not calls:
                break
            items.extend(resp.output)
            for c in calls:
                if tool_calls >= TOOL_CALL_LIMIT:
                    return Answer(
                        parse_error=LIMIT_REACHED,
                        tool_calls=tool_calls, tokens=tokens, raw=resp.output_text,
                        tool_log=tool_log,
                    )
                tool_calls += 1
                output = call_tool(c.name, c.arguments, tools)
                tool_log.append({"name": c.name, "arguments": c.arguments, "output": output[:200]})
                items.append({"type": "function_call_output", "call_id": c.call_id,
                              "output": output})
        raw = resp.output_text
        status = getattr(resp, "status", "completed")
        if status != "completed":  # 거절·토큰 한도로 끊긴 응답은 JSON 오류와 구분한다
            return Answer(parse_error=f"응답이 끝나지 않았다({status})", raw=raw,
                          tokens=tokens, tool_calls=tool_calls, tool_log=tool_log)
        try:
            path, seconds = _parse(raw)
        except ValueError as e:
            return Answer(parse_error=str(e), raw=raw, tokens=tokens, tool_calls=tool_calls,
                          tool_log=tool_log)
        return Answer(path=path, seconds=seconds, raw=raw, tokens=tokens, tool_calls=tool_calls,
                      tool_log=tool_log)

    return llm_tools


@cache
def _llm() -> Callable[[str], Answer]:
    return make_llm()


@cache
def _llm_tools() -> Callable[[str], Answer]:
    return make_llm_tools()


@cache
def _llm_tools_coarse() -> Callable[[str], Answer]:
    return make_llm_tools(tools=COARSE_TOOLS, system=COARSE_SYSTEM)


# 답하는 쪽은 질문 문장만 받는다. 구조화된 필드는 채점만 쓴다.
# llm은 첫 호출 때 client를 만든다 (import만으로 키가 필요하면 안 된다)
ANSWERERS: dict[str, Callable[[str], Answer]] = {
    "stub": stub,
    "llm": lambda text: _llm()(text),
    "llm-tools": lambda text: _llm_tools()(text),
    "llm-tools-coarse": lambda text: _llm_tools_coarse()(text),
}
