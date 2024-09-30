import json

import aws_cdk as core
import aws_cdk.assertions as assertions
import pytest
from stacks.frontend_stack import FrontendStack

with open("cdk.json") as context_file:
    context = json.load(context_file)["context"]


@pytest.fixture(scope="function")
def template():
    app = core.App(context=context)
    stack = FrontendStack(
        app,
        "cdk",
        env=core.Environment(account="123456789012", region="ap-southeast-2"),
    )
    yield assertions.Template.from_stack(stack)


def describe_cloudfront_security_configuration():
    def test_deny_frame_options(template):
        template.has_resource_properties(
            "AWS::CloudFront::ResponseHeadersPolicy",
            {
                "ResponseHeadersPolicyConfig": {
                    "SecurityHeadersConfig": {
                        "FrameOptions": {"FrameOption": "DENY", "Override": True}
                    }
                }
            },
        )

    def test_enabled_xss_protection(template):
        template.has_resource_properties(
            "AWS::CloudFront::ResponseHeadersPolicy",
            {
                "ResponseHeadersPolicyConfig": {
                    "SecurityHeadersConfig": {
                        "XSSProtection": {
                            "ModeBlock": True,
                            "Protection": True,
                            "Override": True,
                        }
                    }
                }
            },
        )

    def test_enabled_strict_transport_security(template):
        template.has_resource_properties(
            "AWS::CloudFront::ResponseHeadersPolicy",
            {
                "ResponseHeadersPolicyConfig": {
                    "SecurityHeadersConfig": {
                        "StrictTransportSecurity": {
                            # This is configured for 1 year
                            "AccessControlMaxAgeSec": 31536000,
                            "Override": True,
                            "Preload": True,
                        }
                    }
                }
            },
        )


def describe_cloudfront_configuration():
    def test_valid_custom_error_responses(template):
        template.has_resource_properties(
            "AWS::CloudFront::Distribution",
            {
                "DistributionConfig": {
                    "CustomErrorResponses": [
                        {
                            "ErrorCode": 403,
                            "ResponseCode": 200,
                            "ResponsePagePath": "/index.html",
                        }
                    ]
                }
            },
        )

    def test_valid_default_root_object(template):
        template.has_resource_properties(
            "AWS::CloudFront::Distribution",
            {"DistributionConfig": {"DefaultRootObject": "index.html"}},
        )
