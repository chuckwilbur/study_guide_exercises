#!/usr/bin/env python3

from aws_cdk import core

from app_pipeline.apppipeline_stack import AppPipelineStack
from app_pipeline.webserver_stage import StackSwitches

app = core.App()
AppPipelineStack(app, "AppPipelineStack", StackSwitches.NoStack, env={
    'account': '441875730569',
    'region': 'us-east-2'
})

app.synth()
