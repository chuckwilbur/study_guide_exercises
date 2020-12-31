from aws_cdk import core

from study_guide_exercises_stack import StudyGuideExercisesStack
from rds_exercise_stack import RDSExerciseStack
from dynamodb_exercise_stack import DynamodbExerciseStack
from kms_key_exercise_stack import KMSKeyExerciseStack
from static_site_exercise_stack import StaticSiteExerciseStack


class WebServerStage(core.Stage):

    def __init__(self, scope: core.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        service = StudyGuideExercisesStack(self, 'WebServer', **kwargs)

        self.vpc_id = service.vpc_id
        self.public_subnet_id = service.public_subnet_id
        self.private_subnet_id = service.private_subnet_id

        RDSExerciseStack(self, 'RDS', **kwargs)

        DynamodbExerciseStack(self, 'DynamoDB', **kwargs)

        kms_key = KMSKeyExerciseStack(self, 'KMSKey', **kwargs)
        self.key_id = kms_key.key_id

        static_site = StaticSiteExerciseStack(self, 'S3Site', **kwargs)
        self.bucket_url = static_site.url
