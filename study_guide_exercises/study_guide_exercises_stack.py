import json

from os import path
from aws_cdk import core
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from aws_cdk import aws_rds as rds
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_dynamodb as dynamodb


class StudyGuideExercisesStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        default_vpc = ec2.Vpc.from_lookup(self, 'default-vpc', is_default=True)

        # The VPC
        vpc = ec2.Vpc(self, 'devassoc',
                      max_azs=1,
                      nat_gateway_provider=ec2.NatProvider.instance(
                          instance_type=ec2.InstanceType('t2.nano'),
                          key_name='devassoc'
                      ))
        core.Tags.of(vpc).add('Name', 'devassoc')

        self.vpc_id = vpc.vpc_id
        self.public_subnet_id = vpc.public_subnets[0].subnet_id
        self.private_subnet_id = vpc.private_subnets[0].subnet_id
        core.CfnOutput(self, 'vpc-id', value=vpc.vpc_id)
        core.CfnOutput(self, 'public-subnet-id', value=vpc.public_subnets[0].subnet_id)
        core.CfnOutput(self, 'private-subnet-id', value=vpc.private_subnets[0].subnet_id)

        # security group for the NAT
        nat_security_group = ec2.SecurityGroup(self, 'devassoc-nat-sg',
                                               vpc=vpc,
                                               security_group_name='nat-sg',
                                               description='Allow NAT instance to forward internet traffic')
        core.Tags.of(nat_security_group).add('Name', 'nat-sg')
        nat_security_group.add_ingress_rule(
            ec2.Peer.ipv4('10.0.0.0/16'), ec2.Port.tcp(80), 'HTTP from VPC instances')
        nat_security_group.add_ingress_rule(
            ec2.Peer.ipv4('10.0.0.0/16'), ec2.Port.tcp(443), 'HTTPS from VPC instances')
        nat_security_group.add_ingress_rule(
            ec2.Peer.ipv4('10.0.0.0/16'), ec2.Port.all_icmp(), 'PING from VPC instances')
        # chicken and egg problem - can't pass sg to vpc creation

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
            'yum update -y',
            'yum install httpd -y',
            'systemctl start httpd',
            'systemctl enable httpd'
        )

        # the public ec2 instance
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

        # open security group for the private instance
        open_security_group = ec2.SecurityGroup(self, 'devassoc-open-sg',
                                                vpc=vpc,
                                                security_group_name='open-http-ssh',
                                                description='HTTP and SSH from anywhere')
        open_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(22), 'SSH from anywhere')
        open_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(80), 'HTTP from anywhere')
        open_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(443), 'HTTPS from anywhere')

        # user data for the ec2 instance
        this_dir = path.dirname(__file__)
        line_list = [line.rstrip('\n') for line in open(path.join(this_dir, 'site_files/server-polly.txt'))]
        private_user_data = ec2.UserData.for_linux()
        private_user_data.add_commands(*line_list)

        # the private ec2 instance
        instance = ec2.Instance(self, 'private-ec2',
                                instance_name='private-instance',
                                instance_type=ec2.InstanceType('t2.micro'),
                                machine_image=ec2.MachineImage.generic_linux(
                                    ami_map={'us-east-2': 'ami-09558250a3419e7d0'}
                                ),
                                vpc=vpc,
                                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),
                                role=role,
                                user_data=private_user_data,
                                security_group=open_security_group,
                                key_name='devassoc')

        # bucket = s3.Bucket(self, 'bucket',
        #                    bucket_name='devassoc-storage')
        # s3deploy.BucketDeployment(self, 'DeployFiles',
        #                           destination_bucket=bucket,
        #                           sources=[s3deploy.Source.asset('./study_guide_exercises/site_files')])

        # Use the default VPC for the sec group and RDS - RDS requires more than one AZ
        db_security_group = ec2.SecurityGroup(self, 'devassoc-rds-sg',
                                              vpc=default_vpc,
                                              security_group_name='rds-sg-dev-demo',
                                              description='RDS Security Group for AWS Dev Study Guide')
        db_security_group.add_ingress_rule(
            ec2.Peer.ipv4('99.116.136.249/32'), ec2.Port.tcp(3306), 'DB from my IP')
        db_security_group.add_ingress_rule(
            ec2.SecurityGroup.from_lookup(self, 'cloud9-sg', 'sg-0fb01f4548d38de83'), ec2.Port.tcp(3306),
            'DB from Cloud9')

        rds_creds_secret = secretsmanager.Secret.from_secret_name(self, 'db-secret', 'rds-maria-db-creds')
        db_version = rds.MariaDbEngineVersion.VER_10_4_13
        rds_maria_db = rds.DatabaseInstance(self, 'devassoc-rds',
                                            instance_identifier='my-rds-db',
                                            database_name='mytestdb',
                                            instance_type=ec2.InstanceType('t2.micro'),
                                            engine=rds.DatabaseInstanceEngine.maria_db(version=db_version),
                                            credentials=rds.Credentials.from_secret(rds_creds_secret),
                                            security_groups=[db_security_group],
                                            allocated_storage=20,
                                            vpc=default_vpc,
                                            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC))

        core.CfnOutput(self, 'db-endpoint', value=rds_maria_db.db_instance_endpoint_address)
        core.CfnOutput(self, 'db-endpoint-port', value=rds_maria_db.db_instance_endpoint_port)

        user_id = dynamodb.Attribute(name='user_id', type=dynamodb.AttributeType.STRING)
        user_email = dynamodb.Attribute(name='user_email', type=dynamodb.AttributeType.STRING)
        dynamo_db = dynamodb.Table(self, 'dynamodb-table',
                                   table_name='Users',
                                   partition_key=user_id,
                                   sort_key=user_email,
                                   read_capacity=5,
                                   write_capacity=5)

        encrypt_enforce_bucket = s3.Bucket(self, 'encrypt-enforced-bucket',
                                           bucket_name='devassoc-encrypted-storage')
        encrypt_enforce_policy = s3.BucketPolicy(self, 'encrypt-policy',
                                                 bucket=encrypt_enforce_bucket)
        deny_incorrect_statement = {
            "Statement": [
                {
                    "Sid": "DenyIncorrectEncryption",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:PutObject",
                    "Resource": encrypt_enforce_bucket.bucket_arn,
                    "Condition": {
                        "StringNotEquals": {
                            "s3:x-amz-server-side-encryption": "AES256"
                        }
                    }
                }
            ]
        }
        encrypt_enforce_policy.document.add_statements(
            iam.PolicyStatement.from_json(deny_incorrect_statement)
        )
        deny_missing_statement = {
            "Statement": [
                {
                    "Sid": "DenyMissingEncryption",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:PutObject",
                    "Resource": encrypt_enforce_bucket.bucket_arn,
                    "Condition": {
                        "Null": {
                            "s3:x-amz-server-side-encryption": True
                        }
                    }
                }
            ]
        }
        encrypt_enforce_policy.document.add_statements(
            iam.PolicyStatement.from_json(deny_missing_statement)
        )
