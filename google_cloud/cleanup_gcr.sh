#!/bin/bash

PROJECT_ID=$1
REGION=$2

# Initialize and Destroy Terraform infrastructure
cd terraform
terraform init
terraform destroy -var="project_id=$PROJECT_ID" -var="region=$REGION" -auto-approve

# Remove Docker images from Google Container Registry
gcloud container images delete gcr.io/"$PROJECT_ID"/fastapi-app --force-delete-tags