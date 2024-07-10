#!/bin/bash

PROJECT_ID=$1
REGION=$2

# Authenticate with Google Cloud
gcloud auth configure-docker

# Build and Push Docker Image
docker build -t gcr.io/$PROJECT_ID/fastapi-app ..
docker push gcr.io/$PROJECT_ID/fastapi-app

# Initialize and Apply Terraform
cd terraform
terraform init
terraform apply -var="project_id=$PROJECT_ID" -var="region=$REGION" -auto-approve