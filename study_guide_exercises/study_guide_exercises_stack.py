from aws_cdk import core
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam


class StudyGuideExercisesStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        vpc = ec2.Vpc(self, 'devassoc',
                      max_azs=1,
                      nat_gateway_provider=ec2.NatProvider.instance(
                          instance_type=ec2.InstanceType.of(
                              instance_class=ec2.InstanceClass.BURSTABLE2,
                              instance_size=ec2.InstanceSize.NANO
                          ),
                          key_name='devassoc'
                      ))
        core.Tags.of(vpc).add('Name', 'devassoc')

        self.vpc_id = vpc.vpc_id
        self.public_subnet_id = vpc.public_subnets[0].subnet_id
        self.private_subnet_id = vpc.private_subnets[0].subnet_id

        role = iam.Role(self, 'devassoc-webserver', assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'))
        core.Tags.of(role).add('Name', 'devassoc-webserver')
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonPollyReadOnlyAccess'))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('TranslateReadOnly'))
