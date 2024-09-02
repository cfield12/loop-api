## Name
Loop API.

## Description
This repository provides the code/templates that created the architecture that supports loop.
Cloudformation templates:
    VPC: Elastic IPs, public/private subnets, Internet Gateway,
    route tables, NAT Gateway
    Cognito: User pool, app client, post confirmation Lambda trigger
    RDS: Private mysql database
    Loop API: endpoints behind loop webapp
    Loop Auth API: login/sign up endpoints to log into loop
    Lambda: User creator in RDS, restaurant thumbnail uploader to S3, User
    deleter

## Visuals
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Contributing
I am not open to contributions.

## Authors and acknowledgment
Charlie Field.
