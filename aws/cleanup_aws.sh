#!/bin/bash

PROJECT_ID=$1
REGION=$2

# Initialize and Destroy Terraform infrastructure
cd terraform
terraform init
terraform destroy -var="project_id=$PROJECT_ID" -var="region=$REGION" -auto-approve

# Remove Docker images from AWS ECR
aws ecr batch-delete-image --repository-name fastapi-app --image-ids imageTag=latest --region $REGION