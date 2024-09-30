from aws_cdk import BundlingOptions, Duration, Stack
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3_deployment
from constructs import Construct


class FrontendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        config = self.node.try_get_context("app_config")
        frontend_domain = config["frontend_domain"]
        backend_domain = config["backend_domain"]
        frontend_acm = config["frontend_acm"]

        # Some variables that we'll use later
        cert = acm.Certificate.from_certificate_arn(
            self,
            id="frontend_cert",
            certificate_arn=frontend_acm,
        )

        bucket = s3.Bucket(self, "frontend_bucket")
        cf_oai = cloudfront.OriginAccessIdentity(
            self,
            "frontend_originpolicy",
        )

        cf_headers = cloudfront.ResponseHeadersPolicy(
            self,
            id="frontend_headers",
            security_headers_behavior=cloudfront.ResponseSecurityHeadersBehavior(
                referrer_policy=cloudfront.ResponseHeadersReferrerPolicy(
                    override=True,
                    referrer_policy=cloudfront.HeadersReferrerPolicy.NO_REFERRER,
                ),
                xss_protection=cloudfront.ResponseHeadersXSSProtection(
                    override=True, mode_block=True, protection=True
                ),
                content_type_options=cloudfront.ResponseHeadersContentTypeOptions(
                    override=True,
                ),
                content_security_policy=cloudfront.ResponseHeadersContentSecurityPolicy(
                    override=True,
                    content_security_policy=" ".join(
                        [
                            "default-src 'self';",
                            "frame-ancestors 'none';",
                            f"connect-src https://{backend_domain}/;",
                            "img-src 'self' https://images.unsplash.com/ data:;",
                            "style-src 'self' 'unsafe-inline'",
                        ]
                    ),
                ),
                frame_options=cloudfront.ResponseHeadersFrameOptions(
                    override=True,
                    frame_option=cloudfront.HeadersFrameOption.DENY,
                ),
                strict_transport_security=cloudfront.ResponseHeadersStrictTransportSecurity(
                    override=True,
                    access_control_max_age=Duration.days(365),
                    preload=True,
                ),
            ),
        )
        cf_dist = cloudfront.Distribution(
            self,
            id="frontend_cloudfront",
            domain_names=[
                frontend_domain,
            ],
            default_root_object="index.html",
            price_class=cloudfront.PriceClass.PRICE_CLASS_ALL,
            certificate=cert,
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    bucket=bucket,
                    origin_access_identity=cf_oai,
                ),
                response_headers_policy=cf_headers,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            error_responses=[
                cloudfront.ErrorResponse(
                    # When an item wasn't found, it returns a 403 not 404.
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                )
            ],
        )

        # Deploy the frontend assets to S3 and invalidate the CloudFront Cache
        setup_command = "&&".join(
            [
                "export npm_config_update_notifier=false",
                "export npm_config_cache=$(mktemp -d)",
                "npm install",
            ]
        )
        build_command = "npm run build && cp -au dist/* /asset-output"
        complete_build_command = setup_command + "&&" + build_command
        s3_deployment.BucketDeployment(
            self,
            id="frontend_deploy",
            distribution=cf_dist,
            distribution_paths=["/*", "/"],
            sources=[
                # This is the directory where the frontend code lives
                # The bundling option will build the website frontend and use that
                # as the final source to deploy to S3
                s3_deployment.Source.asset(
                    "../frontend",
                    bundling=BundlingOptions(
                        # Using Node v14 as AWS doesn't support Node v16 yet
                        image=lambda_.Runtime.NODEJS_20_X.bundling_image,
                        command=[
                            "bash",
                            "-xc",
                            complete_build_command,
                        ],
                    ),
                )
            ],
            destination_bucket=bucket,
        )
