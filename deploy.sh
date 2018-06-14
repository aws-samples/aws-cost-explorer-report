#!/bin/bash
#Suggest deploying to us-east-1 due to CE API, and SES
export AWS_DEFAULT_REGION=us-east-1 
#Change the below, an s3 bucket to store lambda code for deploy, and output report
#Must be in same region as lambda (ie AWS_DEFAULT_REGION)
export BUCKET=changeme
#Comma Seperated list of emails to send too
export SES_TO=email@test.com,email2@test.com
export SES_FROM=email@test.com
export SES_REGION=us-east-1
#Comma Seperated list of Cost Allocation Tags (must be configured in AWS billing prefs)
export COST_TAGS=CostGroup
#Do you want partial figures for the current month (set to true if running weekly/daily)
export CURRENT_MONTH=false

if [ ! -f bin/lambda.zip ]; then
    echo "lambda.zip not found! Downloading one we prepared earlier"
    curl https://s3.amazonaws.com/aws-cost-explorer-report-bin/lambda.zip --create-dirs -o bin/lambda.zip
fi

cd src
zip -ur ../bin/lambda.zip lambda.py
cd ..
aws cloudformation package \
   --template-file src/sam.yaml \
   --output-template-file deploy.sam.yaml \
   --s3-bucket $BUCKET \
   --s3-prefix aws-cost-explorer-report-builds
aws cloudformation deploy \
  --template-file deploy.sam.yaml \
  --stack-name aws-cost-explorer-report \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides SESSendFrom=$SES_FROM S3Bucket=$BUCKET \
  SESSendTo=$SES_TO SESRegion=$SES_REGION \
  AccountLabel=Email ListOfCostTags=$COST_TAGS CurrentMonth=$CURRENT_MONTH
