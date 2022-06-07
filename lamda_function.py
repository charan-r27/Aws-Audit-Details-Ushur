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




#Listing All regions to collect Instances
def ec_details():
    collect_all_regions=['us-west-1', 'us-east-1',  'eu-west-1', 'eu-west-2', 'ap-southeast-2', 'af-south-1']
    ec2info = defaultdict()
    # Connect to EC2
    for each_region in collect_all_regions:
        ec2 = boto3.resource(service_name='ec2',region_name=each_region)
        running_instances = ec2.instances.all()

        
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
    filename = str(today) + str('_EC2.csv')
    # print(filename)
    df2.to_csv(str(filename))

    #Uploading to Bucket
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('aws-audit-details-ushur')
    bucket.upload_file(str(filename), '%s/%s' %(today,filename))



def alb_info():
    region_name = ['us-west-1', 'us-east-1',  'eu-west-1', 'eu-west-2', 'ap-southeast-2', 'af-south-1']
    headersCSV = ['ALB ','Target Groups']

    current_date = datetime.datetime.now()
    today = str(current_date.day)+str(current_date.month)+str(current_date.year)
    filename = str(today) + str('_ALB.csv')

    with open(filename, 'w') as file:
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
            # for tgs in gettargetgrouparns(lb["LoadBalancerArn"]):
            #     gettargethealth(tgs)
            with open(filename, 'a', newline='') as f_object:
                writer_object = writer(f_object)
                writer_object.writerow(list)  
                f_object.close()

    #Uploading to S3 bucket
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('aws-audit-details-ushur')
    key = str(filename) + str('_ALB.csv')
    bucket.upload_file(str(filename), '%s/%s' %(today,filename))


    
def lambda_handler(event, context):
    
    ec_details()
    alb_info()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!') 
    }


