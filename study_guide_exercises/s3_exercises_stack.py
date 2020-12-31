from aws_cdk import core
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy


class S3ExercisesStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket_name = 'devassoc-storage'
        bucket = s3.Bucket(self, 'bucket',
                           bucket_name=bucket_name)
        s3deploy.BucketDeployment(self, 'DeployFiles',
                                  destination_bucket=bucket,
                                  sources=[s3deploy.Source.asset('./study_guide_exercises/polly_file')])

        core.CfnOutput(self, 'new-bucket', value=bucket.bucket_name)

        encrypt_enforce_bucket_name = 'devassoc-encrypted-storage'
        encrypt_enforce_bucket = s3.Bucket(self, 'encrypt-enforced-bucket',
                                           bucket_name=encrypt_enforce_bucket_name)
        deny_incorrect_statement = {
            "Sid": "DenyIncorrectEncryption",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:PutObject",
            "Resource": f"{encrypt_enforce_bucket.bucket_arn}/*",
            "Condition": {
                "StringNotEquals": {
                    "s3:x-amz-server-side-encryption": "AES256"
                }
            }
        }
        encrypt_enforce_bucket.add_to_resource_policy(
            iam.PolicyStatement.from_json(deny_incorrect_statement)
        )
        deny_missing_statement = {
            "Sid": "DenyMissingEncryption",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:PutObject",
            "Resource": f"{encrypt_enforce_bucket.bucket_arn}/*",
            "Condition": {
                "Null": {
                    "s3:x-amz-server-side-encryption": True
                }
            }
        }
        encrypt_enforce_bucket.add_to_resource_policy(
            iam.PolicyStatement.from_json(deny_missing_statement)
        )

        core.CfnOutput(self, 'new-encrypt-enforce-bucket', value=encrypt_enforce_bucket.bucket_name)
