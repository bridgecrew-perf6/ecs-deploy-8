from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_ecs_patterns as ecs_patterns,
    aws_secretsmanager as secretsmanager,
    core,
)


class InfraStack(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        image_tag = core.CfnParameter(
            self,
            "imageTag",
            type="String",
            description="Image tag to deploy as container",
        )
        # Create VPC and Fargate Cluster
        # NOTE: Limit AZs to avoid reaching resource quotas
        vpc = ec2.Vpc(self, "MyCDKVpc", max_azs=2)

        cluster = ecs.Cluster(self, "CDK_Cluster", vpc=vpc)

        # repository = ecr.Repository(self, 'ecs-deploy', repository_name='ecs-deploy');
        repository = ecr.Repository(self, "ecs-deploy")

        secret = secretsmanager.Secret(self, "ServiceSecret")
        service_secret = ecs.Secret.from_secrets_manager(secret)

        # Above should set the image directly, with https://docs.aws.amazon.com/cdk/api/latest/docs/aws-ecs-patterns-readme.html
        fargate_service = ecs_patterns.NetworkLoadBalancedFargateService(
            self,
            "FargateService",
            cluster=cluster,
            memory_limit_mib=512,
            cpu=256,
            task_image_options={
                "image": ecs.ContainerImage.from_ecr_repository(
                    repository=repository, tag=image_tag.value_as_string
                ),
                "secrets": [service_secret],
            },
            platform_version=ecs.FargatePlatformVersion.VERSION1_4,
        )

        fargate_service.service.connections.security_groups[0].add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(80),
            description="Allow HTTP inbound from VPC",
        )

        core.CfnOutput(
            self,
            "LoadBalancerDNS",
            value=fargate_service.load_balancer.load_balancer_dns_name,
        )

        # core.CfnOutput(
        #     self,
        #     "taskDefinitionFamily",
        #     value=fargate_service.service.task_definition.family,
        # )

        # core.CfnOutput(
        #     self,
        #     "taskDefinitionRoleArn",
        #     value=fargate_service.service.task_definition.execution_role.role_arn,
        # )

        # core.CfnOutput(
        #     self,
        #     "taskDefinitionLogGroup",
        #     value=fargate_service.service.task_definition.default_container.log_driver_config.options["awslogs-group"],
        # )

        # core.CfnOutput(
        #     self,
        #     "taskSecretArn",
        #     value=secret.secret_full_arn,
        # )
