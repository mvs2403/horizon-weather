#!/bin/bash

PROJECT_ID=$1
REGION=$2

# Authenticate with AWS
aws configure

# Build and Push Docker Image
docker build -t $PROJECT_ID.dkr.ecr.$REGION.amazonaws.com/fastapi-app ..
$(aws ecr get-login --no-include-email --region $REGION)
docker push $PROJECT_ID.dkr.ecr.$REGION.amazonaws.com/fastapi-app

# Initialize and Apply Terraform
cd terraform
terraform init
terraform apply -var="project_id=$PROJECT_ID" -var="region=$REGION" -auto-approve