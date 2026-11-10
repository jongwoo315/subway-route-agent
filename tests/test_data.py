from subway_route_agent.data import load_rows, parse_mmss


def test_parse_mmss():
    assert parse_mmss("01:40") == 100
    assert parse_mmss("00:00") == 0


def test_load_rows_real_csv():
    rows = load_rows()
    assert len(rows) == 279
    assert {r.line for r in rows} == set(range(1, 9))
    assert rows[1].station == "시청" and rows[1].seconds == 120
