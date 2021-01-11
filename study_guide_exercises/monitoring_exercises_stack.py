from aws_cdk import core
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_cloudwatch as cw
from aws_cdk import aws_sns as sns
from aws_cdk import aws_secretsmanager as sm
from aws_cdk import aws_cloudwatch_actions as cwa
from aws_cdk import aws_cloudtrail as ct
from aws_cdk import aws_ssm as ssm


class MonitoringExercisesStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket_name = 'devassoc-monitored'
        bucket = s3.Bucket(self, 'bucket-monitored',
                           bucket_name=bucket_name,
                           removal_policy=core.RemovalPolicy.DESTROY,
                           auto_delete_objects=True)

        core.CfnOutput(self, 'monitored-bucket', value=bucket.bucket_name)

        size_metric = cw.Metric(namespace='AWS/S3',
                                metric_name='BucketSizeBytes',
                                dimensions={
                                    'BucketName': bucket.bucket_name,
                                    'StorageType': 'StandardStorage'
                                },
                                period=core.Duration.days(1))
        size_alarm = size_metric.create_alarm(self, 'bucket-alarm',
                                              alarm_name='S3 Storage Alarm',
                                              comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
                                              evaluation_periods=1,
                                              period=core.Duration.days(1),
                                              threshold=1000,
                                              actions_enabled=True)
        size_topic = sns.Topic(self, 'size-topic',
                               display_name='My S3 Alarm List')
        email_param = ssm.StringParameter.from_string_parameter_name(self, 'email-param',
                                                                     'notification-email')
        size_topic_sub = sns.Subscription(self, 'size-topic-sub',
                                          topic=size_topic,
                                          protocol=sns.SubscriptionProtocol.EMAIL,
                                          endpoint=email_param.string_value)
        size_action = cwa.SnsAction(size_topic)
        size_alarm.add_alarm_action(size_action)

        bucket_name = 'devassoc-s3-logs'
        log_bucket = s3.Bucket(self, 'bucket-s3-logs',
                               bucket_name=bucket_name,
                               removal_policy=core.RemovalPolicy.DESTROY,
                               auto_delete_objects=True)
        s3_trail = ct.Trail(self, 'bucket-trail',
                            bucket=log_bucket,
                            trail_name='s3_logs')
        s3_trail.add_s3_event_selector([ct.S3EventSelector(bucket=bucket)])
        s3_trail.log_all_s3_data_events()

        single_value_widget = cw.SingleValueWidget(metrics=[size_metric])
        graph_widget = cw.GraphWidget(left=[size_metric])
        cw.Dashboard(self, 'cloudwatch-dashboard',
                     dashboard_name='S3Dashboard',
                     widgets=[[single_value_widget, graph_widget]])
