#!/usr/bin/env python3

from aws_cdk import core

from study_guide_exercises.study_guide_exercises_stack import StudyGuideExercisesStack
from study_guide_exercises.apppipeline_stack import AppPipelineStack

app = core.App()
AppPipelineStack(app, "AppPipelineStack", env={
    'account': '441875730569',
    'region': 'us-east-2'
})

app.synth()
