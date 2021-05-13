from dataclasses import dataclass
from typing import List
import datetime
import enum
import io

class Classification(enum.Enum):
    UNCLASSIFIED = 'U'
    CLASSIFIED = 'C'
    SECRET = 'S'

@dataclass
class TLE:
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
        if len(lines) != 2:
            raise ValueError('2 lines expected')
        if len(lines[0]) != 69 or len(lines[1]) != 69:
            raise ValueError('invalid line length')
        if lines[0][0] != '1' or lines[1][0] != '2':
            raise ValueError('unexpected line sequence')
        if lines[0][2:7] != lines[1][2:7]:
            raise ValueError('catalog numbers do not match')
        if not _checksum(lines[0][:-1], int(lines[0][-1])):
            raise ValueError('line 1 failed checksum')
        if not _checksum(lines[1][:-1], int(lines[1][-1])):
            raise ValueError('line 2 failed checksum')
        return TLE(
            str(int(lines[0][2:7])) if lines[0][2].isdigit() else lines[0][2:7].strip(),
            Classification(lines[0][7]),
            lines[0][9:11],
            int(lines[0][11:14].strip() or 0),
            lines[0][14:17].strip(),
            _parse_epoch(lines[0][18:20], lines[0][20:32].strip()),
            float(lines[0][33:43]),
            float(f'{lines[0][44]}.{lines[0][45:50]}e{lines[0][50:52]}'),
            float(f'{lines[0][53]}.{lines[0][54:59]}e{lines[0][59:61]}'),
            int(lines[0][62]),
            int(lines[0][64:68]),
            float(lines[1][8:16]),
            float(lines[1][17:25]),
            float(f'.{lines[1][26:33]}'),
            float(lines[1][34:42]),
            float(lines[1][43:51]),
            float(lines[1][52:62]),
            int(lines[1][63:68]),
            int(lines[0][-1]),
            int(lines[1][-1])
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
        line1 = f.readline()
        line2 = f.readline()
        while line1 and line2:
            tles.append(TLE.fromlines([line1.strip(), line2.strip()]))
            line1 = f.readline()
            line2 = f.readline()

        return tles