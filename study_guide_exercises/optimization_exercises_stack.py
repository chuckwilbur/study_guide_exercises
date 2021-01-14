from aws_cdk import core
from aws_cdk import aws_iam as iam
from aws_cdk import aws_sns as sns
from aws_cdk import aws_ssm as ssm
from aws_cdk import aws_cloudwatch as cw
from aws_cdk import aws_cloudwatch_actions as cwa
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_config as config
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_events_targets as targets

from helpers.ami_map import ami_map
from helpers import instance_types as type


class OptimizationExercisesStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        high_cpu_topic = sns.Topic(self, 'high-cpu-topic',
                                   display_name='myHighCpuAlarm')
        # phone number format must be 12225558888 for US
        phone_param = ssm.StringParameter.from_string_parameter_name(self, 'phone-param',
                                                                     'notification-phone')
        high_cpu_topic_sub = sns.Subscription(self, 'high-cpu-topic-sub',
                                              topic=high_cpu_topic,
                                              protocol=sns.SubscriptionProtocol.SMS,
                                              endpoint=phone_param.string_value)

        default_vpc = ec2.Vpc.from_lookup(self, 'default-vpc', is_default=True)
        monitored_instance = ec2.Instance(self, 'monitored-instance',
                                          instance_name='devassoc-monitored',
                                          instance_type=type.R3_XLARGE,
                                          machine_image=ec2.MachineImage.generic_linux(
                                              ami_map=ami_map
                                          ),
                                          vpc=default_vpc)

        high_cpu_metric = cw.Metric(namespace='AWS/EC2',
                                    metric_name='CPUUtilization',
                                    dimensions={
                                        'InstanceId': monitored_instance.instance_id
                                    },
                                    statistic='Average',
                                    unit=cw.Unit.PERCENT,
                                    period=core.Duration.seconds(300))
        high_cpu_alarm = high_cpu_metric.create_alarm(self, 'high-cpu-alarm',
                                                      alarm_name='cpu-mon',
                                                      alarm_description='Alarm when CPU exceeds 70%',
                                                      comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
                                                      evaluation_periods=2,
                                                      period=core.Duration.seconds(300),
                                                      threshold=70,
                                                      actions_enabled=True)
        high_cpu_action = cwa.SnsAction(high_cpu_topic)
        high_cpu_alarm.add_alarm_action(high_cpu_action)

        ec2.CfnEIP(self, 'devassoc-elastic-ip')

        # not really a service role, but there are problems with that, per
        # https://github.com/aws/aws-cdk/issues/3492
        config_service_role = iam.Role(self, 'devassoc-config-service-role',
                                       assumed_by=iam.ServicePrincipal('config.amazonaws.com'),
                                       managed_policies=[
                                           iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSConfigRole')
                                       ])
        config_recorder = config.CfnConfigurationRecorder(self, 'devassoc-recorder',
                                                          name='ConfigRecorder',
                                                          role_arn=config_service_role.role_arn,
                                                          recording_group=config.CfnConfigurationRecorder.RecordingGroupProperty(
                                                              all_supported=True)
                                                          )
        config_bucket = s3.Bucket(self, 'config-bucket',
                                  bucket_name='devassoc-config',
                                  removal_policy=core.RemovalPolicy.DESTROY,
                                  auto_delete_objects=True)
        config_bucket.add_to_resource_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW,
                                                                 principals=[iam.ServicePrincipal('config.amazonaws.com')],
                                                                 resources=[config_bucket.bucket_arn],
                                                                 actions=['s3:GetBucketAcl']))
        config_bucket.add_to_resource_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW,
                                                                 principals=[iam.ServicePrincipal('config.amazonaws.com')],
                                                                 resources=[config_bucket.arn_for_objects(
                                                                     f"AWSLogs/{core.Stack.of(self).account}/Config/*")],
                                                                 actions=['s3:PutObject'],
                                                                 conditions={'StringEquals': {
                                                                     's3:x-amz-acl': 'bucket-owner-full-control'}}))
        eip_rule = config.ManagedRule(self, 'devassoc-managed-rule',
                                      identifier=config.ManagedRuleIdentifiers.EIP_ATTACHED,
                                      config_rule_name='devassoc-eip-rule')
        eip_rule.node.add_dependency(config_recorder)
        eip_compliance_topic = sns.Topic(self, 'eip-compliance-topic',
                                         display_name='EIP Compliance Topic')
        eip_compliance_topic_sub = sns.Subscription(self, 'eip-compliance-topic-sub',
                                                    topic=eip_compliance_topic,
                                                    protocol=sns.SubscriptionProtocol.SMS,
                                                    endpoint=phone_param.string_value)
        eip_rule.on_compliance_change('eip-compliance-change',
                                      target=targets.SnsTopic(eip_compliance_topic))
        config.CfnDeliveryChannel(self, 'devassoc-config-delivery',
                                  s3_bucket_name=config_bucket.bucket_name,
                                  sns_topic_arn=eip_compliance_topic.topic_arn)
