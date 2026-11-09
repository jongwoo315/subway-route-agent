from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class Answer:
    path: list[tuple[str, int]] = field(default_factory=list)  # [(역, 호선)]
    seconds: int | None = None
    tool_calls: int = 0


def stub(question_text: str) -> Answer:
    """LLM 없이 고정된 답. 모든 질문에 빈 답을 돌려준다. 다음 티켓에서 LLM 혼자 / LLM + 도구가 이 자리에 들어간다."""
    return Answer()


# 답하는 쪽은 질문 문장만 받는다. 구조화된 필드는 채점만 쓴다
ANSWERERS: dict[str, Callable[[str], Answer]] = {"stub": stub}
