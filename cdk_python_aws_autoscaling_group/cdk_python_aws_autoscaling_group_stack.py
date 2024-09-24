from aws_cdk import (
    CfnOutput,
    Tags,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_autoscaling as autoscaling,
    aws_elasticloadbalancingv2 as elbv2,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
)
import os
import json
from constructs import Construct
import aws_cdk as cdk


class CdkPythonAwsAutoscalingGroupStack(cdk.Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Parse the TAGS environment variable
        tags = json.loads(os.getenv('TAGS', '[]'))

        print("Parsed tags:", tags)  # Debugging: log the tags to verify

        # Apply tags to the stack
        for tag in tags:
            Tags.of(self).add(tag['key'], tag['value'])

        # Get CREATE_DNS_RECORD environment variable
        create_dns_record = os.getenv('CREATE_DNS_RECORD', 'false')

        # Query the environment to get the current VPC
        vpc = ec2.Vpc.from_lookup(self, 'ExistingVpc', is_default=True)

        # Print the VPC ID and CIDR for debugging
        print(f'Current VPC ID: {vpc.vpc_id}')
        print(f'Current VPC CIDR: {vpc.vpc_cidr_block}')

        # Get the subnets for the current VPC
        subnets = vpc.select_subnets()

        # Print the subnet IDs
        for idx, subnet_id in enumerate(subnets.subnet_ids):
            print(f'Subnet {idx + 1} ID: {subnet_id}')

        # Create a security group
        security_group = ec2.SecurityGroup(self, 'MySecurityGroup',
                                           vpc=vpc,
                                           security_group_name='MySecurityGroup')

        # Add ingress/egress rules
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443), 'Allow HTTPS access')
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), 'Allow HTTP access')
        security_group.add_egress_rule(ec2.Peer.any_ipv4(), ec2.Port.all_traffic(), 'Allow all traffic')

        # Create an IAM role for the EC2 instance
        role = iam.Role(self, 'MyInstanceRole',
                        assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),
                        role_name='MyInstanceRole',
                        description='Allows EC2 instances to call AWS services on your behalf')

        # Attach an IAM policy to the role
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'))

        # VPC Endpoints for SSM
        ec2.InterfaceVpcEndpoint(self, 'SSMVPCEndpoint', vpc=vpc, service=ec2.InterfaceVpcEndpointAwsService.SSM)
        ec2.InterfaceVpcEndpoint(self, 'EC2MessagesVPCEndpoint', vpc=vpc, service=ec2.InterfaceVpcEndpointAwsService.EC2_MESSAGES)
        ec2.InterfaceVpcEndpoint(self, 'SSMSessionManagerVPCEndpoint', vpc=vpc, service=ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES)

        # User data script
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            '#!/bin/bash',
            'dnf update -y',
            'dnf install -y httpd',
            'systemctl start httpd',
            'systemctl enable httpd',
            'echo "<h1>Hello World from $(hostname -f)</h1>" > /var/www/html/index.html'
        )

        # Launch template
        launch_template = ec2.LaunchTemplate(self, 'MyLaunchTemplate',
                                             machine_image=ec2.MachineImage.latest_amazon_linux2023(),
                                             instance_type=ec2.InstanceType('t2.micro'),
                                             user_data=user_data,
                                             security_group=security_group,
                                             role=role,
                                             associate_public_ip_address=True)

        # Auto scaling group
        auto_scaling_group = autoscaling.AutoScalingGroup(self, 'MyAutoScalingGroup',
                                                          vpc=vpc,
                                                          vpc_subnets=ec2.SubnetSelection(subnets=subnets.subnets),  # Pass the subnets this way
                                                          launch_template=launch_template,
                                                          min_capacity=1,
                                                          max_capacity=3,
                                                          )

        # Load balancer
        load_balancer = elbv2.ApplicationLoadBalancer(self, 'MyLoadBalancer',
                                                      vpc=vpc,
                                                      internet_facing=True)

        # Target group
        target_group = elbv2.ApplicationTargetGroup(self, 'MyTargetGroup',
                                                    vpc=vpc,
                                                    port=80,
                                                    protocol=elbv2.ApplicationProtocol.HTTP,
                                                    target_type=elbv2.TargetType.INSTANCE)

        if create_dns_record == 'true':
            # Route53 hosted zone and certificate
            hosted_zone = route53.HostedZone.from_hosted_zone_attributes(self, 'MyHostedZone',
                                                                         hosted_zone_id=os.getenv('HOSTED_ZONE_ID', ''),
                                                                         zone_name=os.getenv('ZONE_NAME', ''))

            cert = acm.Certificate(self, 'MyCertificate',
                                   domain_name=os.getenv('DNS_NAME', ''),
                                   validation=acm.CertificateValidation.from_dns(hosted_zone))

            # DNS A record
            route53.ARecord(self, 'AliasRecord',
                            zone=hosted_zone,
                            target=route53.RecordTarget.from_alias(route53_targets.LoadBalancerTarget(load_balancer)),
                            record_name=os.getenv('DNS_NAME', ''))

            # HTTPS listener
            listener = load_balancer.add_listener('MyListener', port=443, open=True, certificates=[cert])
            load_balancer.add_listener('RedirectListener', port=80, open=True,
                                       default_action=elbv2.ListenerAction.redirect(protocol='HTTPS', port='443', permanent=True))

            # Attach target groups
            listener.add_target_groups('MyTargetGroup', target_groups=[target_group])
            target_group.add_target(auto_scaling_group)
        else:
            # HTTP listener
            listener = load_balancer.add_listener('MyListener', port=80, open=True)
            listener.add_target_groups('MyTargetGroup', target_groups=[target_group])
            target_group.add_target(auto_scaling_group)

        # Output values
        CfnOutput(self, 'LoadBalancerDNS', value=load_balancer.load_balancer_dns_name)
        CfnOutput(self, 'LoadBalancerARN', value=load_balancer.load_balancer_arn)
        CfnOutput(self, 'TargetGroupARN', value=target_group.target_group_arn)
        CfnOutput(self, 'AutoScalingGroupARN', value=auto_scaling_group.auto_scaling_group_arn)
        CfnOutput(self, 'AutoScalingGroupName', value=auto_scaling_group.auto_scaling_group_name)


app = cdk.App()

# Define the AWS account and region for the stack environment
CdkPythonAwsAutoscalingGroupStack(app, "CdkPythonAwsAutoscalingGroupStack", env={
    'account': os.getenv('CDK_DEFAULT_ACCOUNT'),
    'region': os.getenv('CDK_DEFAULT_REGION')
})
app.synth()
