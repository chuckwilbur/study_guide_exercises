#!/usr/bin/env python3

from aws_cdk import core

from app_pipeline.apppipeline_stack import AppPipelineStack
from app_pipeline.webserver_stage import StackSwitches as ss

app = core.App()
deploy_flags = ss.NoStack
AppPipelineStack(app, "AppPipelineStack", deploy_flags, env={
    'account': '441875730569',
    'region': 'us-east-2'
})

app.synth()
