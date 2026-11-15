# 190 리뷰 — PR #7

**대상:** `main...HEAD` — 33 commits, 22 files, +1683 −216 (리뷰 fix 첫 리뷰 9개 + 재작업 리뷰 4개 포함)
**plan:** docs/plans/190-1114-plan-tool-granularity.md

리뷰는 `pr-review-toolkit:review-pr`의 코드·테스트·주석·조용한 실패 네 관점으로 두 번 했다. 1~30행은 첫 리뷰(Task 1~4), 31~49행은 반려 뒤 재작업 리뷰(Task 5~9, `b8014ff...HEAD`)다. 타입 관점은 새 타입이 없어 건너뛰었다.
단어장 검사: `docs/concepts.md` 용어 절의 「쓰지 말 말」을 diff의 코드·주석·docstring·문서에서 찾았다. 3곳이 나왔고 아래 12~14행에서 고쳤다.

## 지적

| # | 심각도 | 위치 | 내용 | 처리 |
| --- | --- | --- | --- | --- |
| 1 | Important | `src/subway_route_agent/report.py:216` | `--repeat` 2 이상인 비교 리포트 머리에 답하는 쪽별 모델 이름 줄이 없다. 커밋한 `reports/compare.md`에서 「모델」이 안 나온다 | fix `7f7ed0f` |
| 2 | Important | `src/subway_route_agent/tools.py:1` | 모듈 설명이 「소요 시간은 계산해 주지 않는다」인데 `route_seconds`가 경로 시간을 잰다 | fix `5f5b956` |
| 3 | Important | `docs/concepts.md:52` | 개념 표가 `직접 계산으로 확인한 정답` 줄을 `report.py:85`로 적었으나 지금은 86이다 | fix `ae83599` |
| 4 | Important | `docs/concepts.md:75` | `compare.md` 행이 「크게 묶은 도구는 역 목록을 볼 수 없다」 줄을 두 구성이 다 있을 때만 나온다고 적었다. 코드는 `llm-tools-coarse`만 있어도 쓴다 | fix `d929508` |
| 5 | Important | `tests/test_llm_tools.py:195` | `assert callable(ans)`는 항상 참이라, 등록된 `llm-tools-coarse`가 `COARSE_TOOLS`·`COARSE_SYSTEM`으로 만들어지는지 아무것도 확인하지 않는다 | fix `405a383` |
| 6 | Important | `tests/test_cli.py:609` | `assert "모델" in text`는 리포트 어디든 「모델」이 있으면 통과한다 | fix `ad2d591` |
| 7 | Important | `src/subway_route_agent/cli.py:130` | 답하는 쪽이 하나이고 `--repeat N`이면 마지막 회차 하나만 리포트에 남고 나머지 회차와 범위 행이 없다 | push-back — plan Task 3이 「답하는 쪽 하나 리포트(`render`)는 마지막 회차로 쓴다」로 정했고, 리포트 머리에 「N회 중 마지막 회차 결과다」를 적었다(`999f25a`). 회차를 다 보려면 답하는 쪽을 둘 이상 주거나 `--raw`를 쓴다 |
| 8 | Important | `src/subway_route_agent/cli.py:109` | API 오류가 k회차에서 나면 끝낸 1~k-1회차가 리포트로 안 남는다. `--raw` 없이 돌렸으면 유료 호출 결과가 사라진다 | defer — 오류 때 리포트를 안 쓰는 것은 #189 때부터의 동작이고 이번 plan 범위가 아니다. 회차별 중간 저장은 후속 티켓에서 정한다. 지금은 `--raw`를 주면 끝낸 회차는 파일에 남는다 |
| 9 | Important | `src/subway_route_agent/cli.py:111` | API 오류 때 쓴 부분 raw 파일이 끝난 회차 파일과 이름·모양이 같아 구별이 안 된다 | push-back — 같은 실행의 stderr에 `API 오류(<이름> <질문 id>, <회차>회차)`가 찍혀 어느 질문에서 끊겼는지 나온다. 파일에 표시를 넣는 것은 raw 형식을 바꾸는 일이라 이번 범위 밖이다 |
| 10 | Important | `reports/llm-tools.md:3` | 커밋한 `reports/llm-tools.md`·`reports/llm-tools-coarse.md`에는 「3회 중 마지막 회차 결과다」 줄이, `reports/compare.md`에는 모델 줄(1행)이 없다. 둘 다 그 줄을 더하기 전 코드로 돌린 파일이다 | defer — 실제 키로 다시 돌려야 하는 유료 측정이라 리뷰 세션이 못 한다. 숫자는 그대로이고 빠진 것은 머리 줄뿐이다. PR 본문 Notes가 이미 알린다. 다음에 리포트를 다시 돌릴 때 같이 바뀐다 |
| 11 | Suggestion | `src/subway_route_agent/tools.py:188` | `route_seconds` 설명이 「중간 역은 빼도 된다」고 하는데 갈아타는 역은 빼면 `fill_path`가 못 잇는다(예: 강남 2호선 → 고속터미널 3호선) | defer — 이 설명으로 3회·5회 측정을 했다. 바꾸면 커밋한 리포트와 코드가 어긋난다. 설명을 고쳐 다시 재는 것은 후속 티켓에서 한다 |
| 12 | Suggestion | `tests/test_tools.py:178` | docstring에 단어장이 쓰지 말라는 「기대값」이 있다 | fix `6abc0ea` |
| 13 | Suggestion | `docs/plans/190-1114-plan-tool-granularity.md:93` | plan에 「기대값」이 있다 | fix `456c73c` |
| 14 | Suggestion | `docs/plans/190-1114-plan-tool-granularity.md:96` | plan의 「형식 오류」는 단어장에서 파싱 실패의 쓰지 말 말이다. 여기서는 도구 인자 오류다 | fix `86a31cf` |
| 15 | Suggestion | `src/subway_route_agent/tools.py:116` | 같은 역·호선이 연달아 나오면(별칭을 거쳐 같아지는 경우 포함) 「1번째와 2번째를 이을 수 없다」가 나온다 | 기록만 |
| 16 | Suggestion | `src/subway_route_agent/tools.py:119` | 마지막 `fill_path`·`seconds is None` 분기는 앞의 쌍별 검사를 지나면 닿지 않아 보이고 테스트도 없다 | 기록만 |
| 17 | Suggestion | `src/subway_route_agent/tools.py:99` | 역 하나짜리 경로가 오류 없이 `{"seconds": 0, "transfers": 0}`을 돌려준다 | 기록만 |
| 18 | Suggestion | `src/subway_route_agent/report.py:189` | `COMPARE_DIFF` 줄은 `llm`과 비교하는 문장인데 `llm`이 없는 실행에도 나온다 | 기록만 |
| 19 | Suggestion | `src/subway_route_agent/cli.py:47` | 이전 실행의 raw 파일(더 많은 회차, 회차 없는 이름)이 덮어써지지 않고 남는다 | 기록만 |
| 20 | Suggestion | `src/subway_route_agent/cli.py:108` | `openai.APIError` 말고 다른 예외가 나면 raw 파일도 리포트도 안 남는다 | 기록만 |
| 21 | Suggestion | `src/subway_route_agent/report.py:134` | 도구가 돌려준 오류 수를 어디서도 안 센다. 잘못된 호출만 반복한 질문과 많이 쓴 질문이 리포트에서 같아 보인다 | 기록만 |
| 22 | Suggestion | `src/subway_route_agent/cli.py:50` | `_raw_path` 설명이 이름을 「둘 이상일 때」만 붙인다고 적었으나 `--repeat` 2 이상이면 하나여도 붙는다 | 기록만 |
| 23 | Suggestion | `src/subway_route_agent/answerers.py:195` | 「llm은 첫 호출 때 client를 만든다」 주석이 `llm-tools`·`llm-tools-coarse`도 그렇다는 말을 빼놓았다 | 기록만 |
| 24 | Suggestion | `tests/test_tools.py:203` | 모든 환승 간선 테스트가 그래프를 그 그래프와 비교하고 반복이 0번이어도 통과한다. CSV와 직접 비교는 세 경우뿐이다 | 기록만 |
| 25 | Suggestion | `tests/test_tools.py:200` | `transfer_seconds("서울역", 1, 8)`은 서울역에 8호선이 없어서 실패한다. 「두 호선 다 있는데 환승이 없는」 경우는 시험하지 않는다 | 기록만 |
| 26 | Suggestion | `tests/test_cli.py:517` | CLI 범위 테스트는 두 회차 값이 같아 「최저=최고」만 본다. 세 회차 중 가운데 회차가 극값인 경우가 없다 | 기록만 |
| 27 | Suggestion | `tests/test_cli.py:627` | 2회차 API 오류 테스트가 1회차 raw 파일이 있는지만 보고 질문 10개가 들었는지는 안 본다 | 기록만 |
| 28 | Suggestion | `tests/test_llm_tools.py:184` | 두 지시문 차이 테스트는 도구 안내 문장이 어느 위치에 있는지는 고정하지 않는다 | 기록만 |
| 29 | Suggestion | `tests/test_cli.py:195` | 테스트가 네트워크를 안 부르는 것은 `OPENAI_API_KEY` 삭제나 등록 교체에 기대고 있다. conftest로 막은 것은 아니다 | 기록만 |
| 30 | Suggestion | `tests/test_cli.py:517` | `--repeat` 2 이상 머리 줄(「같은 질문 N개를 … 번 돌렸다」)과, 그때 답하는 쪽별 요약 줄이 없다는 것을 확인하는 assert가 없다 | 기록만 |
| 31 | Important | `src/subway_route_agent/report.py:190` | 두 구성의 회차별 값이 전부 같으면 `d`=0, `e`=0이라 `0 ≥ 0`이 참이 되어 차이가 없는데 `\|d\| ≥ e: 예`가 찍힌다 | fix `106bfa3` |
| 32 | Important | `src/subway_route_agent/tools.py:106` | 같은 호선 오류 문구가 「이 방향으로 이어지지 않는다」인데, 실제 데이터에서 이 문구에 닿는 입력은 같은 역을 연달아 두 번 쓴 경우뿐이다. 원인이 중복인데 방향 문제로 안내한다 | fix `62fe83b` |
| 33 | Important | `src/subway_route_agent/report.py:228` | `no_route`로 맞힌 답은 `filled == 0`이라 머리 줄의 「채우지 않고도 맞은 질문」에 들어가 그 숫자가 q6·q7만큼 부푼다 | fix `681beb6` |
| 34 | Important | `tests/test_cli.py:381` | 평균 차이 줄 테스트가 정답률 줄만 값을 확인한다. 도구 호출·응답 시간·토큰은 회차마다 값이 같아 `DIFF_METRICS` 열 번호가 틀려도 통과한다 | fix `7e7ed81` |
| 35 | Important | `src/subway_route_agent/tools.py:204` | `route_seconds` 설명이 「같은 호선 안의 중간 역만 뺄 수 있다」인데 `fill_path`는 갈아타는 역을 한 번만 써도 채운다(강남 2호선 → 교대 3호선은 오류 없이 153초). 설명이 실제보다 엄격하다 | defer — 재측정 5회·10회가 이 설명으로 돌았다. 바꾸면 커밋한 리포트와 코드가 어긋난다. 설명을 고쳐 다시 재는 것은 후속 티켓에서 한다. 채점과 도구가 같은 `fill_path` 규칙이라 서로 어긋나지는 않는다 |
| 36 | Important | `src/subway_route_agent/report.py:120` | 답이 `no_route`였는지 세는 지표 열이 없다. 5회 비교 리포트에서는 `no_route`를 잘못 낸 답이 「답 있음 O, 맞음 X」로만 보이고, 모든 질문에 `no_route`를 찍는 답하는 쪽도 q6·q7 두 개를 맞혀 2/10이 나오지만 찍은 횟수는 어디에도 안 나온다 | defer — 회차별 지표 표의 열은 plan이 정했고 이번 재작업이 더한 범위가 아니다. 재측정 결과의 `no_route` 횟수는 PR 본문이 `raw`에서 직접 세어 적었다. 열로 넣는 것은 후속 티켓에서 정한다 |
| 37 | Suggestion | `README.md:19` | #190 행 결과 칸의 「정답률 범위 2/10~3/10과 2/10~5/10」·토큰 합이 반려 시점 값이라 지금 `reports/compare.md`(3/10~5/10과 2/10~4/10)와 다르다. `docs/decisions.md:14`도 같다 | 기록만 — 두 파일의 #190 행은 plan이 PR 게이트에서 main이 쓴다고 정했다 |
| 38 | Suggestion | `tests/test_cli.py:381` | 테스트 이름의 `from_rejected_values`가 무슨 뜻인지 코드에서 안 보인다. 반려된 PR 값이라는 뜻이다 | 기록만 |
| 39 | Suggestion | `docs/concepts.md` 평균 차이 줄 행 | 「구간 판정은 정답률 줄로 한다」의 「구간」이 이 repo 코드에 정의가 없고(plan의 통과·다시 잰다·미완), 인용 줄 173은 `DIFF_METRICS`이고 줄을 만드는 `_diff_lines`는 176이다 | 기록만 |
| 40 | Suggestion | `src/subway_route_agent/report.py:182` | 「표준편차」에 단어장 `실행 간 범위`의 쓰지 말 말 「편차」가 들어 있다. 새 표시 문구 `길 없음`은 단어장에 없다 | 기록만 — 표준편차는 통계량 이름이라 범위와 다른 값이다 |
| 41 | Suggestion | `src/subway_route_agent/report.py:186` | 표준오차 2배는 정규 근사라 회차가 5개면 t 분포 기준(약 2.3~2.8배)보다 작게 잡혀 `예`가 필요 이상으로 자주 뜬다 | 기록만 — 측정 방법은 jw가 「측정 방법 바꾸기」로 골랐다 |
| 42 | Suggestion | `src/subway_route_agent/report.py:250` | 답하는 쪽이 둘이 아니면 평균 차이 줄이 이유 없이 빠진다 | 기록만 |
| 43 | Suggestion | `src/subway_route_agent/tools.py:52` | `line_stations`의 `current`가 마지막 지선에서 본선으로 돌아오지 않는다. CSV에서 지선 행 뒤에 본선 행이 오면 그 구간이 지선으로 들어간다. 지금은 2호선·5호선 모두 지선이 호선 끝이라 모든 호선에서 구간 집합이 바꾸기 전과 같다 | 기록만 |
| 44 | Suggestion | `src/subway_route_agent/grade.py:88` | `_parse` 밖에서 `Answer(no_route=True, path=[…])`를 직접 만들면 path를 무시하고 맞다고 채점한다 | 기록만 |
| 45 | Suggestion | `tests/test_tools.py:215` | 2호선 지선 테스트가 첫 구간과 `시청` 부재만 본다. 지선 구성원 전체는 확인하지 않는다 | 기록만 |
| 46 | Suggestion | `tests/test_llm.py:133` | `no_route: true`와 비어 있지 않은 path의 파싱 실패 케이스가 `make_llm`만 거친다. `make_llm_tools`는 정상 경우만 본다 | 기록만 |
| 47 | Suggestion | `tests/test_grade.py:83` | `no_route: true`이면서 `seconds`가 null이 아닌 답의 채점은 시험하지 않는다 | 기록만 |
| 48 | Suggestion | `tests/fixtures/` | 녹화 fixture는 예전 `line_stations` 출력(`segments`)과 `no_route` 없는 스키마로 녹화됐다. 재생은 녹화된 응답을 그대로 돌려주므로 통과하지만 지금 도구 출력을 보고 만든 응답은 아니다 | 기록만 — fixture 다시 녹화는 plan이 이번에 안 하는 것으로 정했다 |

## plan 대조

| plan 기준 | 코드가 만족하나 | 증거 |
| --- | --- | --- |
| 명령 하나(`uv run subway-eval --answerer llm-tools llm-tools-coarse --repeat 3`)로 두 도구 구성이 같은 질문 셋에 각각 세 번 답하고, 비교 리포트에 회차별 지표 표와 실행 간 범위가 나란히 나온다 | 예 | `reports/compare.md` 회차별 지표 표 6행 + 범위 행 2개 · `tests/test_cli.py::test_repeat_two_compare_has_per_round_metric_table_and_range_rows` |
| 지표 일곱 개: 정답률, 지어낸 역(합), 지어낸 소요 시간(질문 수), 질문당 도구 호출(평균), 질문당 응답 시간(평균 초), 파싱 실패, 토큰 | 예 | `src/subway_route_agent/report.py:119` `METRIC_COLUMNS`(여덟째 열은 상한에 닿은 질문) · `reports/compare.md` 표에 빈칸 0 | <!-- style-exempt -->
| 크게 묶은 도구(`route_seconds`)는 경로를 돌려주지 않는다. 출력 키가 테스트로 고정돼 있다 | 예 | `tests/test_tools.py` `COARSE_KEYS` · `runs/190/raw*-llm-tools-coarse-*.json`의 `tool_log`에서 직접 센 키: 3회 seconds 22·transfers 22·error 67·lines 24·candidates 10, 5회 seconds 33·transfers 33·error 115·lines 42·candidates 16 |
| 두 구성의 지시문은 도구 안내 한 문장만 다르다. 테스트로 고정한다 | 예 | `tests/test_llm_tools.py::test_two_systems_differ_only_in_the_tool_guide_sentence` |
| 테스트는 API와 네트워크를 부르지 않는다 | 예 | `env -u OPENAI_API_KEY uv run pytest -q` 188 passed. conftest로 막은 것은 아니다(29행) |
| 실패 징후 1 ① 두 구성 × 회차 × 지표 일곱 개에 빈칸 0 | 예 | `reports/compare.md` 표(3회), PR 본문 5회 표 |
| 실패 징후 1 ② 정답률 실행 간 범위가 겹치지 않는다 | 판정 불가 | 값만: 3회 `llm-tools` 2/10~3/10, `llm-tools-coarse` 2/10~4/10. 5회 2/10~3/10, 2/10~5/10. 구간 판정은 사람 몫 |
| 실패 징후 2 `route_seconds` 출력에 허용 키 밖의 키가 없다 | 예 | 위 키 집계. 3회·5회 모두 허용 5개 안 |
| 실패 징후 3 크게 묶은 쪽 질문당 도구 호출 평균이 회차마다 0.5 미만이 아니다 | 예 | 3회 2.8~3.1, 5회 2.2~3.7 (`reports/compare.md`, PR 본문) |
| 실패 징후 4 도구 호출 상한(25)에 닿은 질문 수를 적고, 한 회차 3개 이상이면 `tool_log`를 요약한다 | 예 | `runs/190/raw*`에서 직접 집계한 값: 3회 `llm-tools` 1회차 1개, 5회 0개. 한 회차 3개 이상 없음 | <!-- style-exempt -->
| 이번에 안 하는 것: 질문 셋·채점·정답 계산·`SYSTEM`·`SCHEMA`·`_parse`·fixture를 안 바꾼다 | 예 | `git diff main...HEAD -- src/subway_route_agent/grade.py src/subway_route_agent/route.py src/subway_route_agent/graph.py data/ tests/fixtures/` 0줄 · `answerers.py` diff에 `SYSTEM`·`SCHEMA`·`_parse` 변경 없음 |


### 재작업(Task 5~9) 기준

| plan 기준 | 코드가 만족하나 | 증거 |
| --- | --- | --- |
| Task 5: 도구 설명에 갈아타는 역 두 번 쓰기 안내, 「이을 수 없다」 오류에 두 역의 이름·호선과 이유, 출력 키는 `error` 하나 | 예 | `tests/test_tools.py::test_route_seconds_error_for_skipped_transfer_station_names_both_stations_and_lines` · 커밋 `180988b` |
| Task 6: `line_stations`가 `main`·`branches`로 나눠 준다. 5호선 마천은 `branches`에만 있고 `from_station`이 강동, 지선 없는 호선은 빈 목록, 구간 합계가 바꾸기 전과 같다 | 예 | 5호선 `main` 48구간·`branches` 7구간, 1~8호선 구간 집합이 `b8014ff` 구현과 같음을 리뷰 에이전트가 직접 대조 · 커밋 `86a4140` |
| Task 7: `no_route` 스키마·지시문·`_parse` 세 경우·`Answer`·채점·`길 없음` 칸, 녹화 재생이 그대로 통과 | 예 | `tests/test_llm.py`·`test_grade.py`·`test_cli.py` · `test_replay_recorded_tool_calls_end_to_end`·`test_regrade_188` 통과 · 커밋 `16731e4` |
| Task 8: 답하는 쪽이 둘이고 회차가 2 이상이면 지표마다 평균·표준편차·`d`·`e`·`\|d\| ≥ e`. 반려 전 값으로 `d`=−0.8, `e`≈1.26, 아니오 | 예 | `tests/test_cli.py::test_render_compare_mean_difference_and_double_standard_error_from_rejected_values` · 커밋 `fa86189`(`d`=0이면 아니오로 고침 `106bfa3`) |
| Task 9: 재측정 5회(다시 잰다면 10회), 개념 표 고침 | 예 | `reports/compare.md` 5회 리포트 · `runs/190b/raw*`(5회)·`raw10-*`(10회) · `docs/concepts.md` 줄 번호 인용 34곳을 리뷰 에이전트가 열어 확인 · 커밋 `fd78d89`·`f79b847` |
| 측정값(통과·다시 잰다·미완 구간): 5회 `\|d\| ≥ e`면 통과 | 판정 불가 | 값만: 5회 `d`=+1.00, `e`=1.10 · 10회 `d`=+1.30, `e`=1.06. 판정은 사람 몫 |
| 바꾸지 않을 것: `git diff b8014ff...HEAD -- data/ tests/fixtures/ src/subway_route_agent/route.py src/subway_route_agent/graph.py` 출력이 비었다 | 예 | 위 명령 출력 0줄 |
| Pre-PR: 테스트·ruff | 예 | `env -u OPENAI_API_KEY uv run pytest -q` 211 passed, `uv run ruff check .` 통과 |

## 맨 아래

- 테스트: `env -u OPENAI_API_KEY uv run pytest -q` 211 passed, `uv run ruff check .` 통과(재작업 리뷰 fix 뒤). 첫 리뷰 뒤에는 188이었다
- 단어장 검사: `docs/concepts.md` 용어 절이 있어 두 번 실행했다. 재작업 diff에서는 40행(「표준편차」)만 걸렸고 통계량 이름이라 기록만으로 뒀다. 「손 계산」은 새 줄에 없다
- 첫 `plan 대조` 표의 「이번에 안 하는 것」 행은 첫 리뷰 시점 값이다. 재작업 Task 7이 `grade.py`·`answerers.py`의 `SYSTEM`·`SCHEMA`·`_parse`를 plan 범위만큼 바꿨다
- 인라인 스레드 게시: 5건 중 1건(7행, `src/subway_route_agent/cli.py:130`)이 그 줄이 diff에 없어 422로 실패해 같은 파일 125줄에 달았다. 나머지 4건은 8·9·10·11행 위치에 달렸다
