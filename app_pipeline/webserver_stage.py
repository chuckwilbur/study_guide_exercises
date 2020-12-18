from aws_cdk import core

from study_guide_exercises.study_guide_exercises_stack import StudyGuideExercisesStack


class WebServerStage(core.Stage):

    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        service = StudyGuideExercisesStack(self, 'WebServer', **kwargs)

        self.vpc_id = service.vpc_id
        self.public_subnet_id = service.public_subnet_id
        self.private_subnet_id = service.private_subnet_id