from subway_route_agent.answerers import Answer
from subway_route_agent.cli import main
from subway_route_agent.data import Row
from subway_route_agent.grade import Grade
from subway_route_agent.graph import build_graph
from subway_route_agent.report import Result, format_path, format_seconds, render
from subway_route_agent.route import Route, shortest


def test_main_runs_end_to_end(tmp_path, capsys):
    out = tmp_path / "skeleton.md"
    assert main(["--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert capsys.readouterr().out.strip() == text.strip()
    rows = {line.split(" | ")[0].lstrip("| "): line.split(" | ") for line in text.splitlines()}
    for qid in ("q1", "q2", "q3"):
        assert qid in rows
        assert rows[qid][1] != "없음" and rows[qid][2] != "없음"  # 정답이 채워져 있다
    assert "0/3" in text
    assert rows["q1"][1] == "강남(2) → 홍대입구(2)" and rows["q1"][2] == "29분 0초"


def test_render_counts_correct_and_answered_rows():
    # stub만 돌리면 정답률이 늘 0/3이라 hits 계산이 고장 나도 안 걸린다
    route = Route([("A", 1), ("C", 1)], 660, 0)
    hit = Result("q1", route, Answer(path=route.nodes, seconds=660), Grade(True, True), 1.0)
    miss = Result("q2", route, Answer(), Grade(False, False), 1.0)
    text = render("t", "d.csv", [hit, miss])
    assert "정답률 1/2 (50%)" in text
    rows = {line.split(" | ")[0].lstrip("| "): line.split(" | ") for line in text.splitlines()}
    assert rows["q1"][3:5] == ["O", "O"] and rows["q2"][3:5] == ["X", "X"]


def test_unknown_answerer_is_rejected(tmp_path):
    import pytest

    with pytest.raises(SystemExit):
        main(["--answerer", "gpt", "--out", str(tmp_path / "x.md")])


def test_format_seconds():
    assert format_seconds(1740) == "29분 0초"
    assert format_seconds(65) == "1분 5초"
    assert format_seconds(None) == "없음"


def test_format_path_shows_endpoints_and_transfer_stations_only():
    rows = [
        Row(1, "A", 0), Row(1, "B", 60), Row(1, "C", 600),
        Row(2, "B", 0), Row(2, "C", 60),
    ]
    g = build_graph(rows)
    assert format_path(shortest(g, "A", "C", max_transfers=0)) == "A(1) → C(1)"
    assert format_path(shortest(g, "A", "C")) == "A(1) → B(1→2) → C(2)"
    assert format_path(None) == "없음"
