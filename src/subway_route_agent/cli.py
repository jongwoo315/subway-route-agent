import argparse
import json
import os
import sys
import time
from pathlib import Path

import openai

from subway_route_agent.answerers import ANSWERERS, MODEL
from subway_route_agent.data import DATA, ROOT, load_rows
from subway_route_agent.grade import _minutes, grade
from subway_route_agent.graph import ALIASES, Graph, build_graph
from subway_route_agent.report import Result, render
from subway_route_agent.route import Route, shortest

QUESTIONS = ROOT / "data" / "questions.json"
REPORT_DIR = ROOT / "reports"


def _write_raw(path: Path, results: list[Result]) -> None:
    raw = {r.qid: {"raw": r.answer.raw, "tokens": r.answer.tokens,
                   "parse_error": r.answer.parse_error} for r in results}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")


def _graph_name(station: str) -> str:
    return ALIASES.get(station, station)


def truth_for(g: Graph, q: dict) -> Route | None:
    """정답. 최단 경로로도 도착 시한을 못 맞추면 정답 없음(None)이다."""
    route = shortest(g, _graph_name(q["origin"]), _graph_name(q["dest"]), q["max_transfers"])
    if route and q.get("depart") and q.get("arrive_by"):
        if _minutes(q["depart"]) * 60 + route.seconds > _minutes(q["arrive_by"]) * 60:
            return None
    return route


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="subway-eval")
    p.add_argument("--answerer", choices=sorted(ANSWERERS), default="stub")
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--raw", type=Path, default=None, help="질문별 LLM 원문을 JSON으로 쓴다")
    args = p.parse_args(argv)
    if args.answerer == "llm" and not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY가 없다", file=sys.stderr)
        return 2

    g = build_graph(load_rows())
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    stations = {n[0] for n in g}
    missing = [(q["id"], s) for q in questions for s in (q["origin"], q["dest"])
               if _graph_name(s) not in stations]
    for qid, station in missing:
        print(f"질문 {qid}: 그래프에 없는 역 — {station}", file=sys.stderr)
    if missing:
        return 2

    answer = ANSWERERS[args.answerer]
    results = []
    for q in questions:
        truth = truth_for(g, q)
        t0 = time.perf_counter()
        try:
            ans = answer(q["text"])  # 답하는 쪽은 문장만 받는다
        except openai.APIError as e:
            print(f"API 오류({q['id']}): {e}", file=sys.stderr)
            if args.raw:  # 이미 받은 답의 원문은 잃지 않는다. 리포트는 쓰지 않는다
                _write_raw(args.raw, results)
            return 1
        ms = (time.perf_counter() - t0) * 1000
        results.append(Result(q["id"], truth, ans, grade(g, q, ans, truth), ms,
                              "hand_seconds" in q))

    if args.raw:
        _write_raw(args.raw, results)

    model = MODEL if args.answerer == "llm" else None
    text = render(args.answerer, DATA.name, results, model)
    out = args.out or REPORT_DIR / f"{args.answerer}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0
