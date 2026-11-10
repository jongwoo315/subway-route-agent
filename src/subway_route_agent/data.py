import csv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "seoul_metro_1to8_240810.csv"


@dataclass(frozen=True)
class Row:
    line: int
    station: str
    seconds: int  # 바로 위 행의 역에서 이 역까지. 노선 첫 행은 0


def parse_mmss(s: str) -> int:
    m, sec = s.strip().split(":")
    return int(m) * 60 + int(sec)


def load_rows(path: Path = DATA) -> list[Row]:
    with open(path, encoding="utf-8", newline="") as f:
        return [
            Row(int(r["호선"]), r["역명"].strip(), parse_mmss(r["소요시간"]))
            for r in csv.DictReader(f)
        ]
