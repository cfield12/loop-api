## Name
Loop

![image](https://github.com/user-attachments/assets/50e7bd5b-9f7c-4cfb-83c5-4678f9690925)

## Description
This repository provides the code/templates that created the architecture that supports loop.
Cloudformation templates:

VPC: Elastic IPs, public/private subnets, Internet Gateway, route tables, NAT Gateway

Cognito: User pool, app client, post confirmation Lambda trigger

RDS: Private mysql database

Loop API: endpoints behind loop webapp

Loop Auth API: login/sign up endpoints to log into loop

Lambda: User creator in RDS, restaurant thumbnail uploader to S3, User deleter


## Authors and acknowledgment
Charlie Field.
