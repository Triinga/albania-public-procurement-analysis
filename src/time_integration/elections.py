"""Election periods for the time analysis (2016-2025)."""
from datetime import datetime

# Election periods in the procurement data period (2016-2025)
# Format: {year: [(start_date, end_date), ...]}
ELECTIONS = {
    2017: [
        (datetime(2017, 6, 25), datetime(2017, 6, 25)),  # June 25, 2017
    ],
    2021: [
        (datetime(2021, 4, 25), datetime(2021, 4, 25)),  # April 25, 2021
    ],
    2023: [
        (datetime(2023, 5, 14), datetime(2023, 5, 14)),  # May 14, 2023
        (datetime(2023, 9, 24), datetime(2023, 9, 24)),  # September 24, 2023
    ],
    2024: [
        (datetime(2024, 8, 4), datetime(2024, 8, 4)),    # August 4, 2024
    ],
    2025: [
        (datetime(2025, 5, 11), datetime(2025, 5, 11)),  # May 11, 2025 (parliamentary)
        (datetime(2025, 11, 9), datetime(2025, 11, 9)),  # November 9, 2025 (local)
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
