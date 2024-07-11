#!/bin/bash

# Check for the required arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <project_id> <region>"
    exit 1
fi

PROJECT_ID=$1
REGION=$2

# Function to enable Google Cloud APIs
enable_google_apis() {
    echo "~~~ Enabling required Google Cloud APIs..."
    echo "~~~   -  Enabling run.googleapis.com..."
    gcloud services enable run.googleapis.com
    echo "~~~   -  Enabling cloudbuild.googleapis.com..."
    gcloud services enable cloudbuild.googleapis.com
    echo "~~~   -  Enabling containerregistry.googleapis.com..."
    gcloud services enable containerregistry.googleapis.com
}

# Enable Google Cloud APIs
enable_google_apis

# Authenticate with Google Cloud
echo "~~~ Authenticating with Google Cloud..."
gcloud auth configure-docker

# Navigate to the root directory where the Dockerfile is located
cd ..

# Submit build to Google Cloud Build
echo "~~~ Submitting build to Google Cloud Build..."
gcloud builds submit --tag gcr.io/"$PROJECT_ID"/fastapi-app .

# Verify that the image exists in GCR
echo "~~~ Verifying the image exists in GCR..."
if ! gcloud container images list-tags gcr.io/"$PROJECT_ID"/fastapi-app | grep -q "DIGEST"; then
    echo "~~~ Image not found in GCR. Build might have failed."
    exit 1
fi

# Initialize and Apply Terraform
cd google_cloud/terraform
echo "~~~ Initializing Terraform..."
terraform init
echo "~~~ Applying Terraform configuration..."
terraform apply -var="project_id=$PROJECT_ID" -var="region=$REGION" -auto-approve