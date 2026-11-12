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


# (원문 파일, 질문 수, 지나는 역을 다 쓴 답 수). 숫자를 박아 두어 파싱이 조용히 비어도 잡힌다
FULL_PATH_COUNTS = [("raw-llm.json", 10, 7), ("raw-llm-tools.json", 10, 2)]


@pytest.mark.parametrize("name,total,full", FULL_PATH_COUNTS)
def test_full_path_answers_grade_like_188(name, total, full):
    unchanged = 0
    answers = _answers(name)
    assert len(answers) == total
    for qid, ans in answers.items():
        q = QS[qid]
        truth = truth_for(G, q)
        new = grade(G, q, ans, truth)
        if ans.path and new.filled == 0:
            assert new.correct == _old_correct(q, ans, truth), (name, qid)
            unchanged += 1
    assert unchanged == full
