from dataclasses import dataclass
from itertools import pairwise

from subway_route_agent.answerers import LIMIT_REACHED, Answer
from subway_route_agent.grade import Grade, fill_path, path_seconds
from subway_route_agent.graph import TRANSFER_SECONDS, Graph, TransferCounts
from subway_route_agent.route import Route
from subway_route_agent.tools import COARSE_TOOLS, FINE_TOOLS

COLUMNS = [
    "질문", "정답 경로", "정답 시간", "답 있음", "맞음", "채운 역", "지어낸 역",
    "지어낸 소요 시간", "조건 어김", "도구 호출", "응답 시간(ms)", "토큰",
]


@dataclass
class Result:
    qid: str
    truth: Route | None
    answer: Answer
    grade: Grade
    elapsed_ms: float
    hand_checked: bool = False  # 질문에 직접 계산한 값(hand_seconds)이 있다


def format_seconds(sec: int | None) -> str:
    if sec is None:
        return "없음"
    return f"{sec // 60}분 {sec % 60}초"


def format_path(route: Route | None) -> str:
    """출발역 · 갈아탄 역 · 도착역만 호선과 함께 쓴다."""
    if route is None:
        return "없음"
    nodes = route.nodes
    parts = [f"{nodes[0][0]}({nodes[0][1]})"]
    for a, b in pairwise(nodes):
        if a[1] != b[1]:
            parts.append(f"{a[0]}({a[1]}→{b[1]})")
    parts.append(f"{nodes[-1][0]}({nodes[-1][1]})")
    return " → ".join(parts)


def transfer_head(counts: TransferCounts | None) -> list[str]:
    """리포트 머리의 환승 시간 줄. 출처 한 줄과, 그 실행의 그래프에서 센 환승역 수 한 줄이다."""
    lines = [
        "- 환승 시간: 서울교통공사 환승역 거리·소요시간 "
        "(data.go.kr 15044419, 2026-08-31 기준, 최단 환승거리 ÷ 초당 1.2m)"
    ]
    if counts is not None:
        left = counts.default_stations
        names = f"({', '.join(left)})" if left else ""
        lines.append(
            f"- 데이터 환승 시간을 쓴 환승역 {counts.data_stations}개 · "
            f"{TRANSFER_SECONDS}초가 남은 환승역 {len(left)}개{names} "
            f"(갈아타는 방향 {counts.directions}개 중 반대 방향 값 {counts.reverse}개). "
            "기다리는 시간은 0으로 본다")
    return lines


def _ox(flag: bool) -> str:
    return "O" if flag else "X"


def render(
    answerer: str, data_name: str, results: list[Result], model: str | None = None,
    notes: list[str] | None = None, counts: TransferCounts | None = None,
) -> str:
    n = len(results)
    hits = sum(r.grade.correct for r in results)
    rate = round(100 * hits / n) if n else 0
    parse_fails = sum(r.answer.parse_error is not None for r in results)
    with_truth = [r for r in results if r.truth is not None]
    hand_ok = sum(r.hand_checked for r in with_truth)
    who = f"{answerer} (모델 {model})" if model else answerer
    lines = [
        "# 리포트",
        "",
        f"- 답하는 쪽: {who}",
        *(f"- {note}" for note in notes or []),
        f"- 데이터: {data_name} (서울 열린데이터광장 OA-12034, 2024-08-10 기준, 1~8호선)",
        *transfer_head(counts),
        f"- 정답률 {hits}/{n} ({rate}%)",
        f"- 파싱 실패 {parse_fails}/{n}",
        f"- 직접 계산으로 확인한 정답: {hand_ok}/{len(with_truth)}",
        "",
        "| " + " | ".join(COLUMNS) + " |",
        "| " + " | ".join("---" for _ in COLUMNS) + " |",
    ]
    for r in results:
        g = r.grade
        lines.append(
            "| " + " | ".join([
                r.qid,
                format_path(r.truth),
                format_seconds(r.truth.seconds if r.truth else None),
                _ox(g.answered),
                _ox(g.correct),
                str(g.filled),
                str(g.invented_stations),
                str(g.invented_time),
                ", ".join(g.violations) or "없음",
                str(r.answer.tool_calls),
                f"{r.elapsed_ms:.2f}",
                str(r.answer.tokens),
            ]) + " |"
        )
    return "\n".join(lines) + "\n"


COMPARE_DIFF = (
    "LLM + 도구 지시문에만 도구 안내 한 문장과 「환승 시간은 역과 호선마다 다르다. "
    "경로는 직접 고른다」 문장이 있다"
)
COARSE_NOTE = "크게 묶은 도구는 한 호선의 역 목록을 볼 수 없다"
TOOL_ANSWERERS = ("llm-tools", "llm-tools-coarse")
COMPARE_COLUMNS = ["맞음", "채운 역", "답 경로 소요 시간", "답이 말한 시간"]
METRIC_COLUMNS = [
    "정답률", "지어낸 역", "지어낸 소요 시간", "질문당 도구 호출", "질문당 응답 시간(초)",
    "파싱 실패", "토큰", "도구 호출 상한에 닿은 질문",
]


def _path_cell(g: Graph, r: Result) -> str:
    if not r.answer.path:
        return "답 없음"
    given = [tuple(n) for n in r.answer.path]
    fill = fill_path(g, given)  # 채점과 같은 경로로 잰다. 못 채우면 답 경로 그대로
    actual = path_seconds(g, fill[0] if fill else given)
    return "끊김" if actual is None else format_seconds(actual)


def _metrics(rs: list[Result]) -> list[float]:
    """한 회차(질문 순서대로 쌓은 Result)의 지표 값. METRIC_COLUMNS 순서다."""
    n = max(len(rs), 1)
    return [
        sum(r.grade.correct for r in rs),
        sum(r.grade.invented_stations for r in rs),
        sum(bool(r.grade.invented_time) for r in rs),  # 질문 수로 센다
        sum(r.answer.tool_calls for r in rs) / n,
        sum(r.elapsed_ms for r in rs) / 1000 / n,
        sum(r.answer.parse_error is not None for r in rs),
        sum(r.answer.tokens for r in rs),
        sum(r.answer.parse_error == LIMIT_REACHED for r in rs),
    ]


def _metric_cell(col: int, value: float, n: int) -> str:
    if col == 0:
        return f"{value}/{n}"
    if col in (3, 4):
        return f"{value:.1f}"
    return str(int(value))


def _metric_rows(name: str, rounds: list[list[Result]]) -> list[str]:
    n = len(rounds[0])
    per_round = [_metrics(rs) for rs in rounds]
    rows = [[name, str(i), *(_metric_cell(c, v, n) for c, v in enumerate(vals))]
            for i, vals in enumerate(per_round, start=1)]
    span = [name, "범위"]
    for c in range(len(METRIC_COLUMNS)):
        col = [vals[c] for vals in per_round]
        span.append(f"{_metric_cell(c, min(col), n)}~{_metric_cell(c, max(col), n)}")
    return ["| " + " | ".join(row) + " |" for row in [*rows, span]]


def render_compare(
    data_name: str,
    by_answerer: dict[str, list[list[Result]]],
    models: dict[str, str | None],
    g: Graph,
    counts: TransferCounts | None = None,
) -> str:
    """답하는 쪽들의 결과를 질문마다 한 줄에 놓는다.

    by_answerer는 답하는 쪽 → 회차 → 질문(Result)이다. 회차가 하나여도 같은 모양이고,
    모든 회차가 같은 질문 순서다.
    """
    names = list(by_answerer)
    n_rounds = len(by_answerer[names[0]])
    n = len(by_answerer[names[0]][0])
    lines = [
        "# 비교 리포트",
        "",
        f"- 데이터: {data_name} (서울 열린데이터광장 OA-12034, 2024-08-10 기준, 1~8호선)",
        *transfer_head(counts),
        *([f"- {COMPARE_DIFF}"] if any(a in by_answerer for a in TOOL_ANSWERERS) else []),
    ]
    if all(a in by_answerer for a in TOOL_ANSWERERS):
        fine = ", ".join(t["name"] for t in FINE_TOOLS)
        coarse = ", ".join(t["name"] for t in COARSE_TOOLS)
        lines.append(f"- 도구 구성: llm-tools = {fine} / llm-tools-coarse = {coarse}. "
                     "두 지시문은 도구 안내 한 문장만 다르다")
    if "llm-tools-coarse" in by_answerer:
        lines.append(f"- {COARSE_NOTE}")
    if n_rounds == 1:
        for name in names:
            rs = by_answerer[name][0]
            said = sum(r.truth is not None and r.answer.seconds == r.truth.seconds for r in rs)
            capped = sum(r.answer.parse_error == LIMIT_REACHED for r in rs)
            unfilled = sum(r.grade.correct and r.grade.filled == 0 for r in rs)
            who = f"{name} (모델 {models[name]})" if models.get(name) else name
            lines.append(
                f"- {who}: 정답률 {sum(r.grade.correct for r in rs)}/{n}, "
                f"채우지 않고도 맞은 질문 {unfilled}/{n}, "
                f"파싱 실패 {sum(r.answer.parse_error is not None for r in rs)}/{n}, "
                f"도구 호출 {sum(r.answer.tool_calls for r in rs)}, "
                f"토큰 {sum(r.answer.tokens for r in rs)}, "
                f"응답 시간 합 {sum(r.elapsed_ms for r in rs) / 1000:.1f}초, "
                f"답이 말한 시간이 정답과 같은 질문 {said}/{n}, "
                f"도구 호출 상한에 닿은 질문 {capped}"
            )
        columns = ["질문", "정답 시간"] + [f"{name} {c}" for name in names for c in COMPARE_COLUMNS]
    else:
        lines.append(f"- 같은 질문 {n}개를 답하는 쪽마다 {n_rounds}번 돌렸다. "
                     "범위는 지표마다 회차 중 최저~최고다")
        lines += [f"- {name} (모델 {models[name]})" for name in names if models.get(name)]
        metric_columns = ["답하는 쪽", "회차", *METRIC_COLUMNS]
        lines += ["", "| " + " | ".join(metric_columns) + " |",
                  "| " + " | ".join("---" for _ in metric_columns) + " |"]
        for name in names:
            lines += _metric_rows(name, by_answerer[name])
        columns = ["질문", "정답 시간"] + [
            f"{name} {c}" for name in names for c in ("맞은 횟수", "도구 호출")]
    lines += ["", "| " + " | ".join(columns) + " |",
              "| " + " | ".join("---" for _ in columns) + " |"]
    for i in range(n):
        first = by_answerer[names[0]][0][i]
        cells = [first.qid, format_seconds(first.truth.seconds if first.truth else None)]
        for name in names:
            rounds = by_answerer[name]
            if n_rounds == 1:
                r = rounds[0][i]
                cells += [_ox(r.grade.correct), str(r.grade.filled), _path_cell(g, r),
                          format_seconds(r.answer.seconds)]
            else:
                hits = sum(rs[i].grade.correct for rs in rounds)
                cells += [f"{hits}/{n_rounds}",
                          "/".join(str(rs[i].answer.tool_calls) for rs in rounds)]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"
