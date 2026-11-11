"""#188 main 실행 원문을 새 채점으로 다시 채점한다. 실제 LLM 답이라 API 없이 쓴다."""

import json
from itertools import pairwise
from pathlib import Path

import pytest

from subway_route_agent.answerers import Answer, _parse
from subway_route_agent.cli import QUESTIONS, truth_for
from subway_route_agent.data import load_rows
from subway_route_agent.grade import _minutes, grade, path_seconds
from subway_route_agent.graph import build_graph

FIXTURES = Path(__file__).parent / "fixtures" / "gate188"
G = build_graph(load_rows())
QS = {q["id"]: q for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))}


def _answers(name: str) -> dict[str, Answer]:
    out = {}
    for qid, rec in json.loads((FIXTURES / name).read_text(encoding="utf-8")).items():
        try:
            path, seconds = _parse(rec["raw"] or "")
        except ValueError:
            path, seconds = [], None  # 실패·빈 경로는 답 없음
        out[qid] = Answer(path=path, seconds=seconds)
    return out


def _old_correct(q: dict, ans: Answer, truth) -> bool:
    """#188까지의 맞음 판정. fill_path를 거치지 않고 path_seconds만 쓴다."""
    if not ans.path or truth is None:
        return False
    path = [tuple(n) for n in ans.path]
    actual = path_seconds(G, path)
    if actual is None or path[0][0] != q["origin"] or path[-1][0] != q["dest"]:
        return False
    if q.get("max_transfers") is not None:
        if sum(a[1] != b[1] for a, b in pairwise(path)) > q["max_transfers"]:
            return False
    if q.get("arrive_by") and q.get("depart"):
        if _minutes(q["depart"]) * 60 + actual > _minutes(q["arrive_by"]) * 60:
            return False
    return actual == truth.seconds


@pytest.mark.parametrize("name", ["raw-llm.json", "raw-llm-tools.json"])
def test_full_path_answers_grade_like_188(name):
    unchanged = 0
    for qid, ans in _answers(name).items():
        q = QS[qid]
        truth = truth_for(G, q)
        new = grade(G, q, ans, truth)
        if ans.path and new.filled == 0:
            assert new.correct == _old_correct(q, ans, truth), (name, qid)
            unchanged += 1
    assert unchanged > 0  # 비교할 답이 하나도 없으면 이 테스트는 아무것도 안 잰다
