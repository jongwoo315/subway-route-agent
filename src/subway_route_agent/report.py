from dataclasses import dataclass
from itertools import pairwise

from subway_route_agent.answerers import LIMIT_REACHED, Answer
from subway_route_agent.grade import Grade, fill_path, path_seconds
from subway_route_agent.graph import TRANSFER_SECONDS, Graph
from subway_route_agent.route import Route

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
    hand_checked: bool = False  # 질문에 손 계산 값(hand_seconds)이 있다


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


def _ox(flag: bool) -> str:
    return "O" if flag else "X"


def render(
    answerer: str, data_name: str, results: list[Result], model: str | None = None,
    notes: list[str] | None = None,
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
        f"- 환승 한 번에 {TRANSFER_SECONDS}초로 고정한 stub이다. 기다리는 시간은 0으로 본다",
        f"- 정답률 {hits}/{n} ({rate}%)",
        f"- 파싱 실패 {parse_fails}/{n}",
        f"- 손 계산으로 확인한 정답: {hand_ok}/{len(with_truth)}",
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


COMPARE_DIFF = f"LLM + 도구 지시문에만 환승 {TRANSFER_SECONDS}초와 도구 사용 안내가 있다"
COMPARE_COLUMNS = ["맞음", "채운 역", "답 경로 소요 시간", "답이 말한 시간"]


def _path_cell(g: Graph, r: Result) -> str:
    if not r.answer.path:
        return "답 없음"
    given = [tuple(n) for n in r.answer.path]
    fill = fill_path(g, given)  # 채점과 같은 경로로 잰다. 못 채우면 답 경로 그대로
    actual = path_seconds(g, fill[0] if fill else given)
    return "끊김" if actual is None else format_seconds(actual)


def render_compare(
    data_name: str,
    by_answerer: dict[str, list[Result]],
    models: dict[str, str | None],
    g: Graph,
) -> str:
    """답하는 쪽들의 결과를 질문마다 한 줄에 놓는다. by_answerer의 값은 같은 질문 순서다."""
    names = list(by_answerer)
    n = len(by_answerer[names[0]])
    lines = [
        "# 비교 리포트",
        "",
        f"- 데이터: {data_name} (서울 열린데이터광장 OA-12034, 2024-08-10 기준, 1~8호선)",
        f"- 환승 한 번에 {TRANSFER_SECONDS}초로 고정한 stub이다. 기다리는 시간은 0으로 본다",
        *([f"- {COMPARE_DIFF}"] if "llm-tools" in by_answerer else []),
    ]
    for name in names:
        rs = by_answerer[name]
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
    lines += ["", "| " + " | ".join(columns) + " |",
              "| " + " | ".join("---" for _ in columns) + " |"]
    for i in range(n):
        first = by_answerer[names[0]][i]
        cells = [first.qid, format_seconds(first.truth.seconds if first.truth else None)]
        for name in names:
            r = by_answerer[name][i]
            cells += [_ox(r.grade.correct), str(r.grade.filled), _path_cell(g, r),
                      format_seconds(r.answer.seconds)]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"
