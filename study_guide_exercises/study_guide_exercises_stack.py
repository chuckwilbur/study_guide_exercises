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

        # role for the ec2 instance to assume
        role = iam.Role(self, 'devassoc-webserver',
                        assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),
                        role_name='devassoc-webserver')
        core.Tags.of(role).add('project', 'devassoc')
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonPollyReadOnlyAccess'))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('TranslateReadOnly'))

        # security group for the ec2 instance
        security_group = ec2.SecurityGroup(self, 'devassoc-sg',
                                           vpc=vpc,
                                           security_group_name='restricted-http-ssh',
                                           description='HTTP and SSH from my IP address only')
        security_group.add_ingress_rule(
            ec2.Peer.ipv4('99.116.136.249/32'), ec2.Port.tcp(22), 'SSH from my IP')
        security_group.add_ingress_rule(
            ec2.Peer.ipv4('99.116.136.249/32'), ec2.Port.tcp(80), 'HTTP from my IP')

        # user data for the ec2 instance
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            'yum install httpd -y',
            'systemctl start httpd',
            'systemctl enable httpd'
        )

        # the ec2 instance
        instance = ec2.Instance(self, 'webserver-ec2',
                                instance_name='webserver',
                                instance_type=ec2.InstanceType('t2.micro'),
                                machine_image=ec2.MachineImage.generic_linux(
                                    ami_map={'us-east-2': 'ami-09558250a3419e7d0'}
                                ),
                                vpc=vpc,
                                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                                role=role,
                                user_data=user_data,
                                security_group=security_group,
                                key_name='devassoc')
