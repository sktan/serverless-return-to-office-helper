import datetime
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import boto3
import pytest
from moto import mock_aws

sys.path.insert(0, str(Path(__file__).parent.parent))
from tracker import generate_tracker_base_entry, generate_tracker_month_entry


@pytest.fixture
def lambda_context():
    @dataclass
    class LambdaContext:
        function_name: str = "apigw"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = (
            "arn:aws:lambda:ap-southeast-2:123456789012:function:apigw"
        )
        aws_request_id: str = "FB48BB8B-FD74-40D2-83F8-5E289249C4C0".lower()

        def get_remaining_time_in_millis(self) -> int:
            return 5

    return LambdaContext()


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.unsetenv("AWS_PROFILE")
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-southeast-2"


@pytest.fixture(scope="function")
def aws(aws_credentials):
    with mock_aws():
        yield boto3.client("dynamodb", region_name="ap-southeast-2")


@pytest.fixture(autouse=True)
def setup_dynamodb(aws):
    ddb_client = boto3.client("dynamodb", region_name="ap-southeast-2")
    ddb_client.create_table(
        TableName="rto-table",
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},
            {"AttributeName": "month", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
            {"AttributeName": "month", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    ddb_client.create_table(
        TableName="rto-idempotency-table",
        KeySchema=[
            {"AttributeName": "id", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "id", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    yield
    ddb_client.delete_table(TableName="rto-table")


@pytest.fixture(scope="function")
def setup_base_record(aws):
    rto_table = boto3.resource("dynamodb").Table("rto-table")

    base = generate_tracker_base_entry(
        "62FDC0E4-FB39-4820-A751-AA4D0080BB74", "Australia/Sydney"
    )
    base.office_ips.append("1.2.3.4")

    rto_table.put_item(Item=base.dict())
    yield


@pytest.fixture(scope="function")
def setup_month_record(aws, setup_base_record):
    rto_table = boto3.resource("dynamodb").Table("rto-table")
    rto_table.put_item(
        Item=generate_tracker_month_entry(
            "62FDC0E4-FB39-4820-A751-AA4D0080BB74", 2024, 5
        ).dict()
    )
    yield


def describe_post_ping():
    @mock_aws
    def returns_404_when_no_base_row(lambda_context):
        import apigw

        event = {
            "path": "/checkin/62FDC0E4-FB39-4820-A751-AA4D0080BB74",
            "httpMethod": "POST",
            "requestContext": {
                "identity": {"sourceIp": "1.2.3.4"},
                "requestId": "BF5A9727-2B7F-4A5F-A033-549C44588411",
            },
            "body": None,
        }
        response = apigw.handler(event, lambda_context)
        assert response["statusCode"] == 404

    @mock_aws
    def returns_200_when_base_exists(lambda_context, setup_base_record):
        import apigw

        event = {
            "path": "/checkin/62FDC0E4-FB39-4820-A751-AA4D0080BB74",
            "httpMethod": "POST",
            "requestContext": {
                "identity": {"sourceIp": "1.2.3.4"},
                "requestId": "BF5A9727-2B7F-4A5F-A033-549C44588411",
            },
        }
        response = apigw.handler(event, lambda_context)
        assert response["statusCode"] == 200

    @mock_aws
    def returns_200_when_month_exists(monkeypatch, lambda_context, setup_month_record):
        import apigw

        def mock_get_current_date(timezone):
            return datetime.datetime(2024, 5, 1, tzinfo=ZoneInfo(timezone))

        monkeypatch.setattr(apigw, "get_current_date", mock_get_current_date)

        event = {
            "path": "/checkin/62FDC0E4-FB39-4820-A751-AA4D0080BB74",
            "httpMethod": "POST",
            "requestContext": {
                "identity": {"sourceIp": "1.2.3.4"},
                "requestId": "BF5A9727-2B7F-4A5F-A033-549C44588411",
            },
        }
        response = apigw.handler(event, lambda_context)
        assert response["statusCode"] == 200

    @mock_aws
    def returns_200_when_month_not_exists(
        monkeypatch, lambda_context, setup_base_record
    ):
        import apigw

        def mock_get_current_date(timezone):
            return datetime.datetime(2024, 1, 1, tzinfo=ZoneInfo(timezone))

        monkeypatch.setattr(apigw, "get_current_date", mock_get_current_date)

        event = {
            "path": "/checkin/62FDC0E4-FB39-4820-A751-AA4D0080BB74",
            "httpMethod": "POST",
            "requestContext": {
                "identity": {"sourceIp": "1.2.3.4"},
                "requestId": "BF5A9727-2B7F-4A5F-A033-549C44588411",
            },
        }
        response = apigw.handler(event, lambda_context)
        assert response["statusCode"] == 200

    @mock_aws
    def returns_202_when_2024_05_05_already_pung(
        monkeypatch, lambda_context, setup_month_record
    ):
        import apigw

        def mock_get_current_date(timezone):
            return datetime.datetime(2024, 5, 5, tzinfo=ZoneInfo(timezone))

        monkeypatch.setattr(apigw, "get_current_date", mock_get_current_date)

        event = {
            "path": "/checkin/62FDC0E4-FB39-4820-A751-AA4D0080BB74",
            "httpMethod": "POST",
            "requestContext": {
                "identity": {"sourceIp": "1.2.3.4"},
                "requestId": "BF5A9727-2B7F-4A5F-A033-549C44588411",
            },
        }

        rto_table = boto3.resource("dynamodb").Table("rto-table")
        rto_table.update_item(
            Key={"id": "62FDC0E4-FB39-4820-A751-AA4D0080BB74", "month": "2024-05"},
            UpdateExpression="SET days.#day = :ip",
            ExpressionAttributeNames={
                "#day": "5",
            },
            ExpressionAttributeValues={":ip": "1.2.3.4"},
        )

        response = apigw.handler(event, lambda_context)
        assert response["statusCode"] == 202

    @mock_aws
    def day_updated_when_month_exists(monkeypatch, lambda_context, setup_month_record):
        import apigw

        def mock_get_current_date(timezone):
            return datetime.datetime(2024, 5, 5, tzinfo=ZoneInfo(timezone))

        monkeypatch.setattr(apigw, "get_current_date", mock_get_current_date)

        event = {
            "path": "/checkin/62FDC0E4-FB39-4820-A751-AA4D0080BB74",
            "httpMethod": "POST",
            "requestContext": {
                "identity": {"sourceIp": "1.2.3.4"},
                "requestId": "BF5A9727-2B7F-4A5F-A033-549C44588411",
            },
        }
        apigw.handler(event, lambda_context)

        rto_table = boto3.resource("dynamodb").Table("rto-table")
        month_record = rto_table.get_item(
            Key={"id": "62FDC0E4-FB39-4820-A751-AA4D0080BB74", "month": "2024-05"}
        )["Item"]
        assert month_record["days"]["5"] is not None

    @mock_aws
    def day_updated_when_month_not_exists(
        monkeypatch, lambda_context, setup_base_record
    ):
        import apigw

        def mock_get_current_date(timezone):
            return datetime.datetime(2024, 5, 5, tzinfo=ZoneInfo(timezone))

        monkeypatch.setattr(apigw, "get_current_date", mock_get_current_date)

        event = {
            "path": "/checkin/62FDC0E4-FB39-4820-A751-AA4D0080BB74",
            "httpMethod": "POST",
            "requestContext": {
                "identity": {"sourceIp": "1.2.3.4"},
                "requestId": "BF5A9727-2B7F-4A5F-A033-549C44588411",
            },
        }
        apigw.handler(event, lambda_context)

        rto_table = boto3.resource("dynamodb").Table("rto-table")
        month_record = rto_table.get_item(
            Key={"id": "62FDC0E4-FB39-4820-A751-AA4D0080BB74", "month": "2024-05"}
        )["Item"]
        assert month_record["days"]["5"] is not None


def describe_get_stats():
    def returns_404_when_no_month_row(lambda_context):
        import apigw

        event = {
            "path": "/stats/62FDC0E4-FB39-4820-A751-AA4D0080BB74/2024/01",
            "httpMethod": "GET",
            "requestContext": {"requestId": "BF5A9727-2B7F-4A5F-A033-549C44588411"},
        }
        response = apigw.handler(event, lambda_context)
        assert response["statusCode"] == 404

    def returns_200_when_month_row_exists(
        monkeypatch, lambda_context, setup_month_record
    ):
        import apigw

        event = {
            "path": "/stats/62FDC0E4-FB39-4820-A751-AA4D0080BB74/2024/05",
            "httpMethod": "GET",
            "requestContext": {"requestId": "BF5A9727-2B7F-4A5F-A033-549C44588411"},
        }
        response = apigw.handler(event, lambda_context)
        assert response["statusCode"] == 200

    def describe_attendance():
        def is_0_when_all_none(monkeypatch, lambda_context, setup_month_record):
            import apigw

            event = {
                "path": "/stats/62FDC0E4-FB39-4820-A751-AA4D0080BB74/2024/05",
                "httpMethod": "GET",
                "requestContext": {"requestId": "BF5A9727-2B7F-4A5F-A033-549C44588411"},
            }
            response = apigw.handler(event, lambda_context)
            assert response["body"] == '{"attendance":0.0}'

        def is_13_when_3days_in_2024_may(
            monkeypatch, lambda_context, setup_month_record
        ):
            import apigw

            event = {
                "path": "/stats/62FDC0E4-FB39-4820-A751-AA4D0080BB74/2024/05",
                "httpMethod": "GET",
                "requestContext": {"requestId": "BF5A9727-2B7F-4A5F-A033-549C44588411"},
            }

            rto_table = boto3.resource("dynamodb").Table("rto-table")
            rto_table.update_item(
                Key={"id": "62FDC0E4-FB39-4820-A751-AA4D0080BB74", "month": "2024-05"},
                UpdateExpression="SET days.#day1 = :ip, days.#day2 = :ip, days.#day3 = :ip",
                ExpressionAttributeNames={
                    "#day1": "1",
                    "#day2": "2",
                    "#day3": "3",
                },
                ExpressionAttributeValues={":ip": "1.2.3.4"},
            )

            response = apigw.handler(event, lambda_context)
            attendance = int(json.loads(response["body"])["attendance"])
            assert attendance == 13


def describe_put_dashboard():
    def returns_200_when_created_without_timezone(lambda_context):
        import apigw

        event = {
            "path": "/dashboard",
            "httpMethod": "PUT",
            "requestContext": {
                "identity": {"sourceIp": "1.2.3.4"},
                "requestId": "BF5A9727-2B7F-4A5F-A033-549C44588411",
            },
            "headers": {"Content-Type": "application/json"},
        }
        response = apigw.handler(event, lambda_context)
        assert response["statusCode"] == 200

    def returns_200_when_created(lambda_context):
        import apigw

        event = {
            "path": "/dashboard",
            "httpMethod": "PUT",
            "requestContext": {
                "identity": {"sourceIp": "1.2.3.4"},
                "requestId": "BF5A9727-2B7F-4A5F-A033-549C44588411",
            },
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"timezone": "Australia/Sydney"}),
        }
        response = apigw.handler(event, lambda_context)
        assert response["statusCode"] == 200

    @mock_aws
    def dashboard_get_table_after_created(monkeypatch, lambda_context):
        import apigw

        def mock_get_current_date(timezone):
            return datetime.datetime(2024, 5, 5, tzinfo=ZoneInfo(timezone))

        monkeypatch.setattr(apigw, "get_current_date", mock_get_current_date)

        event = {
            "path": "/dashboard",
            "httpMethod": "PUT",
            "requestContext": {
                "identity": {"sourceIp": "1.2.3.4"},
                "requestId": "BF5A9727-2B7F-4A5F-A033-549C44588411",
            },
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"timezone": "Australia/Sydney"}),
        }
        response = apigw.handler(event, lambda_context)
        body = json.loads(response["body"])

        rto_table = boto3.resource("dynamodb").Table("rto-table")
        base_record = rto_table.get_item(Key={"id": body["id"], "month": "_base"})
        month_record = rto_table.get_item(Key={"id": body["id"], "month": "2024-05"})

        assert "Item" in base_record and "Item" in month_record

    def returns_422_when_invalid_timezone(lambda_context):
        import apigw

        event = {
            "path": "/dashboard",
            "httpMethod": "PUT",
            "requestContext": {
                "identity": {"sourceIp": "1.2.3.4"},
                "requestId": "BF5A9727-2B7F-4A5F-A033-549C44588411",
            },
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"timezone": "Narnia/Cair Paravel"}),
        }
        response = apigw.handler(event, lambda_context)
        assert response["statusCode"] == 422
