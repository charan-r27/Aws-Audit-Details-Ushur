# Aws-Audit-Details-Ushur

The function overview is as follows:
<p align="center"><p align="center">
  <img src="https://user-images.githubusercontent.com/105628050/177704344-f6d26c69-3c73-4f23-8bd6-1f1006a23afd.png" />
</p>
  


The lambda script consists of various functions which are broken down as follows: 


### 1. Developed a Centralized Auditing script that gathers all details of AWS EC2 Instances, Alb rules, Security groups, and Route 53 entries in specified regions in the CSV file and Uploads them into S3 Bucket in AWS. Deployed it for Production, Dev, and QA accounts.
   * ec_details():  Collects Information about Instance ID, Instance Name, Instance Type, and Instance State.
   * alb_info(): Collects Information about ALB Names, Target Groups, and respective DNS Names.
   * SecurityGroups():  Collects Information about Security Group id, IP Permissions, and IP Permission Egress.
   * route53(): Collects Information about all the Entries Names, Types, and DNS Names in the respective Hosted zone for Prod, Dev, and QA.

### 2.Created 4 custom Layers required for the AWS Lambda function.
Using layers can make it faster to deploy the AWS Lambda Function. By moving the runtime dependencies from the function code to a layer can help reduce the overall size of the archive uploaded during a deployment. Created the following layers and uploaded them to AWS Layers in PROD, Dev, and QA accounts.

   * Pandas
   * Requests
   * Twilio
   * Vonage


### 3. Developed a script that identifies the changes between yesterday’s EC2 instances and Today’s EC2 Instances.
* difference(): Shows the details of which new instances are Added, old instances are deleted and Type changed.
<p align="center">
  <img src="https://user-images.githubusercontent.com/105628050/177479804-f29b6ee3-4aba-4024-a39c-6a988559925d.png" />
</p>

### 4. Developed a Cost Report script for AWS, which gathers Total Blended cost (granularity set as DAILY), expended during the past 3 days.
*  costreport():

<p align="center">
  <img src="https://user-images.githubusercontent.com/105628050/177481670-2b512443-1762-439c-a5e8-678e78dbdeaf.png" />
</p>
 
### 5. Implemented API microservices of Twilio and Nexmo in the serverless AWS Lambda functions for Prod, Dev, and QA Accounts.
* twilio_balance(): Retrieves the remaining Twilio Account Balance.
* nexmo_balance(): Retrieves the remaining Nexmo Account Balance.

### 6. Integrated the AWS Lambda functions to Amazon EventBridge (CloudWatch Events) to trigger the lambda function daily using a Cron expression. The lambda function gets Triggered every day at  07:30 AM.

### 7. Created a webhook and Integrated it with a slack channel where all auditing and cost reports are sent on daily basis.

<p align="center">
  <img src="https://user-images.githubusercontent.com/105628050/177485249-f9c60419-89b1-4a7f-b301-2cc7b3c92f83.png" />
</p>

