import json

import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest
from stacks.backend_stack import BackendStack

with open("cdk.json") as context_file:
    context = json.load(context_file)["context"]


@pytest.fixture(scope="function")
def template():
    app = core.App(context=context)
    stack = BackendStack(
        app,
        "cdk",
        env=core.Environment(account="123456789012", region="ap-southeast-2"),
    )
    yield assertions.Template.from_stack(stack)


def describe_apigw_requirements():
    def test_apigw_disable_default_endpoint(template):
        template.has_resource_properties(
            "AWS::ApiGateway::RestApi",
            {
                "DisableExecuteApiEndpoint": True,
            },
        )

    def test_apigw_edge_endpoint(template):
        template.has_resource_properties(
            "AWS::ApiGateway::RestApi",
            {
                "EndpointConfiguration": {
                    "Types": ["EDGE"],
                },
            },
        )
