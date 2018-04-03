#!/bin/bash
#Suggest deploying to us-east-1 due to CE API, and SES
export AWS_DEFAULT_REGION=us-east-1 
#Change the below
export BUCKET=changeme
export SES_TO=email@test.com,email2@test.com
export SES_FROM=email@test.com
export SES_REGION=us-east-1

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
  AccountLabel=Email ListOfCostTags=CostGroup
