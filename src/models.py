from typing import Dict, List

from aws_lambda_powertools.utilities.parser import BaseModel


class BaseRecordHolidays(BaseModel):
    name: str
    is_global: bool
    counties: List[str] | None


class BaseRecord(BaseModel):
    id: str
    month: str = "_base"
    office_ips: List[str] = []
    rounding: str = "up"
    timezone: str
    percentage: int = 50
    holidays: Dict[str, BaseRecordHolidays] = {}
    created_at: str
    county: str = "AU-NSW"
    country: str = "Australia"


class MonthRecord(BaseModel):
    id: str
    month: str
    days: Dict[str, str | None]
    business_days: int = 0
    holidays: Dict[str, str | None] = {}
