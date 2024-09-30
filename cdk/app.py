#!/usr/bin/env python3
import os

import aws_cdk as cdk
from stacks.backend_stack import BackendStack
from stacks.database_stack import DatabaseStack
from stacks.frontend_stack import FrontendStack

cdk_env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION"),
)

app = cdk.App()
datbase_stack = DatabaseStack(app, "rtoapp-database", env=cdk_env)
backend_stack = BackendStack(app, "rtoapp-backend", env=cdk_env)
frontend_stack = FrontendStack(app, "rtoapp-frontend", env=cdk_env)

app.synth()
