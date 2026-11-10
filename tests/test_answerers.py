import json

from subway_route_agent.answerers import ANSWERERS, Answer, stub
from subway_route_agent.data import ROOT


def test_stub_returns_empty_answer_for_any_text():
    for text in ["강남에서 홍대입구까지", "", "아무 문장"]:
        a = stub(text)
        assert a == Answer(path=[], seconds=None, tool_calls=0)
        assert (a.parse_error, a.tokens, a.raw) == (None, 0, None)


def test_registry_has_stub_and_llm():
    assert list(ANSWERERS) == ["stub", "llm"]


def test_questions_file_has_three_questions_with_fields():
    qs = json.loads((ROOT / "data" / "questions.json").read_text(encoding="utf-8"))
    assert [q["id"] for q in qs] == ["q1", "q2", "q3"]
    for q in qs:
        assert {"text", "origin", "dest", "max_transfers", "depart", "arrive_by"} <= q.keys()
