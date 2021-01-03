from aws_cdk import core

from web_server_exercises_stack import WebServerExercisesStack
from s3_exercises_stack import S3ExercisesStack
from rds_exercise_stack import RDSExerciseStack
from dynamodb_exercise_stack import DynamodbExerciseStack
from kms_key_exercise_stack import KMSKeyExerciseStack
from static_site_exercise_stack import StaticSiteExerciseStack
from auth_exercises_stack import AuthExercisesStack
from microservice_exercises_stack import MicroserviceExercisesStack


class StackSwitches:
    NoStack = 0
    S3ExercisesStack = 1 << 0
    DynamodbExerciseStack = 1 << 1
    KMSKeyExerciseStack = 1 << 2
    StaticSiteExerciseStack = 1 << 3
    AuthExercisesStack = 1 << 4
    MicroserviceExercisesStack = 1 << 5
    # 1 << 6
    # 1 << 7


class WebServerStage(core.Stage):

    def __init__(self, scope: core.Construct, construct_id: str, deploy_flags: int, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        service = WebServerExercisesStack(self, 'WebServer', **kwargs)

        self.vpc_id = service.vpc_id
        self.public_subnet_id = service.public_subnet_id
        self.private_subnet_id = service.private_subnet_id

        RDSExerciseStack(self, 'RDS', **kwargs)

        MicroserviceExercisesStack(self, 'Microservices', **kwargs)

        if deploy_flags & StackSwitches.S3ExercisesStack == StackSwitches.S3ExercisesStack:
            S3ExercisesStack(self, 'S3Buckets', **kwargs)

        if deploy_flags & StackSwitches.DynamodbExerciseStack == StackSwitches.DynamodbExerciseStack:
            DynamodbExerciseStack(self, 'DynamoDB', **kwargs)

        if deploy_flags & StackSwitches.KMSKeyExerciseStack == StackSwitches.KMSKeyExerciseStack:
            kms_key = KMSKeyExerciseStack(self, 'KMSKey', **kwargs)
            self.key_id = kms_key.key_id

        if deploy_flags & StackSwitches.StaticSiteExerciseStack == StackSwitches.StaticSiteExerciseStack:
            static_site = StaticSiteExerciseStack(self, 'S3Site', **kwargs)
            self.bucket_url = static_site.url

        if deploy_flags & StackSwitches.AuthExercisesStack == StackSwitches.AuthExercisesStack:
            auth_stack = AuthExercisesStack(self, 'Auth', **kwargs)
            self.auth_vpc_id = auth_stack.vpc_id
