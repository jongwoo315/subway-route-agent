"""실제 키로 LLM + 도구를 질문 2개(q4, q10)에 돌려 응답을 tests/fixtures에 녹화한다.

실행: uv run python scripts/record_llm_tools.py
"""

import json
from pathlib import Path

import openai

from subway_route_agent.answerers import make_llm_tools

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "llm_tools_responses.json"
QUESTION_IDS = ("q4", "q10")


class Recorder:
    """client.responses.create가 돌려준 응답을 dict로 쌓는다."""

    def __init__(self, client):
        self.records: list[dict] = []
        self.responses = type("R", (), {"create": self._create})()
        self._client = client

    def _create(self, **kwargs):
        resp = self._client.responses.create(**kwargs)
        record = resp.model_dump()
        record["output_text"] = resp.output_text  # 속성이라 model_dump에 없다
        self.records.append(record)
        return resp


def main() -> None:
    questions = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
    client = openai.OpenAI()
    recorded = {}
    for q in (q for q in questions if q["id"] in QUESTION_IDS):
        rec = Recorder(client)
        ans = make_llm_tools(rec)(q["text"])
        recorded[q["id"]] = {"responses": rec.records, "tool_calls": ans.tool_calls,
                             "tokens": ans.tokens, "parse_error": ans.parse_error}
        print(q["id"], "도구 호출", ans.tool_calls, "토큰", ans.tokens, ans.parse_error)
    OUT.write_text(json.dumps(recorded, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
