from aws_cdk import core
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms


class KMSKeyExerciseStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        key = kms.Key(self, 'kms-key',
                      alias='devassoc-key',
                      description='Dev Cert Exercise key')
        admin_role = iam.User.from_user_name(self, 'admin-user', 'DevAdmin')
        key.grant_admin(admin_role)
        key.grant_encrypt_decrypt(admin_role)
        self.key_id = key.key_id

        core.CfnOutput(self, 'kms-key-id', value=key.key_id)
        core.CfnOutput(self, 'kms-key-arn', value=key.key_arn)
