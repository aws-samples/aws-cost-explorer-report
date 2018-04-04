## AWS Cost Explorer Report Generator

Python SAM Lambda module for generating an Excel cost report with graphs, including month on month cost changes. Uses the AWS Cost Explorer API for data.

![screenshot](https://github.com/aws-samples/aws-cost-explorer-report/blob/master/screenshot.png)

## License Summary

This sample code is made available under a modified MIT license. See the LICENSE file.

## AWS Costs
Lambda Invocation (Usually Free)  
SES (Usually Free)  
Minimal S3 Usage  
Cost Explorer at 0.01c per API call (about 24c per run)

## Prerequisites
awscli - https://aws.amazon.com/cli/  

configure AWS credentials for target account  
`aws configure` 
 
Docker (optional for building the lambda python package with updated third-party libraries)

## Building (Optional, or use the prebuilt zip in /bin)
Run build.sh to build a new lambda deployment package.
This requires Docker, as it builds the package in an amazon linux container.

`sh build.sh`

## Deploying (SAM / Script)
Update the values in deploy.sh for your AWS account.
And then run deploy.sh

`sh deploy.sh`

## Deploy Manually (Lambda Console)
1. Create a lambda function (python 3.6 runtime)
2. Create a lambda IAM execution role with ce:, ses:, s3:, organizations:ListAccounts
3. Upload zip bin/lambda.zip
4. Update ENV Variables in Lambda console  
  S3_BUCKET: S3 Bucket to use
  SES_SEND: Email list to send to (comma separated)  
  SES_FROM: SES Verified Sender Email  
  SES_REGION: SES Region  
  COST_TAGS: List Of Cost Tag Keys (comma separated)  
5. Create a trigger (CloudWatch Event)
