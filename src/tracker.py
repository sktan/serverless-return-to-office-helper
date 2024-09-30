import json
import urllib.request
import zoneinfo
from calendar import monthrange
from datetime import datetime
from typing import Any

from models import BaseRecord, MonthRecord

# Country and holidays functionality provided by the Nager.Date project
# https://github.com/nager/Nager.Date
available_countries = json.loads(
    urllib.request.urlopen("https://date.nager.at/api/v3/AvailableCountries").read()
)
country_codes: dict[str, str] = {
    country["name"]: country["countryCode"] for country in available_countries
}


def get_public_holidays(country: str, year: int) -> dict[str, dict[str, Any]]:
    """Gets the public holidays for the specified country and year

    Args:
        country (str): The country
        year (int): The year

    Returns:
        dict[str, str]: The public holidays
    """
    if country not in country_codes:
        raise ValueError(f"Invalid country: {country}")

    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_codes[country]}"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())

    holidays: dict[str, dict[str, Any]] = {
        holiday["date"]: {
            "name": holiday["localName"],
            "is_global": holiday["global"],
            "counties": holiday["counties"],
        }
        for holiday in data
    }
    return holidays


def get_current_date(timezone: str) -> datetime:
    """Gets the current date in the specified timezone

    Args:
        timezone (str): The timezone

    Returns:
        int: The current date
    """
    return datetime.now(zoneinfo.ZoneInfo(timezone))


def generate_tracker_base_entry(guid: str, timezone: str) -> BaseRecord:
    """Generates a tracker base row to insert into the database

    Returns:
        BaseRecord: The tracker base row
    """
    dt = get_current_date(timezone)

    data = BaseRecord(
        id=guid, timezone=timezone, created_at=f"{dt.year}-{dt.month:02d}-{dt.day:02d}"
    )
    return data


def generate_tracker_month_entry(guid: str, year: int, month: int) -> MonthRecord:
    """Generates a tracker month row to insert into the database

    Args:
        year (int): The year
        month (int): The month
    """
    days: int = monthrange(year, month)[1]
    data = MonthRecord(
        id=guid,
        month=f"{year}-{month:02d}",
        days={day: None for day in range(1, days + 1)},
    )

    for day in range(1, days + 1):
        dt = datetime(year, month, day)
        if dt.weekday() < 5:
            data.business_days += 1

    return data
