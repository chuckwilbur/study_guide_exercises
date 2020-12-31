from aws_cdk import core
from aws_cdk import aws_dynamodb as dynamodb


class DynamodbExerciseStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        dynamodb_table_name = 'Users'
        user_id = dynamodb.Attribute(name='user_id', type=dynamodb.AttributeType.STRING)
        user_email = dynamodb.Attribute(name='user_email', type=dynamodb.AttributeType.STRING)
        dynamo_db = dynamodb.Table(self, 'dynamodb-table',
                                   table_name=dynamodb_table_name,
                                   partition_key=user_id,
                                   sort_key=user_email,
                                   read_capacity=5,
                                   write_capacity=5)
