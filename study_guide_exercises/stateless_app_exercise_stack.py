from aws_cdk import core
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_elasticache as ecache
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_efs as efs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3deploy
from aws_cdk import aws_backup as backup

from helpers.ami_map import ami_map
from helpers import instance_types as type


class StatelessAppExerciseStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        default_vpc = ec2.Vpc.from_lookup(self, 'default-vpc', is_default=True)
        cache_security_group = ec2.SecurityGroup(self, 'devassoc-cache-sg',
                                                 vpc=default_vpc,
                                                 security_group_name='cache-sg-dev-demo',
                                                 description='Elasticache Security Group for AWS Dev Study Guide')
        cache_security_group.add_ingress_rule(
            ec2.Peer.ipv4('99.116.136.249/32'), ec2.Port.tcp(22), 'SSH from my IP')
        cache_security_group.add_ingress_rule(
            cache_security_group, ec2.Port.tcp(2049), 'NFS for mount')

        ecache.CfnCacheCluster(self, 'elasticache',
                               engine='Memcached',
                               cluster_name='devassoc-memcache',
                               num_cache_nodes=2,
                               cache_node_type='cache.t2.micro',
                               vpc_security_group_ids=[cache_security_group.security_group_id])

        efs_volume = efs.FileSystem(self, 'efs-volume',
                                    vpc=default_vpc,
                                    security_group=cache_security_group,
                                    removal_policy=core.RemovalPolicy.DESTROY)

        ec2.Instance(self, 'ec2-efs-instance',
                     instance_name='efs-instance',
                     instance_type=type.T2_MICRO,
                     machine_image=ec2.MachineImage.generic_linux(
                         ami_map=ami_map
                     ),
                     vpc=default_vpc,
                     vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                     security_group=cache_security_group,
                     key_name='devassoc')

        bucket_name = 'devassoc-storage-versioned'
        bucket = s3.Bucket(self, 'bucket-versioned',
                           bucket_name=bucket_name,
                           removal_policy=core.RemovalPolicy.DESTROY,
                           auto_delete_objects=True,
                           versioned=True)
        deploy = s3deploy.BucketDeployment(self, 'DeployFiles',
                                           destination_bucket=bucket,
                                           sources=[s3deploy.Source.asset('./study_guide_exercises/polly_file')],
                                           storage_class=s3deploy.StorageClass.ONEZONE_IA,
                                           cache_control=[s3deploy.CacheControl.set_public()])

        dynamodb_table_name = 'State'
        state_id = dynamodb.Attribute(name='Id', type=dynamodb.AttributeType.STRING)
        dynamo_db = dynamodb.Table(self, 'dynamodb-stateless-app',
                                   table_name=dynamodb_table_name,
                                   partition_key=state_id,
                                   read_capacity=2,
                                   write_capacity=2,
                                   removal_policy=core.RemovalPolicy.DESTROY)

        core.CfnOutput(self, 'db-table-name', value=dynamo_db.table_name)
        core.CfnOutput(self, 'db-table-arn', value=dynamo_db.table_arn)

        global_table_name = 'Tables'
        table_id = dynamodb.Attribute(name='Id', type=dynamodb.AttributeType.STRING)
        table_group = dynamodb.Attribute(name='Group', type=dynamodb.AttributeType.STRING)
        dynamo_db_global = dynamodb.Table(self, 'dynamodb-global',
                                          table_name=global_table_name,
                                          partition_key=table_id,
                                          sort_key=table_group,
                                          stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
                                          replication_regions=['us-west-2', 'eu-central-1'],
                                          removal_policy=core.RemovalPolicy.DESTROY)

        core.CfnOutput(self, 'global-table-name', value=dynamo_db_global.table_name)
        core.CfnOutput(self, 'global-table-arn', value=dynamo_db_global.table_arn)

        # TODO: create this in different region and set up replication
        replication_bucket_name = 'devassoc-storage-replica'
        bucket = s3.Bucket(self, 'bucket-replica',
                           bucket_name=replication_bucket_name,
                           removal_policy=core.RemovalPolicy.DESTROY,
                           auto_delete_objects=True,
                           versioned=True)

        backup_plan = backup.BackupPlan.daily_weekly_monthly5_year_retention(self, 'backup-plan')
        backup_plan.add_selection('backup-selection',
                                  resources=[backup.BackupResource.from_dynamo_db_table(dynamo_db)],
                                  backup_selection_name='StateBackup')
