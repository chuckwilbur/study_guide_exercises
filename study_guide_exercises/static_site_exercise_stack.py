from aws_cdk import core
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy


class StaticSiteExerciseStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        static_site_bucket_name = 'devassoc-static-site'
        static_site_bucket = s3.Bucket(self, 'static-site-bucket',
                                       bucket_name=static_site_bucket_name,
                                       website_index_document='index.html',
                                       website_error_document='error.html',
                                       removal_policy=core.RemovalPolicy.DESTROY,
                                       auto_delete_objects=True)
        public_read_statement = {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": [
                f"{static_site_bucket.bucket_arn}/*"
            ]
        }
        static_site_bucket.add_to_resource_policy(
            iam.PolicyStatement.from_json(public_read_statement)
        )
        s3deploy.BucketDeployment(self, 'DeployStaticSiteFiles',
                                  destination_bucket=static_site_bucket,
                                  sources=[s3deploy.Source.asset('./study_guide_exercises/site_files')])
        core.CfnOutput(self, 'new-static-site-bucket-url', value=static_site_bucket.bucket_website_url)
        core.CfnOutput(self, 'new-static-site-bucket', value=static_site_bucket.bucket_name)
        self.url = static_site_bucket.bucket_website_url
