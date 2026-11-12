# 189 리뷰 — PR #6

**대상:** `main...HEAD` — 10 commits(이 파일 커밋 전), 21 files, +785 −106
**plan:** docs/plans/189-1112-plan-transfer-time.md

## 지적

| # | 심각도 | 위치 | 내용 | 처리 |
| --- | --- | --- | --- | --- |
| 1 | Important | `tests/test_graph.py` (`graph.py` `build_graph`·`count_transfers`) | 환승 값을 「그 방향 → 반대 방향」 순서로 찾는 규칙이 테스트로 고정돼 있지 않다. 실제 CSV는 양방향이 같아 순서를 뒤집어도 148개가 전부 통과했다 | fix `abc83f0` |
| 2 | Important | `tests/test_cli.py:50` | `main()`이 `render_compare`에 `counts`를 넘기는 줄을 지워도 테스트가 통과한다. 비교 리포트 머리의 환승역 수 줄이 실제 그래프로 검증되지 않는다 | fix `4b8bb7f` |
| 3 | Important | `src/subway_route_agent/data.py:36` | CSV 헤더·노선 표기가 바뀌어 `load_transfers`가 `{}`를 돌려주면 에러 없이 환승이 전부 180초가 된다. 리포트에 「0개 · 180초 35개」가 찍힐 뿐 종료 코드는 0이다 | fix `0ecf117` |
| 4 | Important | `src/subway_route_agent/graph.py:88` | (라) `mismatch`는 `build_graph`와 `count_transfers`가 같은 별칭·같은 순서로 값을 찾아 실행 경로에서 늘 0이다. 이름 매칭이 틀어져도 (라)는 안 올라가고 (다)·안 쓰인 행 수만 변한다(`ALIASES`를 비우면 방향 76·안 쓰인 행 11, (다)·(라) 0). plan 통과 조건 「(라) 0」을 이름 매칭 근거로 읽으면 안 된다 | defer — 실제로 이름 매칭을 막는 것은 방향 78·안 쓰인 행 9를 고정한 `test_count_transfers_on_real_graph`와 (다) 0이다. 게이트에서 (라) 0을 근거로 읽지 않도록 여기 적는다. (라)를 독립 계산으로 바꾸는 것은 plan 실패 징후 정의를 바꾸는 일이라 이 PR 밖이다 |
| 5 | Important | `src/subway_route_agent/report.py:44` | `unused_rows`·`mismatch`가 리포트 머리에 안 나온다. 값이 다른 방향이 있는 환승역은 `data_stations`에도 `default_stations`에도 안 들어가 「N + M」이 전체 환승역 수와 안 맞을 수 있다. 지금 실제 그래프에서는 mismatch 0이라 잠복 상태다 | defer — plan Task 3이 머리 두 줄의 형식을 고정했고 안 쓰인 행 9개는 PR 본문에 적도록 되어 있다. mismatch가 생기는 데이터 갱신 때 머리 줄을 다시 정한다 |
| 6 | Suggestion | `src/subway_route_agent/graph.py:23`, `data.py:39` | 같은 키가 두 번 들어오면(별칭 합치기 포함) 뒤 값이 앞 값을 조용히 덮는다. 지금 데이터는 중복 키 0개 | 기록만 |
| 7 | Suggestion | `src/subway_route_agent/report.py:44` | `counts=None`이면 머리에서 「기다리는 시간은 0으로 본다」가 빠진다. `cli.main`은 늘 `counts`를 넘겨 실제 리포트에는 영향 없다 | 기록만 |
| 8 | Suggestion | `tests/test_cli.py:50` | 줄 끝 주석 「정답이 있는 8개 모두 직접 계산한 값이 있다」가 8/8 assert에서 떨어져 `고정한 stub` assert에 붙었다 | 기록만 |
| 9 | Suggestion | `tests/test_cli.py:83`, `tests/test_grade.py:16`, `tests/test_graph.py:81` 외 | 가짜 역(A·B·C) 그래프가 `transfers=None`으로 실제 CSV를 읽는다. 가짜 역이 실제 역 이름과 겹치면 180초 가정이 조용히 틀어진다 | 기록만 |
| 10 | Suggestion | `src/subway_route_agent/graph.py:66`, `report.py:44` | 주석 두 곳이 부정확하다: `unused_rows`에는 같은 호선 행(성수 2→2 등 3개)도 들어가는데 「그래프에 안 쓰인 행」이라고만 적었고, `transfer_head` docstring은 「환승역 수 한 줄」이라는데 그 줄에 방향 수·반대 방향 값도 담긴다 | 기록만 |
| 11 | Suggestion | `src/subway_route_agent/data.py:20` | `parse_mmss`·`int(r["호선"])`가 형식이 어긋난 행에서 행 번호·파일 이름 없는 `ValueError`를 낸다 | 기록만 |
| 12 | Suggestion | `tests/test_regrade_188.py` | 새 정답 아래 채점 결과를 고정하는 테스트가 없다. plan은 이 비교를 Task 4 측정 스크립트(커밋 안 함)로 뒀다 | 기록만 |
| 13 | Suggestion | `docs/concepts.md` 용어 절 | 단어장 검사: diff의 코드·주석·docstring·문서에서 「쓰지 말 말」 칸의 말을 찾았으나 없었다. plan의 규칙 문장(「손 계산」이라는 말을 쓰지 않는다) 한 곳만 규칙으로 인용돼 있다 | 기록만 |

## plan 대조

| plan 기준 | 코드가 만족하나 | 증거 |
| --- | --- | --- |
| 그래프의 갈아타는 간선이 환승역 데이터의 `환승소요시간`을 쓴다. 그 방향 값이 없으면 반대 방향 값, 둘 다 없을 때만 180초다 | 예 | `graph.py:47-49`, `tests/test_graph.py` 이수 4↔7 간선·까치산 2→5 간선·가짜 역 180초·방향 순서(`abc83f0`) |
| 리포트 머리에 「데이터 환승 시간을 쓴 환승역 수」와 「180초가 남은 환승역 수」가 나온다 | 예 | `report.py:44-58`, `tests/test_cli.py:46-49`(단일 리포트), 비교 리포트 줄 확인(`4b8bb7f`) |
| 정답이 있는 질문 8개 모두 `hand_seconds`가 다익스트라 정답과 같다. 직접 계산은 그래프 코드를 쓰지 않는다 | 예 | `tests/test_route.py` `_transfer_seconds`가 `csv` 모듈만 쓴다. `uv run pytest -q` 150 passed |
| 정답이 바뀐 질문을 PR 본문 표에 적는다 | 판정 불가 | PR 본문 표는 이 리뷰에서 대조하지 않았다. `data/questions.json` diff는 q2·q4·q5·q8·q9의 `hand_*` 칸 안에서만 바뀌었다 |
| LLM 점수를 두 가지로 다시 잰다(원문 다시 채점, 실제 키 두 번) | 판정 불가 | 이 리뷰에서 실행하지 않았다. 실제 키 측정은 구현 루프 몫이고 PR 본문·`reports/`에 있다 |
| 테스트는 API와 네트워크를 부르지 않는다 | 예 | `env -u OPENAI_API_KEY uv run pytest -q` → 150 passed, `uv run ruff check .` 통과 |
| 실패 징후 1 측정값 ①: 방향 78, (가) 77, (나) 1, (다) 0, (라) 0, 환승역 35/0 | 예 | `count_transfers`를 실제 그래프로 돌린 값이 같다. 단 (라)는 구조상 0이다(지적 4) |
| 실패 징후 2: 안 쓰인 1~8호선 행이 9개(지선 같은 호선 3 + 1호선 코레일 구간 6) | 예 | 성수 2→2, 신도림 2→1, 신도림 2→2, 창동 4→1, 신길 5→1, 강동 5→5, 도봉산 7→1, 가산디지털단지 7→1, 온수 7→1 |
| 바꾸지 않을 것: `grade.py`·`tools.py`·`tests/fixtures/` diff가 비었다 | 예 | `git diff main...HEAD -- src/subway_route_agent/grade.py src/subway_route_agent/tools.py tests/fixtures/` 0줄 |
| `data/seoul_metro_transfer_260831.csv` sha256 | 판정 불가 | 현재 값 `9c2c02e160d27a1203aa1b9570fdb5e958bc282dd2d8064d0c5969e6ddc310b6`. main이 넣은 파일과의 비교는 이 리뷰에서 못 했다 |

## 참고

- `TOOLS_SYSTEM`은 이제 「환승 시간은 역과 호선마다 다르다」고만 말하고, 환승 시간을 알려 주는 도구는 없다(Kickoff 결정 A, plan이 `tools.py`를 안 건드린다고 정함). 환승역 선택으로 정답이 갈리는 질문에서 LLM + 도구 쪽은 환승 시간을 알 수 없다. LLM 점수를 읽을 때 감안한다.
- 데이터 CSV에 거리와 시간이 어긋난 행이 하나 있다(김포공항 5호선→공항철도 122m인데 `04:42`, 122÷1.2 ≈ `01:42`). 1~8호선 밖 행이라 지금은 쓰이지 않는다.
- 리뷰 에이전트 세 개(코드·테스트·오류/주석)가 낸 지적을 합쳐 중복을 한 행으로 묶었다.
- 수정 뒤 `env -u OPENAI_API_KEY uv run pytest -q` 150 passed, `uv run ruff check .` 통과를 다시 확인했다.
