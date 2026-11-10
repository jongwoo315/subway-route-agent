import argparse
import json
import time
from pathlib import Path

from subway_route_agent.answerers import ANSWERERS
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
    args = p.parse_args(argv)

    g = build_graph(load_rows())
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    answer = ANSWERERS[args.answerer]
    results = []
    for q in questions:
        truth = shortest(g, q["origin"], q["dest"], q["max_transfers"])
        t0 = time.perf_counter()
        ans = answer(q["text"])  # 답하는 쪽은 문장만 받는다
        ms = (time.perf_counter() - t0) * 1000
        results.append(Result(q["id"], truth, ans, grade(g, q, ans, truth), ms))

    text = render(args.answerer, DATA.name, results)
    out = args.out or REPORT_DIR / f"{args.answerer}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0
