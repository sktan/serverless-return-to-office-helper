from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as dynamodb  # Duration,; aws_sqs as sqs,
from aws_cdk import aws_ssm as ssm
from constructs import Construct


class DatabaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a DynamoDB table to track the RTO Statistics
        rto_table = dynamodb.Table(
            self,
            "rto_tracker_table",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="month", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            # Use AWS managed KMS key for encryption at rest
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True,
            deletion_protection=True,
        )

        # Store RTO App Parameter for later reference
        # This reduces the cross-stack dependency between the Backend and DB stack
        ssm.StringParameter(
            self,
            "rto_table_name",
            parameter_name="/sktanapps/rtoapp/dynamodb/rto_tracker_table",
            string_value=rto_table.table_name,
        )

        # Create a DynamoDB table to store any idompotency items
        rto_idempotency_table = dynamodb.Table(
            self,
            "rto_idempotency_table",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            # Use AWS managed KMS key for encryption at rest
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="expiration",
            point_in_time_recovery=True,
        )

        # Store RTO App Parameter for later reference
        ssm.StringParameter(
            self,
            "rto_idempotency_table_name",
            parameter_name="/sktanapps/rtoapp/dynamodb/rto_idempotency_table",
            string_value=rto_idempotency_table.table_name,
        )
