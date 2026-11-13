import csv
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "seoul_metro_1to8_240810.csv"
TRANSFER_DATA = ROOT / "data" / "seoul_metro_transfer_260831.csv"


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


def load_transfers(path: Path = TRANSFER_DATA) -> dict[tuple[str, int, int], int]:
    """(역 이름, 앞 호선, 뒤 호선) → 환승 소요시간(초). 환승노선이 1~8호선인 행만 담는다."""
    out = {}
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            m = re.fullmatch(r"([1-8])호선", r["환승노선"].strip())
            if m:
                key = (r["환승역명"].strip(), int(r["호선"]), int(m[1]))
                out[key] = parse_mmss(r["환승소요시간"])
    if not out:  # 헤더·노선 표기가 바뀌면 전부 180초로 조용히 돌아가므로 여기서 멈춘다
        raise ValueError(f"{path.name}에 1~8호선 환승 행이 없다")
    return out
