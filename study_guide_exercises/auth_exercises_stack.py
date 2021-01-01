from aws_cdk import core
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_directoryservice as ad
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_iam as iam


class AuthExercisesStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        env = kwargs.get('env', {})
        if env['region'] == 'us-east-1':  # simple AD not in us-east-2
            # The VPC for simple AD
            simple_vpc = ec2.Vpc(self, 'devassoc-auth-simple',
                                 max_azs=2,
                                 cidr='10.40.0.0/16',
                                 subnet_configuration=[
                                     ec2.SubnetConfiguration(
                                         name='simple-ad-demo-',
                                         subnet_type=ec2.SubnetType.PUBLIC,
                                         cidr_mask=24
                                     )
                                 ])
            core.Tags.of(simple_vpc).add('Name', 'devassoc-simple-ad-demo')

            self.vpc_id = simple_vpc.vpc_id
            core.CfnOutput(self, 'simple-vpc-id', value=simple_vpc.vpc_id)
            core.CfnOutput(self, 'simple-public-subnet-id-1', value=simple_vpc.public_subnets[0].subnet_id)
            core.CfnOutput(self, 'simple-public-subnet-az-1', value=simple_vpc.public_subnets[0].availability_zone)
            core.CfnOutput(self, 'simple-public-subnet-id-2', value=simple_vpc.public_subnets[1].subnet_id)
            core.CfnOutput(self, 'simple-public-subnet-az-2', value=simple_vpc.public_subnets[1].availability_zone)

            ad.CfnSimpleAD(self, 'simple-ad',
                           name='simple-ad-demo',
                           password='admin123!',
                           size='Small',
                           vpc_settings={
                               "vpcId": simple_vpc.vpc_id,
                               "subnetIds": [
                                   simple_vpc.public_subnets[0].subnet_id,
                                   simple_vpc.public_subnets[1].subnet_id
                               ]
                           })

        # The VPC for Microsoft AD
        microsoft_vpc = ec2.Vpc(self, 'devassoc-auth-microsoft',
                                max_azs=2,
                                cidr='10.30.0.0/16',
                                subnet_configuration=[
                                    ec2.SubnetConfiguration(
                                        name='microsoft-ad-demo-',
                                        subnet_type=ec2.SubnetType.PUBLIC,
                                        cidr_mask=24
                                    )
                                ])
        core.Tags.of(microsoft_vpc).add('Name', 'devassoc-microsoft-ad-demo')

        self.vpc_id = microsoft_vpc.vpc_id
        core.CfnOutput(self, 'microsoft-vpc-id', value=microsoft_vpc.vpc_id)
        core.CfnOutput(self, 'microsoft-public-subnet-id-1', value=microsoft_vpc.public_subnets[0].subnet_id)
        core.CfnOutput(self, 'microsoft-public-subnet-az-1', value=microsoft_vpc.public_subnets[0].availability_zone)
        core.CfnOutput(self, 'microsoft-public-subnet-id-2', value=microsoft_vpc.public_subnets[1].subnet_id)
        core.CfnOutput(self, 'microsoft-public-subnet-az-2', value=microsoft_vpc.public_subnets[1].availability_zone)

        ad.CfnMicrosoftAD(self, 'microsoft-ad',
                          name='corp.example.com',  # must be valid as a DNS name
                          short_name='corp',  # console calls this "Directory NetBIOS name"
                          password='microsoft-ad-123!',
                          edition='Standard',
                          vpc_settings={
                              "vpcId": microsoft_vpc.vpc_id,
                              "subnetIds": [
                                  microsoft_vpc.public_subnets[0].subnet_id,
                                  microsoft_vpc.public_subnets[1].subnet_id
                              ]
                          })

        # There should be a Cloud Directory example here, but I couldn't find a CDK API

        cognito_user_pool = cognito.UserPool(self, 'cognito-user-pool',
                                             user_pool_name='admin-group',
                                             sign_in_aliases={'username': True})
        core.Tags.of(cognito_user_pool).add('user', 'admin-user')
