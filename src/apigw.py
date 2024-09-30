import os
import uuid
import zoneinfo
from dataclasses import dataclass
from typing import Any, Optional

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, CORSConfig
from aws_lambda_powertools.event_handler.api_gateway import Response
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent_function,
)
from aws_lambda_powertools.utilities.idempotency.serialization.pydantic import (
    PydanticSerializer,
)
from aws_lambda_powertools.utilities.parser import BaseModel
from aws_lambda_powertools.utilities.typing import LambdaContext

import location

persistence_layer = DynamoDBPersistenceLayer(
    table_name=os.environ.get("RTO_IDEMPOTENCY_TABLE_NAME", "rto-idempotency-table")
)
idempotency_config = IdempotencyConfig()

from models import BaseRecord, BaseRecordHolidays, MonthRecord
from tracker import (
    generate_tracker_base_entry,
    generate_tracker_month_entry,
    get_current_date,
)
from tracker import get_public_holidays as get_public_holidays_orig

tracker_table = boto3.resource("dynamodb").Table(
    os.environ.get("RTO_TABLE_NAME", "rto-table")
)

is_dev = os.environ.get("IS_DEV", None) is not None
extra_origins = ["http://localhost:3000"] if is_dev else None
cors_origin = os.environ.get("CORS_ORIGIN", "https://example.com")

# Initialise aws lambda powertools utils
cors_config = CORSConfig(
    allow_origin=cors_origin, extra_origins=extra_origins, max_age=300
)
app = APIGatewayRestResolver(cors=cors_config, enable_validation=True, debug=is_dev)
logger = Logger()


def create_new_month_entry(base_record: BaseRecord, timezone: str) -> MonthRecord:
    """Handles the creation of a new month entry

    Args:
        event (dict[str, Any]): The event
        context (Any): The context
    """

    dt = get_current_date(timezone)
    date_row = generate_tracker_month_entry(base_record.id, dt.year, dt.month)

    for day, holiday in base_record.holidays.items():
        if not day.startswith(f"{date_row.month}-"):
            continue
        if not holiday.is_global and base_record.county not in holiday.counties:
            continue
        date_row.holidays[day] = holiday.name

    return date_row


class NewUserPayload(BaseModel):
    timezone: Optional[str] = None


@idempotent_function(
    data_keyword_argument="ipaddr",
    config=idempotency_config,
    persistence_store=persistence_layer,
    output_serializer=PydanticSerializer,
)
def get_ip_location(ipaddr: str) -> location.IpApiResponse:
    return location.get_ip_location(ipaddr)


@dataclass
class PublicHolidaysArgs:
    country: str
    year: int


@idempotent_function(
    data_keyword_argument="kwargs",
    config=idempotency_config,
    persistence_store=persistence_layer,
)
def get_public_holidays(kwargs: PublicHolidaysArgs) -> dict[str, dict[str, Any]]:
    return get_public_holidays_orig(kwargs.country, kwargs.year)


@app.put("/dashboard")
def handle_new_user(
    dashboard: Optional[NewUserPayload] = NewUserPayload(),
) -> BaseRecord | dict[str, str]:
    """Handles the creation of a new user of the RTO System"""
    # TODO: Implement hCaptcha and Cloudflare turnstile support and reject invalid requests
    guid = str(uuid.uuid4())

    timezone = dashboard.timezone
    location = get_ip_location(
        ipaddr=app.current_event.request_context.identity.source_ip
    )

    if timezone is None:
        timezone = location.timezone

    if timezone not in zoneinfo.available_timezones():
        return Response(
            status_code=422,
            content_type="application/json",
            body={"error": "Invalid timezone"},
        )

    base_row = generate_tracker_base_entry(guid, timezone)
    base_row.county = f"{location.countryCode}-{location.region}"
    base_row.country = location.country
    base_row.office_ips = os.environ.get("OFFICE_IPS", "").split(",")

    dt = get_current_date(timezone)
    holidays = get_public_holidays(
        kwargs=PublicHolidaysArgs(country=base_row.country, year=dt.year)
    )

    base_row.holidays = {
        date: BaseRecordHolidays(**holiday) for date, holiday in holidays.items()
    }

    month_row = create_new_month_entry(base_row, timezone)
    tracker_table.put_item(Item=base_row.dict())
    tracker_table.put_item(Item=month_row.dict())

    return Response(status_code=200, content_type="application/json", body=base_row)


@app.get("/dashboard/<guid>")
def handle_get_user(guid: str) -> BaseRecord:
    """Handles the retrieval of the user's dashboard"""
    base_row = tracker_table.get_item(Key={"id": guid, "month": "_base"})
    if "Item" not in base_row:
        return Response(status_code=404, content_type="application/json")

    return Response(
        status_code=200,
        content_type="application/json",
        body=BaseRecord(**base_row["Item"]),
    )


@app.get("/dashboard/<guid>/<year>/<month>")
def handle_get_month(guid: str, year: str, month: str) -> MonthRecord:
    """Handles the retrieval of the user's dashboard"""
    month_row = tracker_table.get_item(
        Key={"id": guid, "month": f"{year}-{int(month):02d}"}
    )
    if "Item" not in month_row:
        return Response(status_code=404, content_type="application/json")

    return Response(
        status_code=200,
        content_type="application/json",
        body=MonthRecord(**month_row["Item"]),
    )


class StatsResponse(BaseModel):
    attendance: float


@app.get("/stats/<guid>/<year>/<month>")
def handle_calculate_stats(guid: str, year: str, month: str) -> StatsResponse:
    """Handles the calculation of the statistics for the specified month

    Args:
        event (dict[str, Any]): The event
        context (Any): The context
    """
    month_row = tracker_table.get_item(
        Key={"id": guid, "month": f"{year}-{int(month):02d}"}
    )
    if "Item" not in month_row:
        return Response(status_code=404, content_type="application/json")

    month_record = MonthRecord(**month_row["Item"])
    days = month_record.days
    attended = len(days) - list(days.values()).count(None)
    not_counted = len(days) - month_record.business_days + len(month_record.holidays)

    total_eligible_days = len(days) - not_counted

    return Response(
        status_code=200,
        content_type="application/json",
        body=StatsResponse(attendance=(attended / total_eligible_days) * 100),
    )


@app.post("/checkin/<guid>")
def post_ping(guid: str) -> MonthRecord:
    """Handles a PING sent from a client to the RTO system

    Args:
        guid (str): The GUID of the user
    """
    base_row = tracker_table.get_item(Key={"id": guid, "month": "_base"})
    if "Item" not in base_row:
        return Response(status_code=404, content_type="application/json")

    base_record = BaseRecord(**base_row["Item"])

    dt = get_current_date(base_record.timezone)
    month_row = tracker_table.get_item(
        Key={"id": guid, "month": f"{dt.year}-{dt.month:02d}"}
    )

    month_record: MonthRecord
    if "Item" not in month_row:
        month_record = create_new_month_entry(base_record, base_record.timezone)
    else:
        month_record = MonthRecord(**month_row["Item"])

    if month_record.days[str(dt.day)] is not None:
        return Response(status_code=202, content_type="application/json")

    user_ip = app.current_event.request_context.identity.source_ip
    if user_ip in base_record.office_ips:
        month_record.days[str(dt.day)] = user_ip

    tracker_table.put_item(Item=month_record.dict())
    return Response(status_code=200, content_type="application/json")


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
def handler(event: dict, context: LambdaContext):
    """Handles HTTP requests and sends it to the router"""
    idempotency_config.register_lambda_context(context)
    return app.resolve(event, context)
