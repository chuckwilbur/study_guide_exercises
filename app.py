#!/usr/bin/env python3

from aws_cdk import core

from study_guide_exercises.study_guide_exercises_stack import StudyGuideExercisesStack


app = core.App()
StudyGuideExercisesStack(app, "study-guide-exercises")

app.synth()
