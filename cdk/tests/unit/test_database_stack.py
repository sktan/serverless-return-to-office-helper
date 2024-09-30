import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest
from stacks.database_stack import DatabaseStack


@pytest.fixture(scope="function")
def template():
    app = core.App()
    stack = DatabaseStack(app, "cdk")
    yield assertions.Template.from_stack(stack)


def describe_dynamodb_standards():
    def test_dynamodb_encryption(template):
        template.has_resource_properties(
            "AWS::DynamoDB::Table", {"SSESpecification": {"SSEEnabled": True}}
        )

    def test_dynamodb_pitr_enabled(template):
        template.has_resource_properties(
            "AWS::DynamoDB::Table",
            {
                "PointInTimeRecoverySpecification": {
                    "PointInTimeRecoveryEnabled": True
                },
            },
        )

    def test_dynamodb_deletion_protection(template):
        template.has_resource_properties(
            "AWS::DynamoDB::Table", {"DeletionProtectionEnabled": True}
        )
