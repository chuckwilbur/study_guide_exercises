#!/usr/bin/env python3

from aws_cdk import core

from app_pipeline.apppipeline_stack import AppPipelineStack

app = core.App()
AppPipelineStack(app, "AppPipelineStack", False, env={
    'account': '441875730569',
    'region': 'us-east-2'
})

app.synth()
