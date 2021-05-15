from dataclasses import dataclass
from typing import List, Optional
import datetime
import enum
import io

class Classification(enum.Enum):
    UNCLASSIFIED = 'U'
    CLASSIFIED = 'C'
    SECRET = 'S'

@dataclass
class TLE:
    name: Optional[str]
    satellite_catalog_num: str
    classification: Classification
    launch_year: str
    launch_number: int
    launch_piece: str
    epoch: datetime.datetime
    mean_motion_1st_derivative: float
    mean_motion_2nd_derivative: float
    bstar_drag_term: float
    ephemeris_type: int
    element_set_number: int
    inclination: float
    right_ascension: float
    eccentricity: float
    argument_of_perigree: float
    mean_anomaly: float
    mean_motion: float
    revolution_number: int
    checksum1: int
    checksum2: int

    @staticmethod
    def fromlines(lines: List[str]) -> 'TLE':
        if len(lines) < 2 or len(lines) > 3:
            raise ValueError('2 or 3 lines expected')

        (l0, l1, l2) = lines if len(lines) == 3 else [None, *lines]

        if len(l1) != 69 or len(l2) != 69:
            raise ValueError('invalid line length')
        if (l0 and l0[0] != '0') or l1[0] != '1' or l2[0] != '2':
            raise ValueError('unexpected line sequence')
        if l1[2:7] != l1[2:7]:
            raise ValueError('catalog numbers do not match')
        if not _checksum(l1[:-1], int(l1[-1])):
            raise ValueError('line 1 failed checksum')
        if not _checksum(l2[:-1], int(l2[-1])):
            raise ValueError('line 2 failed checksum')
        return TLE(
            l0[1:].strip() if l0 else None,
            str(int(l1[2:7])) if l1[2].isdigit() else l1[2:7].strip(),
            Classification(l1[7]),
            l1[9:11],
            int(l1[11:14].strip() or 0),
            l1[14:17].strip(),
            _parse_epoch(l1[18:20], l1[20:32].strip()),
            float(l1[33:43]),
            float(f'{l1[44]}.{l1[45:50]}e{l1[50:52]}'),
            float(f'{l1[53]}.{l1[54:59]}e{l1[59:61]}'),
            int(l1[62]),
            int(l1[64:68]),
            float(l2[8:16]),
            float(l2[17:25]),
            float(f'.{l2[26:33]}'),
            float(l2[34:42]),
            float(l2[43:51]),
            float(l2[52:62]),
            int(l2[63:68]),
            int(l1[-1]),
            int(l2[-1])
        )


def _parse_epoch(year: str, day: str) -> datetime.datetime:
    full_year = int(year)
    if full_year > 57:
        full_year += 1900
    else:
        full_year += 2000
    base_date = datetime.datetime(full_year, 1, 1)
    return base_date + datetime.timedelta(days=float(day))


def _checksum(value: str, checksum: int) -> bool:
    return (
        sum(int(x) for x in value if x.isdigit()) +
        sum(1 for x in value if x == '-')) % 10 == checksum


class TLEFile:
    def __init__(self, tles):
        self.tles = tles

    @staticmethod
    def fromfile(f: io.TextIOWrapper):
        tles = []
        current_lines = []
        while line := f.readline().strip():
            current_lines.append(line)
            if line.startswith('2'):
                tles.append(TLE.fromlines(current_lines))
                current_lines = []

        return tles