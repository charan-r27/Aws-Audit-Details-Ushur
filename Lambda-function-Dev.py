import json
import boto3
from pprint import pprint
from collections import defaultdict
import csv
import os
import datetime
from email import header
from csv import writer
import pandas as pd
import numpy as np
from email import message
from datetime import date
from datetime import timedelta
from io import StringIO 
import vonage
import twilio
import requests
from twilio.rest import Client



import requests


finalmsg = ""

   
   
#Listing All regions to collect Instances
def ec_details():
    collect_all_regions=['us-west-2']
    ec2info = defaultdict()
    # Connect to EC2
    for each_region in collect_all_regions:
        ec2 = boto3.resource(service_name='ec2',region_name=each_region)
        running_instances = ec2.instances.all()
        region = each_region

        
        for instance in running_instances:
            for tag in instance.tags:
                if 'Name'in tag['Key']:
                    name = tag['Value']
            # Add instance info to a dictionary         
            ec2info[instance.id] = {
                    
                'Id': instance.id,
                'Name': name,
                'Type': instance.instance_type,
                'State': instance.state['Name']
                }
            ec2info[instance.id].update({'Region' : "us-west-2"})    
        
        

        # attributes = ['Id','Name', 'Type', 'State']
        # for instance_id, instance in ec2info.items():
        #     for key in attributes:
        #         print("{0}: {1}".format(key, instance[key]))
        #     print("------")


    df = pd.DataFrame.from_dict(ec2info)

    df2 = df.T
    df2.reset_index(drop=True, inplace=True)
    df2 = df2.loc[:, ~df2.columns.str.contains('^Unnamed')]
    # print(df2)
    current_date = datetime.datetime.now()
    today = str(current_date.day)+str(current_date.month)+str(current_date.year)
    filenametmp = '/tmp/'+ str(today) + str('_EC2.csv')
    # print(filename)
    df2.to_csv(str(filenametmp))
    print(df2)
    
    # Uploading to Bucket
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('aws-audit-details-ushur')
    todayProd = today + "_Dev"
    filename = str(today) + str('_EC2.csv')
    bucket.upload_file(str(filenametmp), '%s/%s' %(todayProd,filename),)



def alb_info():
    region_name = ['us-west-2']
    headersCSV = ['ALB ','Target Groups','DNSName']

    current_date = datetime.datetime.now()
    today = str(current_date.day)+str(current_date.month)+str(current_date.year)
    filenametmp = '/tmp/' + str(today) + str('_ALB.csv')

    with open(filenametmp, 'w') as file:
        dw = csv.DictWriter(file, delimiter=',',fieldnames=headersCSV)
        dw.writeheader()


    for each_region in region_name:
        elb = boto3.client(service_name='elbv2',region_name=each_region)
        ec2 = boto3.client(service_name='ec2',region_name=each_region)

        def gettargetgroups(arn):
            tgs=elb.describe_target_groups(LoadBalancerArn=arn)
            tgstring=[]
            for tg in tgs["TargetGroups"]:
                tgstring.append(tg["TargetGroupName"])
            return tgstring

        def gettargetgrouparns(arn):
            tgs=elb.describe_target_groups(LoadBalancerArn=arn)
            tgarns=[]
            for tg in tgs["TargetGroups"]:
                tgarns.append(tg["TargetGroupArn"])
            return tgarns

        def getinstancename(instanceid):
            instances=ec2.describe_instances(Filters=[
                {
                    'Name': 'instance-id',
                    'Values': [
                        instanceid
                    ]
                },
            ],)
            for instance in instances["Reservations"]:
                for inst in instance["Instances"]:
                    for tag in inst["Tags"]:
                        if tag['Key'] == 'Name':
                            return (tag['Value'])
            
        def gettargethealth(arn):
            inss=elb.describe_target_health(TargetGroupArn=arn)
            instanceids=[]
            for ins in inss["TargetHealthDescriptions"]:
                ins["Name"]=getinstancename(ins['Target']['Id'])
                instanceids.append(ins['Target']['Id'])
                print (ins)

        lbs = elb.describe_load_balancers(PageSize=400)

        for lb in lbs["LoadBalancers"]:
            print("\n")
            # # print ("-"*6)
            # print("Name:",lb["LoadBalancerName"])
            # print("Type:",lb["Type"])
            # print("TargetGroups:",str(gettargetgroups(lb["LoadBalancerArn"])))
            list = []
            list.append(lb["LoadBalancerName"])
            list.append(str(gettargetgroups(lb["LoadBalancerArn"])))
            list.append(lb["DNSName"])
            # for tgs in gettargetgrouparns(lb["LoadBalancerArn"]):
            #     gettargethealth(tgs)
            with open(filenametmp, 'a', newline='') as f_object:
                writer_object = writer(f_object)
                writer_object.writerow(list)  
                f_object.close()

    #Uploading to S3 bucket
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('aws-audit-details-ushur')
    todayProd = today + "_Dev"
    filename = str(today) + str('_ALB.csv')
    bucket.upload_file(str(filenametmp), '%s/%s' %(todayProd,filename),)

def SecurityGroups():
    
    headersCSV = ['Security Group ID ','IP Permissions','IP permissions Egress']
    
    current_date = datetime.datetime.now()
    today = str(current_date.day)+str(current_date.month)+str(current_date.year)
    filenametmp = '/tmp/' + str(today) + str('_SecurityGroups.csv')
    
    
    with open(filenametmp, 'w') as file:
           dw = csv.DictWriter(file, delimiter=',',fieldnames=headersCSV)
           dw.writeheader()
    
    #Listing All regions to collect Instances
    collect_all_regions =['us-west-2']
    # Connect to EC2
    for each_region in collect_all_regions:
            ec2 = boto3.client(service_name='ec2',region_name=each_region)
            response=ec2.describe_security_groups()
            security_groups = response['SecurityGroups']
            for group_object in security_groups:
                list = []
                list.append(group_object["GroupId"])
                list.append(group_object["IpPermissions"])
                list.append(group_object["IpPermissionsEgress"])
    
                with open(filenametmp, 'a', newline='') as f_object:
                    writer_object = writer(f_object)
                    writer_object.writerow(list)  
                    f_object.close()
                    
                    
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('aws-audit-details-ushur')
    todayProd = today + "_Dev"
    filename = str(today) + str('_SecurityGroups.csv')
    bucket.upload_file(str(filenametmp), '%s/%s' %(todayProd,filename),)  
    
    
def route53():
    client = boto3.client('route53')
    headersCSV = ['Name ','Type','DNSName']
    current_date = datetime.datetime.now()
    today = str(current_date.day)+str(current_date.month)+str(current_date.year)
   
    filenametmp = '/tmp/' + str(today)+ str('_Route53.csv')
    
    with open(filenametmp, 'w') as file:
           dw = csv.DictWriter(file, delimiter=',',fieldnames=headersCSV)
           dw.writeheader()
    
    
    paginator = client.get_paginator('list_resource_record_sets')
    
    try:
        HostedZoneId = os.environ['HostedZoneId']
        source_zone_records = paginator.paginate(HostedZoneId=HostedZoneId)
        for record_set in source_zone_records:
            for record in record_set['ResourceRecordSets']:
    
                    if 'AliasTarget' in record:
                        # print (record['Name']+','+record['Type']+','+record['AliasTarget']['DNSName'])
                        list = []
                        list.append(record["Name"])
                        list.append(record["Type"])
                        list.append(record['AliasTarget']['DNSName'])
                        with open(filenametmp, 'a', newline='') as f_object:
                            writer_object = writer(f_object)
                            writer_object.writerow(list)  
                            f_object.close()
    
                    else:
                        records=[]
                        for ip in record['ResourceRecords']:
                            records.append(ip['Value'])
                        t = ','.join(records)
                        # print(records)
    
                        list = []
                        list.append(record["Name"])
                        list.append(record["Type"])
                        list.append(t)
    
                        with open(filenametmp, 'a', newline='') as f_object:
                            writer_object = writer(f_object)
                            writer_object.writerow(list)  
                            f_object.close()
    
                        # print (record['Name']+','+record['Type']+','+','.join(records))
    
    except Exception as error:
    	print ('An error occured getting source zone records '+ str(error))
    	exit(1)
    
    df = pd.read_csv(filenametmp)
    df.sort_values(["Type"],axis=0,ascending=[True],inplace=True)
    df.reset_index(drop=True, inplace=True)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.to_csv(str(filenametmp))
    
    
    # s3 = boto3.resource('s3')
    # bucket_name = 'aws-audit-details-ushur'
    # s3_object_name = str(today)+ str('_Route53.csv')
    # s3.Object(bucket_name, s3_object_name).put(Body=csv_buffer.getvalue())
    
    
    # bucket = s3.Bucket('aws-audit-details-ushur')
    # today = today+ "_Dev"
    # bucket.upload_file(str(filename), '%s/%s' %(today,filename))
    
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('aws-audit-details-ushur')
    todayProd = today + "_Dev"
    filename = str(today) + str('_Route53.csv')
    bucket.upload_file(str(filenametmp), '%s/%s' %(todayProd,filename),)



def difference():
    
    global finalmsg
    
    s3 = boto3.client('s3')
    bucket = 'aws-audit-details-ushur'
    
    today = date.today()
    yesterday = today - timedelta(days = 1)
    today = str(today.day)+str(today.month)+str(today.year)
    
    yesterday = str(yesterday.day)+str(yesterday.month)+str(yesterday.year)
    
    
    todayfile = str(today)+ str('_EC2.csv')
    yesterdayfile = str(yesterday) + str('_EC2.csv')
    
    today = today + "_Dev"
    yesterday = yesterday + "_Dev"
    path1 = today + "/" + todayfile
    path2 = yesterday + "/" + yesterdayfile
    obj1 = s3.get_object(Bucket=bucket, Key=path1)
    obj2 = s3.get_object(Bucket=bucket, Key=path2)
    
    df2 = pd.read_csv(obj1['Body']) 
    df1 = pd.read_csv(obj2['Body']) 
    
    #df2 = pd.read_csv ('1362022_EC2.csv',index_col=[0])
    #df2 = pd.read_csv (todayfile,index_col=[0])
    
    old = list(df1['Id'])
    new = list(df2['Id'])
    
    # print(list1)
    # old = dict(list1) 
    # new = dict(list2)
    
    # removed = {k:old[k] for k in old.keys() - new.keys()}
    # added = {k:new[k] for k in new.keys() - old.keys()}
    
    def compare_list(old, new):
        new_set = set(new)
        old_set = set(old)
        return new_set - old_set, old_set - new_set, new_set & old_set
    
    
    added, deleted, unchanged = compare_list(old, new)
    
    ListAdded = list(added)
    ListDeleted = list(deleted)
    
    cnt1 = 0
    cnt2 = 0
    if(len(added)==0):
        # print("No New Instance Added \n")
        msg1 = "No New Instance Added \n"
    
    else:
        # print("Total Number of Instance Added: ",len(added),"Instance added: ", ListAdded)
        msg1 = "Total Number of Instance Added:"+str(len(added)) + "\n"+"Instance added:" +"\n"
        for i in added:
            cnt1+=1
            msg1 += str(cnt1) +". Instance ID: " + str(i)
            a = df2.loc[df2['Id'] == i, 'Name'].item()
            msg1 +=" ," +"Instance Name: " +str(a) + "\n"
            
        # print(msg1)
    
    # print('\n')
    msg2 = ""
    if(len(deleted)==0):
        # print("No Instance was Deleted")
        msg2 += "No Instance was Deleted"
    
    else:
        
        # print("Total Number of Instance Deleted: ",len(deleted),"Instance Deleted: ", ListDeleted)
        msg2 += "Total Number of Instance Deleted:" +str(len(deleted))+ "\n"+ "Instance Deleted:" +"\n"
    
        for i in deleted:
            cnt2+=1
            msg2 += str(cnt2) +". Instance ID: " + str(i)
            b = df1.loc[df1['Id'] == i, 'Name'].item()
            msg2 += " ," +"Instance Name: " +str(b) + "\n"
        
        # print(msg2)
    
    df3 =pd.merge(df2, df1, on='Id')
    df3['diff'] = np.where(df3['Type_x'] == df3['Type_y'] , '0', '1')
    df3.to_csv("/tmp/merged.csv")
    
    df4 = pd.read_csv("/tmp/merged.csv")
    df4.reset_index(drop=True, inplace=True)
    df4 = df4.loc[:, ~df4.columns.str.contains('^Unnamed')]
    df5 = df4.filter(['Id','Name_x','Type_x','Type_y','diff'],axis=1)
    df6 = df5.loc[df5['diff'] == 1]
    
    typechange = "\nInstances Changed : \n"
    cnt = 0
    if not(df6.empty):
        for index, row in df6.iterrows():
            cnt+=1
            typechange += str(cnt)+ ". Instance Id: " + row['Id']  + ",Instance Name: " + row['Name_x']  + "\n Type changed: " + row['Type_x'] + " → " + row['Type_y']
            typechange += "\n"
    
    else:
        typechange += "No instances were changed"
    
    # print(typechange)
    sns = boto3.client('sns',region_name="us-east-1")
    msg = msg1+ "\n " + msg2
    # finalmsg =  "EC2 Instance Changes are: " + "\n"
    finalmsg += "------------------------------------------------------------------------------------------------------------------"
    finalmsg += "\n"

    finalmsg += "𝐃𝐞𝐯 𝐀𝐜𝐜𝐨𝐮𝐧𝐭: \n"
    finalmsg += "\n"
    finalmsg += msg
    finalmsg += "\n"
    finalmsg += typechange
    
    today = date.today()
    today = str(today.day)+str(today.month)+str(today.year)
    today = today + "_Dev"
    finalmsg += "\n \n𝑻𝒉𝒆 𝒓𝒆𝒑𝒐𝒓𝒕𝒔 𝒂𝒓𝒆 𝒂𝒗𝒂𝒊𝒍𝒂𝒃𝒍𝒆 𝒂𝒕: \n " + "s3://aws-audit-details-ushur/" + str(today) + "/"
    finalmsg += '\n \n'
    



    
    
def twilio_balance():
    global finalmsg
    account_sid = os.environ['twilio_account_sid']
    auth_token = os.environ['twilio_auth_token']
    twilio_client = Client(account_sid, auth_token)
    
    finalmsg +="𝐓𝐰𝐢𝐥𝐢𝐨 𝐀𝐜𝐜𝐨𝐮𝐧𝐭 𝐁𝐚𝐥𝐚𝐧𝐜𝐞 𝐢𝐬 : "
    balancemsg = str(twilio_client.api.v2010.balance.fetch().balance)
    finalmsg += balancemsg
    finalmsg += " USD"
    finalmsg +='\n'
    
    
def nexmo_balance():
    global finalmsg
    key = os.environ['nexmo_key']
    secret = os.environ['nexmo_secret']
    nexmo = vonage.Client(key, secret)
    res_nexmo = nexmo.account.get_balance()
    finalmsg += "𝐍𝐞𝐱𝐦𝐨 𝐀𝐜𝐜𝐨𝐮𝐧𝐭 𝐁𝐚𝐥𝐚𝐧𝐜𝐞 𝐢𝐬 : " + str(res_nexmo['value']) + " EUR" + "\n"


def send_slack_message(slack_webhook_url, slack_message):
  slack_payload = {'text': slack_message}
  response = requests.post(slack_webhook_url, json.dumps(slack_payload))
  
  
def lambda_handler(event, context):
    ec_details()
    alb_info()
    SecurityGroups()
    global finalmsg
    difference()
    route53()
    nexmo_balance()
    twilio_balance()
    
    URL = os.environ['URL']
    
    finalmsg += "------------------------------------------------------------------------------------------------------------------"
    finalmsg += '\n'
    send_slack_message(URL,finalmsg)

    print(finalmsg)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!') 
    }
