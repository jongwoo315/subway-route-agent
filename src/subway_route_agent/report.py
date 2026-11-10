from dataclasses import dataclass
from itertools import pairwise

from subway_route_agent.answerers import Answer
from subway_route_agent.grade import Grade
from subway_route_agent.graph import TRANSFER_SECONDS
from subway_route_agent.route import Route

COLUMNS = [
    "질문", "정답 경로", "정답 시간", "답 있음", "맞음", "지어낸 역",
    "지어낸 소요 시간", "조건 어김", "도구 호출", "응답 시간(ms)", "토큰",
]


@dataclass
class Result:
    qid: str
    truth: Route | None
    answer: Answer
    grade: Grade
    elapsed_ms: float


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
    answerer: str, data_name: str, results: list[Result], model: str | None = None
) -> str:
    n = len(results)
    hits = sum(r.grade.correct for r in results)
    rate = round(100 * hits / n) if n else 0
    parse_fails = sum(r.answer.parse_error is not None for r in results)
    who = f"{answerer} (모델 {model})" if model else answerer
    lines = [
        "# 리포트",
        "",
        f"- 답하는 쪽: {who}",
        f"- 데이터: {data_name} (서울 열린데이터광장 OA-12034, 2024-08-10 기준, 1~8호선)",
        f"- 환승 한 번에 {TRANSFER_SECONDS}초로 고정한 stub이다. 기다리는 시간은 0으로 본다",
        f"- 정답률 {hits}/{n} ({rate}%)",
        f"- 파싱 실패 {parse_fails}/{n}",
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
                str(g.invented_stations),
                str(g.invented_time),
                ", ".join(g.violations) or "없음",
                str(r.answer.tool_calls),
                f"{r.elapsed_ms:.2f}",
                str(r.answer.tokens),
            ]) + " |"
        )
    return "\n".join(lines) + "\n"
