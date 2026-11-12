# 개념과 용어

## 용어

plan·리포트·PR 본문·판단 기록에서 쓰는 말이다. 「쓰지 말 말」은 같은 개념을 가리키는 다른 이름이다.

| 용어 | 뜻 | 쓰지 말 말 | 제안자 | 만든 티켓 |
| --- | --- | --- | --- | --- |
| 답하는 쪽 | 질문 문장을 받아 경로와 소요 시간을 돌려주는 것. stub, LLM 혼자, LLM + 도구가 여기 들어간다 | 에이전트, 솔버 | Claude | #185 |
| 정답 | 다익스트라가 1~8호선 그래프에서 구한 경로와 소요 시간 | 기준 경로, 레퍼런스 | Claude | #185 |
| 지어낸 역 | 답 경로의 역 중 데이터에 없는 역 | 환각 역 | Claude | #185 |
| 지어낸 소요 시간 | 답이 말한 시간이 그 경로의 실제 소요 시간과 60초 넘게 다른 것 | | Claude | #185 |
| 조건 어김 | 출발역·도착역·환승 상한·도착 시한 중 하나를 안 지켰거나 경로가 끊긴 것 | 제약 위반 | Claude | #185 |
| 정답률 | 맞은 질문 수 ÷ 질문 수. 맞으려면 답이 있고, 빠진 역을 채운 경로가 이어지고, 조건 어김이 0개이고, 실제 소요 시간이 정답과 같아야 한다 | | Claude | #185, #193에서 고침 |
| LLM 혼자 | 질문 문장만 받고 역 목록·그래프·도구 없이 답하는 답하는 쪽 | 순수 LLM, 베이스라인 LLM | Claude | #186 |
| 파싱 실패 | LLM이 돌려준 원문을 정해진 답 형식으로 읽지 못한 것 | 형식 오류, 포맷 에러 | Claude | #186 |
| 직접 계산한 값 | 다익스트라를 쓰지 않고 CSV 구간 소요시간을 직접 더해 구한 정답 소요 시간 | 손 계산 값, 수동 정답, 기대값 | Claude | #187 |
| 정답 없음 | 출발역과 도착역은 그래프에 있지만, 환승 상한이나 도착 시한을 지키는 경로가 없는 질문 | 도달 불가, 답 없음 | Claude | #187 | <!-- style-exempt -->
| LLM + 도구 | 질문 문장과 도구 셋을 받아 도구를 불러 가며 답하는 답하는 쪽 | 에이전트, tool agent | Claude | #188 |
| 비교 리포트 | 명령 하나로 돌린 답하는 쪽들의 결과를 질문마다 한 줄에 놓은 리포트(`reports/compare.md`) | 대조표 | Claude | #188 |
| 답 경로 소요 시간 | 답이 낸 경로를 그래프로 잰 실제 소요 시간 | | Claude | #188 |
| 답이 말한 시간 | 답하는 쪽이 직접 말한 소요 시간(`Answer.seconds`) | | Claude | #188 |
| 채운 역 | 답 경로에서 빠진 중간 역을 채점이 채운 역. 같은 호선 안의 두 역 사이, 또는 한 번만 쓴 갈아타는 역에서만 채운다 | 보정 역, 보간 | Claude | #193 |

## 개념

코드에 이름이 있는 개념이다. 이름은 코드 식별자 그대로 쓴다.

| 이름 | 뜻 | 정의한 곳 | 만든 티켓 |
| --- | --- | --- | --- |
| `Answer.path` | 답하는 쪽이 말한 경로. (역, 호선) 목록이다. 비어 있으면 답이 없다 | `src/subway_route_agent/answerers.py:13` | #185 |
| `Answer.seconds` | 답하는 쪽이 말한 소요 시간(초). 말하지 않았으면 `None` | `src/subway_route_agent/answerers.py:14` | #185 |
| `Answer.tool_calls` | 질문 하나에 쓴 도구 호출 수. stub은 0 | `src/subway_route_agent/answerers.py:15` | #185 |
| `Answer.parse_error` | LLM 원문을 답 형식으로 읽지 못한 이유 한 줄. 읽었으면 `None`. 값이 있는 행을 리포트의 `파싱 실패`로 센다 | `src/subway_route_agent/answerers.py:16` | #186 |
| `Answer.tokens` | 질문 하나에 쓴 입력 + 출력 토큰. stub은 0 | `src/subway_route_agent/answerers.py:17` | #186 |
| `Answer.raw` | LLM이 돌려준 원문. `--raw`로 질문별로 파일에 쓴다 | `src/subway_route_agent/answerers.py:18` | #186 |
| `max_transfers` | 조건. 환승 횟수 상한. `None`이면 제한 없음 | `src/subway_route_agent/grade.py:103` | #185 |
| `depart` | 조건. 출발 시각(`HH:MM`). `arrive_by`와 같이 있을 때만 시한을 잰다. 둘 중 하나만 있으면 시한을 재지 않는다 | `src/subway_route_agent/grade.py:105` | #185 |
| `arrive_by` | 조건. 도착 시한(`HH:MM`). 출발 시각 + 실제 소요 시간이 이보다 늦으면 어긴 것. `depart`와 같이 있을 때만 잰다 | `src/subway_route_agent/grade.py:105` | #185 |
| `hand_path` | 질문 필드(선택). 직접 계산한 경로. 호선 구간 목록 `[{"line": 2, "stations": [...]}]`이다. 갈아타는 역은 앞 구간의 끝과 다음 구간의 처음에 둘 다 쓴다 | `data/questions.json:10` | #187 |
| `hand_seconds` | 질문 필드(선택). 직접 계산한 값(초). CSV 구간 소요시간 합 + 환승 한 번에 180초다. 테스트가 CSV 행만 더해 다시 계산해 `shortest()` 결과와 맞춰 본다 | `data/questions.json:13` | #187 |
| `hand_note` | 질문 필드. 계산 과정 한 줄. `hand_path`가 없는 질문에서는 정답이 없는 이유다 | `data/questions.json:14` | #187 |
| 역 검사 | 실행 전에 질문의 출발·도착역이 그래프에 있는지 본다(별칭은 바꾼 뒤). 하나라도 없으면 `질문 q5: 그래프에 없는 역 — 무슨역`을 stderr에 쓰고 exit 2. 리포트를 쓰지 않는다 | `src/subway_route_agent/cli.py:74` | #187 |
| 시한을 못 맞추면 정답 없음 | `depart`와 `arrive_by`가 둘 다 있고 최단 경로로도 출발 시각 + 소요 시간이 시한보다 늦으면 `truth_for`가 정답 없음(`None`)을 돌려준다 | `src/subway_route_agent/cli.py:34` | #187 |
| `직접 계산으로 확인한 정답` | 리포트 머리 줄 `K/M`. M = 정답이 있는 질문 수, K = 그중 `hand_seconds`가 있는 질문 수 | `src/subway_route_agent/report.py:68` | #187 |
| `출발역 다름` | 조건 어김. 답 경로의 첫 역이 질문의 출발역과 다르다 | `src/subway_route_agent/grade.py:97` | #185 |
| `도착역 다름` | 조건 어김. 답 경로의 끝 역이 질문의 도착역과 다르다 | `src/subway_route_agent/grade.py:99` | #185 |
| `경로 끊김` | 조건 어김. 채울 수 없을 때만 붙는다 — 답 경로에서 이웃하지 않은 두 노드를 `fill_path`가 못 이었다(같은 호선이 아니고 갈아타는 역을 한 번 쓴 것도 아니거나, 데이터에 없는 노드가 있다). 이웃하지 않아도 채워지면 안 붙는다 | `src/subway_route_agent/grade.py:101` | #185 |
| `환승 초과` | 조건 어김. 답 경로의 환승 횟수가 `max_transfers`보다 많다 | `src/subway_route_agent/grade.py:104` | #185 |
| `시한 초과` | 조건 어김. 출발 시각 + 실제 소요 시간이 `arrive_by`보다 늦다 | `src/subway_route_agent/grade.py:107` | #185 |
| 리포트 열 | `COLUMNS` 12개: 질문 · 정답 경로 · 정답 시간 · 답 있음 · 맞음 · 채운 역 · 지어낸 역 · 지어낸 소요 시간 · 조건 어김 · 도구 호출 · 응답 시간(ms) · 토큰 | `src/subway_route_agent/report.py:9` | #185, #186, #193 |
| `ANSWERERS` | 답하는 쪽 목록. `stub`·`llm`·`llm-tools` 셋. `llm`과 `llm-tools`는 첫 호출 때 client를 만든다 | `src/subway_route_agent/answerers.py:189` | #185, #186, #188 |
| `llm` | 답하는 쪽. LLM 혼자 — 질문 문장만 OpenAI에 보내고 JSON으로 경로와 소요 시간을 받는다. `--answerer llm`으로 고른다 | `src/subway_route_agent/answerers.py:89` | #186 |
| `SYSTEM` | LLM 혼자의 시스템 지시. 답 형식만 설명하고 역 목록·정답·질문별 힌트는 넣지 않는다 | `src/subway_route_agent/answerers.py:33` | #186 |
| `OPENAI_MODEL` | 환경변수. `llm`이 쓰는 모델 이름. 비면 `gpt-5.4-mini` | `src/subway_route_agent/answerers.py:30` | #186 |
| `find_station` | 도구. 역 이름 → 그래프 역 이름과 지나는 호선 목록. 없으면 이름에 그 글자가 든 역 후보 최대 10개. 별칭(`총신대입구` → `이수`)은 바꿔서 찾는다 | `src/subway_route_agent/tools.py:28` | #188 |
| `line_stations` | 도구. 호선 하나의 구간 목록 `[{from, to, seconds, one_way}]`. CSV 행 순서 그대로이고 지선은 갈라지는 역에서, 응암순환은 한 방향(`one_way`)으로 이어 준다 | `src/subway_route_agent/tools.py:37` | #188 |
| `travel_seconds` | 도구. 한 호선 안에서 갈아타지 않고 두 역 사이를 갈 때의 소요 시간(초). 경로와 여러 호선을 거치는 시간은 돌려주지 않고, 두 역이 그 호선에 없으면 오류를 돌려준다 | `src/subway_route_agent/tools.py:58` | #188 |
| `TOOL_CALL_LIMIT` | 질문 하나에 실행하는 도구 호출 상한(25). 닿으면 그 질문은 `parse_error="도구 호출 상한(25)에 닿았다"`로 끝나고 파싱 실패로 센다 | `src/subway_route_agent/answerers.py:112` | #188 |
| `TOOLS_SYSTEM` | LLM + 도구의 시스템 지시. `SYSTEM`에 도구 사용 안내와 환승 180초를 덧붙인 것이다. 역 목록·정답·질문별 힌트는 넣지 않는다 | `src/subway_route_agent/answerers.py:116` | #188 |
| `llm-tools` | 답하는 쪽 이름. LLM + 도구 — 도구를 함께 주고, 도구 호출이 없는 응답이 올 때까지 결과를 붙여 다시 부른다. `--answerer llm-tools`로 고른다 | `src/subway_route_agent/answerers.py:123` | #188 |
| `compare.md` | 비교 리포트. 답하는 쪽이 둘 이상일 때 `reports/compare.md`에 쓴다. 머리는 답하는 쪽마다 한 줄, 표는 질문마다 정답 시간과 `맞음`·`채운 역`·`답 경로 소요 시간`·`답이 말한 시간`. 머리 줄에 `채우지 않고도 맞은 질문 K/N`(맞음이고 채운 역 0)이 있다 | `src/subway_route_agent/report.py:105` | #188, #193 |
| `--answerer` 여러 값 | `--answerer stub llm llm-tools`처럼 여러 이름을 받는다. 같은 이름은 한 번만 돈다. `--out`은 하나면 그 리포트, 둘 이상이면 비교 리포트 경로이고 `--raw`는 둘 이상이면 `<파일명>-<이름>.json`이다 | `src/subway_route_agent/cli.py:59` | #188 |
| `fill_path` | 채점이 답 경로의 빠진 중간 역을 채운다. 붙은 두 노드가 이웃하면 그대로 두고, 같은 호선이면 그 호선 간선만으로 가장 짧은 길(순환선은 짧은 쪽), 호선이 다르고 뒤 역이 앞 호선에도 있으면 갈아타는 역을 한 번만 쓴 것으로 보고 `앞 → … → (뒤 역, 앞 호선) → (뒤 역, 뒤 호선)`으로 채운다. 못 채우면 `None` | `src/subway_route_agent/grade.py:53` | #193 |
| `Grade.filled` | 채점이 채운 역 수. 갈아타는 역을 앞 호선으로 한 번 더 쓴 노드도 1로 센다. 못 채웠거나 채울 게 없으면 0. 리포트의 `채운 역` 열이다 | `src/subway_route_agent/grade.py:16` | #193 |
| `채운 역` 열 | 리포트 열. 질문마다 `Grade.filled`. 비교 리포트에서는 답하는 쪽마다 `<이름> 채운 역` | `src/subway_route_agent/report.py:9` | #193 |
| `Answer.tool_log` | 질문 하나의 도구 호출 기록. 호출마다 `{name, arguments, output}`이고 `output`은 결과 앞 200자다. `--raw`의 `tool_log`로 파일에 쓴다 | `src/subway_route_agent/answerers.py:19` | #193 |
