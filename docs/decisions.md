# 판단 기록

착수 전 기준은 plan을 쓰기 전에 jw가 직접 쓴 한 줄이다. 결과는 루프가 잰 값이고,
판정과 이유는 PR 게이트에서 jw가 썼다. 자동 기준(plan §통과 기준)은 PR에 있다.

| 티켓 | 착수 전 기준 (jw) | 결과 | 판정 | 이유 (갈렸을 때만) | PR |
| --- | --- | --- | --- | --- | --- |
| #185 skeleton | 명령 하나로 전체 프로젝트가 처음부터 끝까지 잘 돈다 | PR HEAD를 새로 clone해 `uv run subway-eval` 하나만 실행했다. exit 0, `reports/skeleton.md` 생김, 질문 3개 모두 정답 경로·시간이 채워짐(29분 0초 · 24분 0초 · 66분 40초) | 통과 | 명령어 실행을 통해 리포트가 생성됨 | [#1](https://github.com/jongwoo315/subway-route-agent/pull/1) | <!-- style-exempt -->
| #186 LLM 혼자 | 경로질문에 대한 답변을 llm이 하도록 변경된다 | 실제 키로 `uv run subway-eval --answerer llm`을 세 번 돌렸다(루프 2번, 리뷰 수정 뒤 HEAD에서 main 1번). 세 번 모두 exit 0, 답하는 쪽 `llm (모델 gpt-5.4-mini)`, 질문 3개 모두 `답 있음` O, 파싱 실패 0/3. 정답률은 세 번 모두 0/3 | 통과 | LLM이 모두 답을 했고 파싱 실패 건이 없음 | [#2](https://github.com/jongwoo315/subway-route-agent/pull/2) | <!-- style-exempt -->
| #187 질문 10개 | n개 질문으로 늘렸을 때에도 파싱 실패건이 없고, llm이 답변을 내놓는다 | 질문 10개로 실제 키를 써서 `uv run subway-eval --answerer llm`을 세 번 돌렸다(루프 2번, 리뷰 수정 뒤 HEAD에서 main 1번). 세 번 모두 exit 0, 파싱 실패 0/10, 질문 10개 모두 `답 있음` O. 정답 없음 질문 2개(q6·q7)에도 LLM은 「길이 없다」가 아니라 경로로 답했다. 정답률은 세 번 모두 0/10 | 통과 | 기준과 계획대로 진행됨, 볼것 세션에서 언급된 사항들은 현재 티켓들이 다 처리된 이후 확인예정 | [#3](https://github.com/jongwoo315/subway-route-agent/pull/3) | <!-- style-exempt -->
| #188 LLM + 도구 | 도구를 사용했을 때 역간 최단거리를 llm단독으로 계산했을 때보다 정확하게 계산한다, llm단독과 llm+도구로 같은 질의를 했을 때 결과를 비교할 수 있다 | 실제 키로 `uv run subway-eval --answerer stub llm llm-tools`를 여섯 번 돌렸다(루프 5번, 리뷰 수정 뒤 HEAD에서 main 1번). 여섯 번 모두 exit 0, `reports/compare.md`에 질문 10개마다 세 답하는 쪽 결과가 한 줄에 나온다. 정답률은 LLM 혼자 여섯 번 모두 0/10, LLM + 도구 1·0·1·0·0·0/10(맞은 것은 두 번 모두 q2). 답 경로의 같은 호선 중간 역을 채워 다시 채점하면 LLM + 도구 3~5/10, LLM 혼자 0~2/10(실행 5번) | 유보 | llm+도구가 더 나은 결과를 보여줬지만 정답률이 처참함, 지시문이 지켜지지 않은 이유와 채점방식에 대한 논의가 다시 이루어질 필요가 있음 (#193에서 다시) | [#4](https://github.com/jongwoo315/subway-route-agent/pull/4) | <!-- style-exempt -->
| #193 채점 방식 | 지나는 역을 확실히 채점을 하든지 이동 경로를 정확히 계산했다면 지나는 역이 모두 나오지 않아도 정답으로 보는 채점방식으로 수정한다 | | | | |
