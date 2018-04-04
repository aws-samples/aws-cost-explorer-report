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

Verfied SES Sender Email
https://docs.aws.amazon.com/ses/latest/DeveloperGuide/verify-email-addresses.html
 
Docker (optional for building the lambda python package with updated https://pypi.python.org/ third-party libraries)

## Building (Optional, or use the prebuilt zip in /bin)
Run build.sh to build a new lambda deployment package.
This requires Docker, as it builds the package in an amazon linux container.

`sh build.sh`

## Deploying (SAM / Script)
Update the values in deploy.sh for your AWS account details.
And then run deploy.sh

`sh deploy.sh`

## Deploy Manually (Lambda Console)
1. Create a lambda function (python 3.6 runtime)
2. Create a lambda IAM execution role with ce:, ses:, s3:, organizations:ListAccounts
3. Upload code as zip bin/lambda.zip
4. Update ENV Variables in Lambda console  
  S3_BUCKET: S3 Bucket to use
  SES_SEND: Email list to send to (comma separated)  
  SES_FROM: SES Verified Sender Email  
  SES_REGION: SES Region  
  COST_TAGS: List Of Cost Tag Keys (comma separated)  
5. Create a trigger (CloudWatch Event)

## Customise the report
Edit the last segment of src/lambda.py

```python
def main_handler(event=None, context=None): 
    costexplorer = CostExplorer()
    costexplorer.addReport(Name="Total", GroupBy=[],Style='Total')
    costexplorer.addReport(Name="TotalChange", GroupBy=[],Style='Change')
    costexplorer.addRiReport(Name="RICoverage")
    costexplorer.addReport(Name="Services", GroupBy=[{"Type": "DIMENSION","Key": "SERVICE"}],Style='Total')
    costexplorer.addReport(Name="ServicesChange", GroupBy=[{"Type": "DIMENSION","Key": "SERVICE"}],Style='Change')
    costexplorer.addReport(Name="Accounts", GroupBy=[{"Type": "DIMENSION","Key": "LINKED_ACCOUNT"}],Style='Total')
    costexplorer.addReport(Name="AccountsChange", GroupBy=[{"Type": "DIMENSION","Key": "LINKED_ACCOUNT"}],Style='Change')
    costexplorer.addReport(Name="Regions", GroupBy=[{"Type": "DIMENSION","Key": "REGION"}],Style='Total')
    costexplorer.addReport(Name="RegionsChange", GroupBy=[{"Type": "DIMENSION","Key": "REGION"}],Style='Change')
    if os.environ.get('COST_TAGS'): #Support for multiple/different Cost Allocation tags
        for tagkey in os.environ.get('COST_TAGS').split(','):
            tabname = tagkey.replace(":",".") #Remove special chars from Excel tabname
            costexplorer.addReport(Name="{}".format(tabname)[:31], GroupBy=[{"Type": "TAG","Key": tagkey}],Style='Total')
            costexplorer.addReport(Name="Change-{}".format(tabname)[:31], GroupBy=[{"Type": "TAG","Key": tagkey}],Style='Change')
    costexplorer.generateExcel()
    return "Report Generated"
```
