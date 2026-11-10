# 판단 기록

착수 전 기준은 plan을 쓰기 전에 jw가 직접 쓴 한 줄이다. 결과는 루프가 잰 값이고,
판정과 이유는 PR 게이트에서 jw가 썼다. 자동 기준(plan §통과 기준)은 PR에 있다.

| 티켓 | 착수 전 기준 (jw) | 결과 | 판정 | 이유 (갈렸을 때만) | PR |
| --- | --- | --- | --- | --- | --- |
| #185 skeleton | 명령 하나로 전체 프로젝트가 처음부터 끝까지 잘 돈다 | PR HEAD를 새로 clone해 `uv run subway-eval` 하나만 실행했다. exit 0, `reports/skeleton.md` 생김, 질문 3개 모두 정답 경로·시간이 채워짐(29분 0초 · 24분 0초 · 66분 40초) | 통과 | 명령어 실행을 통해 리포트가 생성됨 | [#1](https://github.com/jongwoo315/subway-route-agent/pull/1) | <!-- style-exempt -->
| #186 LLM 혼자 | 경로질문에 대한 답변을 llm이 하도록 변경된다 | | | | |
