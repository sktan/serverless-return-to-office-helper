import datetime
import json
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import tracker


def describe_enerate_tracker_month_entry():
    def valid_businessdays():
        guid = str(uuid.uuid4())

        result = tracker.generate_tracker_month_entry(guid, 2024, 1)
        assert result.business_days == 23

    def valid_leapyears():
        guid = str(uuid.uuid4())

        leap = tracker.generate_tracker_month_entry(guid, 2024, 2)
        nonleap = tracker.generate_tracker_month_entry(guid, 2023, 2)
        assert len(leap.days.items()) == 29 and len(nonleap.days.items()) == 28

    def valid_month(monkeypatch):
        entry = tracker.generate_tracker_month_entry("guid", 2024, 5)
        assert entry.month == "2024-05"


def describe_generate_tracker_base_entry():
    def check_createdat(monkeypatch):
        def mock_get_current_date(timezone):
            return datetime.datetime(2024, 5, 1, tzinfo=ZoneInfo(timezone))

        monkeypatch.setattr(tracker, "get_current_date", mock_get_current_date)

        base = tracker.generate_tracker_base_entry("guid", "Australia/Sydney")
        assert base.created_at == "2024-05-01"


class MockUrlOpenResponseClass:
    data = None

    def __init__(self, data):
        self.data = data

    def read(self):
        return self.data


def describe_get_public_holidays():
    def valid_result_australia(monkeypatch):
        @contextmanager
        def mock_urlopen(url):
            yield MockUrlOpenResponseClass(
                json.dumps(
                    [
                        {
                            "date": "2024-01-01",
                            "localName": "New Year's Day",
                            "global": True,
                            "counties": None,
                        },
                        {
                            "date": "2024-12-25",
                            "localName": "Christmas Day",
                            "global": True,
                            "counties": None,
                        },
                    ]
                )
            )

        monkeypatch.setattr(tracker.urllib.request, "urlopen", mock_urlopen)

        holidays = tracker.get_public_holidays("Australia", 2024)
        assert holidays == {
            "2024-01-01": {
                "counties": None,
                "is_global": True,
                "name": "New Year's Day",
            },
            "2024-12-25": {
                "counties": None,
                "is_global": True,
                "name": "Christmas Day",
            },
        }

    def throws_exception(monkeypatch):
        with pytest.raises(ValueError) as excinfo:
            tracker.get_public_holidays("Narnia", 2024)

        assert str(excinfo.value) == "Invalid country: Narnia"
