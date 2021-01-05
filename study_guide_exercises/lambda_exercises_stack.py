from os import path

from aws_cdk import core
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as s3n


class LambdaExercisesStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        shoe_company_ingestion_bucket_name = 'devassoc-shoe-company-ingestion'
        shoe_company_ingestion_bucket = s3.Bucket(self, 'shoe-company-ingestion-bucket',
                                                  bucket_name=shoe_company_ingestion_bucket_name,
                                                  access_control=s3.BucketAccessControl.PRIVATE,
                                                  removal_policy=core.RemovalPolicy.DESTROY,
                                                  auto_delete_objects=True)
        core.CfnOutput(self, 'new-ingestion-bucket', value=shoe_company_ingestion_bucket.bucket_name)

        shoe_company_json_bucket_name = 'devassoc-shoe-company-json'
        shoe_company_json_bucket = s3.Bucket(self, 'shoe-company-json-bucket',
                                             bucket_name=shoe_company_json_bucket_name,
                                             access_control=s3.BucketAccessControl.PRIVATE,
                                             removal_policy=core.RemovalPolicy.DESTROY,
                                             auto_delete_objects=True)
        core.CfnOutput(self, 'new-json-bucket', value=shoe_company_json_bucket.bucket_name)

        lambda_role = iam.Role(self, 'lambda-role',
                               role_name='PayrollProcessingLambdaRole',
                               description='Provides lambda with access to s3 and cloudwatch to execute payroll processing',
                               assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'))
        lambda_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AWSLambdaExecute'))

        this_dir = path.dirname(__file__)
        conversion_function = lam.Function(self, 'conversion-function',
                                           function_name='PayrollProcessing',
                                           runtime=lam.Runtime.PYTHON_3_7,
                                           handler='conversion.lambda_handler',
                                           code=lam.Code.from_asset(path.join(this_dir, 'lambda')),
                                           role=lambda_role,
                                           description='Converts payroll csvs to json and puts results in s3 bucket',
                                           timeout=core.Duration.minutes(3),
                                           memory_size=128)
        conversion_function.add_permission('lambdas3permission',
                                           principal=iam.ServicePrincipal('s3.amazonaws.com'),
                                           action='lambda:InvokeFunction',
                                           source_arn=shoe_company_ingestion_bucket.bucket_arn,
                                           source_account=kwargs.get('env')['account'])
        shoe_company_ingestion_bucket.add_object_created_notification(s3n.LambdaDestination(conversion_function),
                                                                      s3.NotificationKeyFilter(suffix='.csv'))
