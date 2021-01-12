from aws_cdk import core
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from aws_cdk import aws_rds as rds
from aws_cdk import aws_secretsmanager as secretsmanager

from helpers import instance_types as type


class RDSExerciseStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        default_vpc = ec2.Vpc.from_lookup(self, 'default-vpc', is_default=True)

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
                                            instance_type=type.T2_MICRO,
                                            engine=rds.DatabaseInstanceEngine.maria_db(version=db_version),
                                            credentials=rds.Credentials.from_secret(rds_creds_secret),
                                            security_groups=[db_security_group],
                                            allocated_storage=20,
                                            vpc=default_vpc,
                                            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC))

        core.CfnOutput(self, 'db-endpoint', value=rds_maria_db.db_instance_endpoint_address)
        core.CfnOutput(self, 'db-endpoint-port', value=rds_maria_db.db_instance_endpoint_port)
