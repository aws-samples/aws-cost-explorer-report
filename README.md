## AWS Cost Explorer Report Generator

Python SAM Lambda module for generating an Excel cost report with graphs, including month on month cost changes. Uses the AWS Cost Explorer API for data.

![screenshot](https://github.com/aws-samples/aws-cost-explorer-report/blob/master/screenshot.png)

## License Summary

This sample code is made available under a modified MIT license. See the LICENSE file.

## AWS Costs

* AWS Lambda Invocation 
  * Usually [Free](https://aws.amazon.com/free/)  
* Amazon SES 
  * Usually [Free](https://aws.amazon.com/free/)
* Amazon S3
  * Minimal usage
* AWS Cost Explorer API calls   
  * [$0.01 per API call (about 25 calls per run)](https://aws.amazon.com/aws-cost-management/pricing/)

## Prerequisites

* [awscli](https://aws.amazon.com/cli)
* Configure AWS credentials for target account
  * run `aws configure` 
* [Cost Explorer enabled](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-explorer-signup.html)
* [Verfied Amazon SES Sender email](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/verify-email-addresses.html)
* If you verify an email, you can send from/to that address.
* To send to other addresses, you need to [move SES out of sandbox mode](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/request-production-access.html).  
 
Docker (optional for building the lambda python package with updated https://pypi.python.org/ third-party libraries)

## Easy Deploy (us-east-1 only)
If you do not need to modify the code, just deploy the included easy_deploy.yaml using AWS Cloudformation via the console.

## Deploying (SAM / Script)
Update the values in deploy.sh for your AWS account details.  

  | Variable      | Description                                            |
  | ------------- | ------------------------------------------------------ |
  | S3_BUCKET     | S3 Bucket to use                                       |
  | SES_SEND      | Email list to send to (comma separated)                |
  | SES_FROM      | SES Verified Sender Email                              |
  | SES_REGION    | SES Region                                             |
  | COST_TAGS     | List Of Cost Tag Keys (comma separated)                |
  | CURRENT_MONTH | true / false for if report does current partial month  |
  | DAY_MONTH     | When to schedule a run. 6, for the 6th by default      |
  | TAG_KEY       | Provide tag key e.g. Name                              |
  | TAG_VALUE_FILTER       | Provide tag value to filter e.g. Prod*        |
  | LAST_MONTH_ONLY         | Specify true if you wish to generate for only last month  |

And then run `sh deploy.sh`

## Deploy Manually (Lambda Console)

1. Create a lambda function (python 3.6 runtime), and update the code to the contents of src/lambda.py
2. Create a lambda IAM execution role with ce:, ses:, s3:, organizations:ListAccounts
3. Configure the dependency layer: arn:aws:lambda:us-east-1:749981256976:layer:aws-cost-explorer-report:1
4. Update ENV Variables in Lambda console
   * Details in table above. 
5. Create a trigger (CloudWatch Event)

## Running / Testing

Once the Lambda is created, find it in the AWS Lambda console.
You can create ANY test event (as the event content is ignored), and hit the test button for a manual run.

https://docs.aws.amazon.com/lambda/latest/dg/tutorial-scheduled-events-test-function.html

## Building the Lambda Layer (Optional, for if you want to build your own AWS Lambda layer for use with the script)
Run build.sh to build a new AWS lambda layer with the required Python libraries.
This requires Docker, as it builds the package in an Amazon Linux container.

`sh build.sh`

## Customise the report
Edit the `main_handler` segment of src/lambda.py  

```python
def main_handler(event=None, context=None): 
    costexplorer = CostExplorer(CurrentMonth=False)
    #Default addReport has filter to remove Support / Credits / Refunds / UpfrontRI
    #Overall Billing Reports
    costexplorer.addReport(Name="Total", GroupBy=[],Style='Total',IncSupport=True)
    costexplorer.addReport(Name="TotalChange", GroupBy=[],Style='Change')
    costexplorer.addReport(Name="TotalInclCredits", GroupBy=[],Style='Total',NoCredits=False,IncSupport=True)
    costexplorer.addReport(Name="TotalInclCreditsChange", GroupBy=[],Style='Change',NoCredits=False)
    costexplorer.addReport(Name="Credits", GroupBy=[],Style='Total',CreditsOnly=True)
    costexplorer.addReport(Name="Refunds", GroupBy=[],Style='Total',RefundOnly=True)
    costexplorer.addReport(Name="RIUpfront", GroupBy=[],Style='Total',UpfrontOnly=True)
    #GroupBy Reports
    costexplorer.addReport(Name="Services", GroupBy=[{"Type": "DIMENSION","Key": "SERVICE"}],Style='Total',IncSupport=True)
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
    #RI Reports
    costexplorer.addRiReport(Name="RICoverage")
    costexplorer.addRiReport(Name="RIUtilization")
    costexplorer.addRiReport(Name="RIUtilizationSavings", Savings=True)
    costexplorer.addRiReport(Name="RIRecommendation")
    costexplorer.generateExcel()
    return "Report Generated"
```
