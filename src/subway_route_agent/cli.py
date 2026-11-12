import argparse
import json
import os
import sys
import time
from pathlib import Path

import openai

from subway_route_agent.answerers import ANSWERERS, MODEL, TOOL_CALL_LIMIT
from subway_route_agent.data import DATA, ROOT, load_rows
from subway_route_agent.grade import _minutes, grade
from subway_route_agent.graph import ALIASES, Graph, build_graph
from subway_route_agent.report import Result, render, render_compare
from subway_route_agent.route import Route, shortest
from subway_route_agent.tools import TOOLS

QUESTIONS = ROOT / "data" / "questions.json"
REPORT_DIR = ROOT / "reports"


def _write_raw(path: Path, results: list[Result]) -> None:
    raw = {r.qid: {"raw": r.answer.raw, "tokens": r.answer.tokens,
                   "parse_error": r.answer.parse_error,
                   "tool_log": r.answer.tool_log} for r in results}
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


LLM_ANSWERERS = ("llm", "llm-tools")


def _raw_path(raw: Path, name: str, many: bool) -> Path:
    return raw.with_name(f"{raw.stem}-{name}{raw.suffix}") if many else raw


def _notes(name: str) -> list[str]:
    if name != "llm-tools":
        return []
    tools = ", ".join(t["name"] for t in TOOLS)
    return [f"도구: {tools} (호출 상한 {TOOL_CALL_LIMIT})"]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="subway-eval")
    p.add_argument("--answerer", nargs="+", choices=sorted(ANSWERERS), default=["stub"])
    p.add_argument("--out", type=Path, default=None,
                   help="답하는 쪽이 하나면 그 리포트, 둘 이상이면 비교 리포트 경로")
    p.add_argument("--raw", type=Path, default=None,
                   help="질문별 LLM 원문을 JSON으로 쓴다. 둘 이상이면 <파일명>-<이름>.json")
    args = p.parse_args(argv)
    names = list(dict.fromkeys(args.answerer))  # 같은 이름은 한 번만 돈다
    many = len(names) > 1
    if any(n in LLM_ANSWERERS for n in names) and not os.environ.get("OPENAI_API_KEY"):
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

    by_answerer: dict[str, list[Result]] = {}
    for name in names:
        answer = ANSWERERS[name]
        results = []
        for q in questions:
            truth = truth_for(g, q)
            t0 = time.perf_counter()
            try:
                ans = answer(q["text"])  # 답하는 쪽은 문장만 받는다
            except openai.APIError as e:
                print(f"API 오류({name} {q['id']}): {e}", file=sys.stderr)
                if args.raw:  # 이미 받은 답의 원문은 잃지 않는다. 리포트는 쓰지 않는다
                    _write_raw(_raw_path(args.raw, name, many), results)
                return 1
            ms = (time.perf_counter() - t0) * 1000
            results.append(Result(q["id"], truth, ans, grade(g, q, ans, truth), ms,
                                  "hand_seconds" in q))
        if args.raw:
            _write_raw(_raw_path(args.raw, name, many), results)
        by_answerer[name] = results

    models = {n: MODEL if n in LLM_ANSWERERS else None for n in names}
    for name, results in by_answerer.items():
        text = render(name, DATA.name, results, models[name], _notes(name))
        out = args.out if args.out and not many else REPORT_DIR / f"{name}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(text, end="")
    if many:
        text = render_compare(DATA.name, by_answerer, models, g)
        out = args.out or REPORT_DIR / "compare.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(text, end="")
    return 0
