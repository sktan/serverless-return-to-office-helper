from aws_cdk import BundlingOptions, Duration, Stack
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_ssm as ssm
from constructs import Construct

__BUNDLING_CMD__ = "pip install pipenv && pip install -r <(pipenv requirements) -t /asset-output && cp -au . /asset-output"


class BackendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        config = self.node.try_get_context("app_config")
        frontend_domain = config["frontend_domain"]
        backend_domain = config["backend_domain"]
        backend_acm = config["backend_acm"]

        rto_table = dynamodb.Table.from_table_name(
            self,
            id="rto_table",
            table_name=ssm.StringParameter.value_from_lookup(
                self,
                "/sktanapps/rtoapp/dynamodb/rto_tracker_table",
            ),
        )

        rto_idempotency_table = dynamodb.Table.from_table_name(
            self,
            id="rto_idempotency_table",
            table_name=ssm.StringParameter.value_from_lookup(
                self,
                "/sktanapps/rtoapp/dynamodb/rto_idempotency_table",
            ),
        )

        bundling_options = BundlingOptions(
            image=lambda_.Runtime.PYTHON_3_11.bundling_image,
            command=[
                "bash",
                "-xc",
                __BUNDLING_CMD__,
            ],
            user="root",
        )
        rto_backend_lambda = lambda_.Function(
            self,
            id="rto_backend_lambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(30),
            code=lambda_.Code.from_asset(
                "../src",
                bundling=bundling_options,
            ),
            handler="apigw.handler",
            layers=[
                lambda_.LayerVersion.from_layer_version_arn(
                    self,
                    id="lambda_powertools_layer",
                    layer_version_arn="arn:aws:lambda:ap-southeast-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:73",
                )
            ],
            environment={
                "IS_DEV": "true",
                "RTO_TABLE_NAME": rto_table.table_name,
                "RTO_IDEMPOTENCY_TABLE_NAME": rto_idempotency_table.table_name,
                "CORS_ORIGIN": f"https://{frontend_domain}",
                "OFFICE_IPS": ",".join(config["office_ips"]),
            },
        )
        rto_table.grant_read_write_data(rto_backend_lambda)
        rto_idempotency_table.grant_read_write_data(rto_backend_lambda)

        cors = apigw.CorsOptions(
            allow_origins=[f"https://{frontend_domain}", "http://localhost:3000"],
            allow_methods=["GET", "PUT", "POST", "DELETE"],
        )

        domain = backend_domain
        cert = acm.Certificate.from_certificate_arn(
            self,
            id="backend_cert",
            certificate_arn=backend_acm,
        )
        api = apigw.RestApi(
            self,
            id="rtoapp_backend_api",
            disable_execute_api_endpoint=True,
            domain_name=apigw.DomainNameOptions(
                certificate=cert,
                domain_name=domain,
                security_policy=apigw.SecurityPolicy.TLS_1_2,
            ),
            default_cors_preflight_options=cors,
            endpoint_types=[apigw.EndpointType.EDGE],
        )
        api.add_gateway_response(
            id="backend_api_clienterrors",
            type=apigw.ResponseType.DEFAULT_4_XX,
            response_headers={"Access-Control-Allow-Origin": "'*'"},
        )
        api.add_gateway_response(
            id="backend_api_unauthorized",
            type=apigw.ResponseType.DEFAULT_5_XX,
            response_headers={"Access-Control-Allow-Origin": "'*'"},
        )

        root_ep = api.root
        root_wildcard_ep = root_ep.add_resource("{proxy+}")
        root_wildcard_ep.add_method("GET", apigw.LambdaIntegration(rto_backend_lambda))
        root_wildcard_ep.add_method("POST", apigw.LambdaIntegration(rto_backend_lambda))
        root_wildcard_ep.add_method("PUT", apigw.LambdaIntegration(rto_backend_lambda))
