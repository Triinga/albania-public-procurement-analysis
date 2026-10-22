"""Election periods for the time analysis (2016-2025).

Nationwide elections in Albania (source: KQZ, https://kqz.gov.al). Partial
by-elections (e.g. Kukës mayor, 24.09.2023) are left out. The President is elected
by the Assembly, so there are no presidential elections by popular vote.
"""
from datetime import datetime

# Format: {year: [(start_date, end_date), ...]}
ELECTIONS = {
    # Before the data period, kept so early 2016 gets its true nearest election
    2015: [
        (datetime(2015, 6, 21), datetime(2015, 6, 21)),  # Local
    ],
    2017: [
        (datetime(2017, 6, 25), datetime(2017, 6, 25)),  # Parliamentary
    ],
    2019: [
        (datetime(2019, 6, 30), datetime(2019, 6, 30)),  # Local
    ],
    2021: [
        (datetime(2021, 4, 25), datetime(2021, 4, 25)),  # Parliamentary
    ],
    2023: [
        (datetime(2023, 5, 14), datetime(2023, 5, 14)),  # Local
    ],
    2025: [
        (datetime(2025, 5, 11), datetime(2025, 5, 11)),  # Parliamentary
    ],
}


def get_election_period(date):
    """Return election period (year, month) or None if no election in that month."""
    if not hasattr(date, 'year') or not hasattr(date, 'month'):
        return None

    year = date.year
    month = date.month

    if year not in ELECTIONS:
        return None

    for start, end in ELECTIONS[year]:
        if start.month <= month <= end.month:
            return (year, start.month)

    return None
