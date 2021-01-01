from aws_cdk import core
from aws_cdk import aws_codepipeline as cppl
from aws_cdk import aws_codepipeline_actions as cpplactions
from aws_cdk import pipelines

from app_pipeline.webserver_stage import WebServerStage


class AppPipelineStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, deploy_all: bool, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        source_artifact = cppl.Artifact()
        cloud_assembly_artifact = cppl.Artifact()

        npm_install_cmd: str = 'npm install -g aws-cdk && pip install -r requirements.txt'

        pipeline = pipelines.CdkPipeline(self, 'Pipeline',
                                         cloud_assembly_artifact=cloud_assembly_artifact,
                                         pipeline_name=construct_id,
                                         source_action=cpplactions.GitHubSourceAction(
                                             action_name='GitHub',
                                             output=source_artifact,
                                             oauth_token=core.SecretValue.secrets_manager('github-as-chuckwilbur-user'),
                                             owner='chuckwilbur',
                                             repo='study_guide_exercises',
                                             branch='main',
                                             trigger=cpplactions.GitHubTrigger.POLL),
                                         synth_action=pipelines.SimpleSynthAction(
                                             source_artifact=source_artifact,
                                             cloud_assembly_artifact=cloud_assembly_artifact,
                                             install_command=npm_install_cmd,
                                             synth_command='cdk synth')
                                         )

        pipeline.add_application_stage(WebServerStage(self, 'Pre-Prod', deploy_all, **kwargs))
