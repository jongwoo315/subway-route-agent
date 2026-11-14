import argparse
import json
import os
import sys
import time
from pathlib import Path

import openai

from subway_route_agent.answerers import ANSWERERS, MODEL, TOOL_CALL_LIMIT
from subway_route_agent.data import DATA, ROOT, load_rows, load_transfers
from subway_route_agent.grade import _minutes, grade
from subway_route_agent.graph import ALIASES, Graph, build_graph, count_transfers
from subway_route_agent.report import Result, render, render_compare
from subway_route_agent.route import Route, shortest
from subway_route_agent.tools import COARSE_TOOLS, FINE_TOOLS

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


LLM_ANSWERERS = ("llm", "llm-tools", "llm-tools-coarse")
TOOL_SETS = {"llm-tools": FINE_TOOLS, "llm-tools-coarse": COARSE_TOOLS}


def _raw_path(raw: Path, name: str, many: bool, rnd: int, repeat: int) -> Path:
    """답하는 쪽이 둘 이상이면 이름을, 회차가 둘 이상이면 회차(1부터)를 파일명에 붙인다."""
    if repeat > 1:
        return raw.with_name(f"{raw.stem}-{name}-{rnd}{raw.suffix}")
    return raw.with_name(f"{raw.stem}-{name}{raw.suffix}") if many else raw


def _notes(name: str) -> list[str]:
    if name not in TOOL_SETS:
        return []
    tools = ", ".join(t["name"] for t in TOOL_SETS[name])
    return [f"도구: {tools} (호출 상한 {TOOL_CALL_LIMIT})"]


def _repeat(value: str) -> int:
    n = int(value)
    if n < 1:
        raise argparse.ArgumentTypeError("1 이상이어야 한다")
    return n


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="subway-eval")
    p.add_argument("--answerer", nargs="+", choices=sorted(ANSWERERS), default=["stub"])
    p.add_argument("--out", type=Path, default=None,
                   help="답하는 쪽이 하나면 그 리포트, 둘 이상이면 비교 리포트 경로")
    p.add_argument("--raw", type=Path, default=None,
                   help="질문별 LLM 원문을 JSON으로 쓴다. 둘 이상이면 <파일명>-<이름>.json, "
                        "--repeat이 2 이상이면 <파일명>-<이름>-<회차>.json")
    p.add_argument("--repeat", type=_repeat, default=1,
                   help="답하는 쪽마다 질문 셋을 이만큼 되풀이해 돈다(기본 1)")
    args = p.parse_args(argv)
    names = list(dict.fromkeys(args.answerer))  # 같은 이름은 한 번만 돈다
    many = len(names) > 1
    if any(n in LLM_ANSWERERS for n in names) and not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY가 없다", file=sys.stderr)
        return 2

    transfers = load_transfers()
    g = build_graph(load_rows(), transfers)
    counts = count_transfers(g, transfers)
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    stations = {n[0] for n in g}
    missing = [(q["id"], s) for q in questions for s in (q["origin"], q["dest"])
               if _graph_name(s) not in stations]
    for qid, station in missing:
        print(f"질문 {qid}: 그래프에 없는 역 — {station}", file=sys.stderr)
    if missing:
        return 2

    by_answerer: dict[str, list[list[Result]]] = {}
    for name in names:
        answer = ANSWERERS[name]
        by_answerer[name] = []
        for rnd in range(1, args.repeat + 1):
            results = []
            for q in questions:
                truth = truth_for(g, q)
                t0 = time.perf_counter()
                try:
                    ans = answer(q["text"])  # 답하는 쪽은 문장만 받는다
                except openai.APIError as e:
                    print(f"API 오류({name} {q['id']}, {rnd}회차): {e}", file=sys.stderr)
                    if args.raw:  # 이미 받은 답의 원문은 잃지 않는다. 리포트는 쓰지 않는다
                        _write_raw(_raw_path(args.raw, name, many, rnd, args.repeat), results)
                    return 1
                ms = (time.perf_counter() - t0) * 1000
                results.append(Result(q["id"], truth, ans, grade(g, q, ans, truth), ms,
                                      "hand_seconds" in q))
            if args.raw:
                _write_raw(_raw_path(args.raw, name, many, rnd, args.repeat), results)
            by_answerer[name].append(results)

    models = {n: MODEL if n in LLM_ANSWERERS else None for n in names}
    for name, rounds in by_answerer.items():
        notes = _notes(name)
        if args.repeat > 1:
            notes.append(f"{args.repeat}회 중 마지막 회차 결과다")
        text = render(name, DATA.name, rounds[-1], models[name], notes, counts)
        out = args.out if args.out and not many else REPORT_DIR / f"{name}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(text, end="")
    if many:
        text = render_compare(DATA.name, by_answerer, models, g, counts)
        out = args.out or REPORT_DIR / "compare.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(text, end="")
    return 0
