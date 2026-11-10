import argparse
import json
import os
import sys
import time
from pathlib import Path

import openai

from subway_route_agent.answerers import ANSWERERS, MODEL
from subway_route_agent.data import DATA, ROOT, load_rows
from subway_route_agent.grade import grade
from subway_route_agent.graph import build_graph
from subway_route_agent.report import Result, render
from subway_route_agent.route import shortest

QUESTIONS = ROOT / "data" / "questions.json"
REPORT_DIR = ROOT / "reports"


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
    answer = ANSWERERS[args.answerer]
    results = []
    for q in questions:
        truth = shortest(g, q["origin"], q["dest"], q["max_transfers"])
        t0 = time.perf_counter()
        try:
            ans = answer(q["text"])  # 답하는 쪽은 문장만 받는다
        except openai.APIError as e:
            print(f"API 오류: {e}", file=sys.stderr)
            return 1
        ms = (time.perf_counter() - t0) * 1000
        results.append(Result(q["id"], truth, ans, grade(g, q, ans, truth), ms))

    if args.raw:
        raw = {r.qid: {"raw": r.answer.raw, "tokens": r.answer.tokens,
                       "parse_error": r.answer.parse_error} for r in results}
        args.raw.parent.mkdir(parents=True, exist_ok=True)
        args.raw.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

    model = MODEL if args.answerer == "llm" else None
    text = render(args.answerer, DATA.name, results, model)
    out = args.out or REPORT_DIR / f"{args.answerer}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0
