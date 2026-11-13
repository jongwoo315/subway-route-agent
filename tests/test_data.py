from subway_route_agent.data import load_rows, parse_mmss


def test_parse_mmss():
    assert parse_mmss("01:40") == 100
    assert parse_mmss("00:00") == 0


def test_load_rows_real_csv():
    rows = load_rows()
    assert len(rows) == 279
    assert {r.line for r in rows} == set(range(1, 9))
    assert rows[1].station == "시청" and rows[1].seconds == 120


def test_load_transfers_keeps_only_lines_1_to_8():
    import csv

    from subway_route_agent.data import TRANSFER_DATA, load_transfers

    t = load_transfers()
    with open(TRANSFER_DATA, encoding="utf-8", newline="") as f:
        raw = list(csv.DictReader(f))
    assert len(raw) == 145
    assert len(t) == 86  # 호선·환승노선이 둘 다 1~8호선인 행
    assert all(1 <= a <= 8 and 1 <= b <= 8 for _, a, b in t)  # 공항철도·9호선 행은 없다
    assert ("종합운동장", 2, 9) not in t
    # 값은 MM:SS를 초로 바꾼 것이다
    assert t[("까치산", 5, 2)] == 14  # 00:14
    assert t[("서울역", 1, 4)] == 133  # 02:13
    # 역 이름은 별칭을 바꾸지 않고 데이터 그대로다
    assert t[("총신대입구", 4, 7)] == 143 and t[("이수", 7, 4)] == 143


def test_load_transfers_raises_when_no_line_1_to_8_rows(tmp_path):
    import pytest

    from subway_route_agent.data import load_transfers

    f = tmp_path / "t.csv"
    f.write_text("호선,환승역명,환승노선,환승소요시간\n9,A,공항철도,01:00\n", encoding="utf-8")
    with pytest.raises(ValueError, match="1~8호선 환승 행이 없다"):
        load_transfers(f)
