# CDK Python AWS AutoScaling Group

- [CDK Python AWS AutoScaling Group](#cdk-python-aws-autoscaling-group)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
    - [Install the dependencies:](#install-the-dependencies)
    - [Set Up Environment Variables](#set-up-environment-variables)
    - [Deployment](#deployment)
      - [Deploy the Stack](#deploy-the-stack)
    - [Destroy the Stack](#destroy-the-stack)
  - [Useful commands](#useful-commands)

This project is an AWS CDK (Cloud Development Kit) stack written in Python that deploys an AutoScaling group, load balancer, and optionally a Route53 DNS record. Serves 'Hello World' webpage. It uses environment variables for configuration and requires manual setup for account-specific details.

## Prerequisites

Before using this project, ensure you have the following installed:

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- [Node.js](https://nodejs.org/en/download/) (version 14.x or higher)
- [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) (installed globally)

Install AWS CDK globally:

```bash
npm install -g aws-cdk
```

## Setup

### Install the dependencies:










create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```






### Set Up Environment Variables

To configure environment-specific settings, you'll need to create and fill out the appropriate `.env` files.

1. **Default `.env.dns` for DNS configurations:**

   If you want to enable Route53 DNS record creation, the `.env.dns` file has the following structure:

   ```plaintext
   TAGS='[{"key": "Name", "value": "cdk-demo"}, {"key": "environment", "value": "production"}]'
   CREATE_DNS_RECORD=true
   ```

2. **Default `.env.notdns` for configurations without DNS:**

   You can also use `.env.notdns` if you don't want to create Route53 DNS records, TLS certificate etc.:

   ```plaintext
   TAGS='[{"key": "Name", "value": "cdk-demo"}, {"key": "environment", "value": "development"}]'
   CREATE_DNS_RECORD=false
   ```

I find it simpler to export environment variables directly for the common parts, e.g. `source .env.common` where `.env.common` is like:

```bash
export CDK_DEFAULT_ACCOUNT=
export CDK_DEFAULT_REGION=
export AWS_PROFILE=
export AWS_REGION=
export DNS_NAME="" # Only required if CREATE_DNS_RECORD=true
export HOSTED_ZONE_ID='' # Only required if CREATE_DNS_RECORD=true
export ZONE_NAME='' # Only required if CREATE_DNS_RECORD=true
```
 
### Deployment

At this point you can now synthesize the CloudFormation template for this code (optional).

```bash
$ cdk synth
```


#### Deploy the Stack

To deploy the stack to your AWS account:

```bash
   cdk deploy
```

This will deploy your resources, including AutoScaling groups, security groups, load balancers, and (optionally) DNS records if the `.env.dns` file is configured.

### Destroy the Stack

To tear down all the resources created by this stack:

```bash
   cdk destroy
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
