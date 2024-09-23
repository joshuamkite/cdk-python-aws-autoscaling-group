import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_python_aws_autoscaling_group.cdk_python_aws_autoscaling_group_stack import CdkPythonAwsAutoscalingGroupStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_python_aws_autoscaling_group/cdk_python_aws_autoscaling_group_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkPythonAwsAutoscalingGroupStack(app, "cdk-python-aws-autoscaling-group")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
