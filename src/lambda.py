#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Cost Explorer Report

A script, for local or lambda use, to generate CostExplorer excel graphs

"""

from __future__ import print_function

__author__ = "David Faulkner"
__version__ = "0.1.0"
__license__ = "MIT No Attribution"

import boto3
import os
import datetime
import logging
import pandas as pd
#For email
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

#GLOBALS
SES_REGION = os.environ.get('SES_REGION')
if not SES_REGION:
    SES_REGION="us-east-1"
ACCOUNT_LABEL = os.environ.get('ACCOUNT_LABEL')
if not ACCOUNT_LABEL:
    ACCOUNT_LABEL = 'Email'

class CostExplorer:
    """Retrieves BillingInfo checks from CostExplorer API
    >>> costexplorer = CostExplorer()
    >>> costexplorer.addReport(GroupBy=[{"Type": "DIMENSION","Key": "SERVICE"}])
    >>> costexplorer.generateExcel()
    """    
    def __init__(self):
        #Array of reports ready to be output to Excel.
        self.reports = []
        self.client = boto3.client('ce', region_name='us-east-1')
        year = datetime.timedelta(days=365)
        self.end = (datetime.date.today().replace(day=25) + datetime.timedelta(days=14)).replace(day=1) - datetime.timedelta(days=1)
        self.riend = datetime.date.today()
        self.start = self.end - year
        self.ristart = self.riend - year
        self.accounts = self.getAccounts()
        
    def getAccounts(self):
        accounts = {}
        client = boto3.client('organizations', region_name='us-east-1')
        paginator = client.get_paginator('list_accounts')
        response_iterator = paginator.paginate()
        for response in response_iterator:
            for acc in response['Accounts']:
                accounts[acc['Id']] = acc
        return accounts
    
    def addRiReport(self, Name="RICoverage"):

        results = []
        response = self.client.get_reservation_coverage(
            TimePeriod={
                'Start': self.ristart.isoformat(),
                'End': self.riend.isoformat()
            },
            Granularity='MONTHLY'
        )
        results.extend(response['CoveragesByTime'])
        while 'nextToken' in response:
            nextToken = response['nextToken']
            response = self.client.get_reservation_coverage(
                TimePeriod={
                    'Start': self.ristart.isoformat(),
                    'End': self.riend.isoformat()
                },
                Granularity='MONTHLY',
                NextPageToken=nextToken
            )
            results.extend(response['CoveragesByTime'])
            if 'nextToken' in response:
                nextToken = response['nextToken']
            else:
                nextToken = False
        
        rows = []
        for v in response['CoveragesByTime']:
            row = {'date':v['TimePeriod']['Start']}
            row.update({'Coverage%':float(v['Total']['CoverageHours']['CoverageHoursPercentage'])})
            rows.append(row)  
                
        df = pd.DataFrame(rows)#index=[i['date'] for i in rows]
        df.set_index("date", inplace= True)
        df = df.fillna(0.0)
        df = df.T
        self.reports.append({'Name':Name,'Data':df})
            
        
    def addReport(self, Name="Default",GroupBy=[{"Type": "DIMENSION","Key": "SERVICE"},], Style='Total'):
        results = []
        response = self.client.get_cost_and_usage(
            TimePeriod={
                'Start': self.start.isoformat(),
                'End': self.end.isoformat()
            },
            Granularity='MONTHLY',
            Metrics=[
                'UnblendedCost',
            ],
            GroupBy=GroupBy
        )

        if response:
            results.extend(response['ResultsByTime'])
            
            while 'nextToken' in response:
                nextToken = response['nextToken']
                response = self.client.get_cost_and_usage(
                    TimePeriod={
                        'Start': self.start.isoformat(),
                        'End': self.end.isoformat()
                    },
                    Granularity='MONTHLY',
                    Metrics=[
                        'UnblendedCost',
                    ],
                    GroupBy=GroupBy,
                    NextPageToken=nextToken
                )
                results.extend(response['ResultsByTime'])
                if 'nextToken' in response:
                    nextToken = response['nextToken']
                else:
                    nextToken = False
        # Now we should have all records, lets setup a waterfall datagrid
        #{key:value for (key,value) in dictonary.items()}
        rows = []
        for v in results:
            row = {'date':v['TimePeriod']['Start']}
            for i in v['Groups']:
                key = i['Keys'][0]
                if key in self.accounts:
                    key = self.accounts[key]['Email']
                row.update({key:float(i['Metrics']['UnblendedCost']['Amount'])}) 
            if not v['Groups']:
                row.update({'Total':float(v['Total']['UnblendedCost']['Amount'])})
            rows.append(row)  

        df = pd.DataFrame(rows)#index=[i['date'] for i in rows]
        df.set_index("date", inplace= True)
        df = df.fillna(0.0)
        
        if Style == 'Change':
            dfc = df.copy()
            lastindex = None
            for index, row in df.iterrows():
                if lastindex:
                    for i in row.index:
                        try:
                            df.at[index,i] = dfc.at[index,i] - dfc.at[lastindex,i]
                        except:
                            logging.exception("Error")
                            df.at[index,i] = 0
                lastindex = index
        df = df.T    
        
        self.reports.append({'Name':Name,'Data':df})
        
        
    def generateExcel(self):
        # Create a Pandas Excel writer using XlsxWriter as the engine.\
        os.chdir('/tmp')
        writer = pd.ExcelWriter('cost_explorer_report.xlsx', engine='xlsxwriter')
        workbook = writer.book
        for report in self.reports:
            report['Data'].to_excel(writer, sheet_name=report['Name'])
            worksheet = writer.sheets[report['Name']]
            
            
            # Create a chart object.
            chart = workbook.add_chart({'type': 'column', 'subtype': 'stacked'})

            for row_num in range(1, len(report['Data']) + 1):
                chart.add_series({
                    'name':       [report['Name'], row_num, 0],
                    'categories': [report['Name'], 0, 1, 0, 12],
                    'values':     [report['Name'], row_num, 1, row_num, 12],
                })
            
            worksheet.insert_chart('N2', chart)
        writer.save()
        
        #Time to deliver the file to S3
        if os.environ.get('S3_BUCKET'):
            s3 = boto3.client('s3')
            s3.upload_file("cost_explorer_report.xlsx", os.environ.get('S3_BUCKET'), "cost_explorer_report.xlsx")
        if os.environ.get('SES_SEND'):
            #Email logic
            msg = MIMEMultipart()
            msg['From'] = os.environ.get('SES_FROM')
            msg['To'] = COMMASPACE.join(os.environ.get('SES_SEND').split(","))
            msg['Date'] = formatdate(localtime=True)
            msg['Subject'] = "Cost Explorer Report"
            text = "Find your Cost Explorer report attached\n\n"
            msg.attach(MIMEText(text))
            with open("cost_explorer_report.xlsx", "rb") as fil:
                part = MIMEApplication(
                    fil.read(),
                    Name="cost_explorer_report.xlsx"
                )
            part['Content-Disposition'] = 'attachment; filename="%s"' % "cost_explorer_report.xlsx"
            msg.attach(part)
            #SES Sending
            ses = boto3.client('ses', region_name=SES_REGION)
            result = ses.send_raw_email(
                Source=msg['From'],
                Destinations=os.environ.get('SES_SEND').split(","),
                RawMessage={'Data': msg.as_string()}
            )     


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
    return "Report Generated"

if __name__ == '__main__':
    main_handler()
