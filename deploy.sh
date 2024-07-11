#!/bin/bash

set -e

# Function to set permissions
set_permissions() {
    chmod +x raspberry_pi/setup_docker.sh
    chmod +x raspberry_pi/deploy_pi.sh
    chmod +x raspberry_pi/cleanup_pi.sh
    chmod +x google_cloud/deploy_gcr.sh
    chmod +x google_cloud/cleanup_gcr.sh
    chmod +x aws/deploy_aws.sh
    chmod +x aws/cleanup_aws.sh
}

# Function to install Terraform
install_terraform() {
    if ! command -v terraform > /dev/null 2>&1; then
        echo "Terraform is not installed. Installing Terraform..."
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            wget https://releases.hashicorp.com/terraform/1.0.10/terraform_1.0.10_linux_amd64.zip
            unzip terraform_1.0.10_linux_amd64.zip
            sudo mv terraform /usr/local/bin/
            rm terraform_1.0.10_linux_amd64.zip
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install terraform
        else
            echo "Unsupported OS type: $OSTYPE"
            exit 1
        fi
    else
        echo "Terraform is already installed."
    fi
}

# Function to enable Google Cloud APIs
enable_google_apis() {
    gcloud services enable run.googleapis.com || exit 1
    gcloud services enable cloudbuild.googleapis.com || exit 1
    gcloud services enable containerregistry.googleapis.com || exit 1
}

# Function to check if billing is enabled
check_billing_enabled() {
    PROJECT_ID=$1
    if ! gcloud beta billing projects describe $PROJECT_ID | grep -q "billingEnabled: true"; then
        echo "Billing is not enabled for project $PROJECT_ID. Please enable billing and try again."
        exit 1
    fi
}

# Function to ensure Docker is running
ensure_docker_running() {
    if ! docker info > /dev/null 2>&1; then
        echo "Docker daemon is not running. Attempting to start Docker..."
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo systemctl start docker
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            open -a Docker
            while ! docker info > /dev/null 2>&1; do
                echo "Waiting for Docker to start..."
                sleep 5
            done
        else
            echo "Please start Docker manually."
            exit 1
        fi
    fi
}

# Function to deploy to Raspberry Pi
deploy_pi() {
    cd raspberry_pi
    ./setup_docker.sh
    ./deploy_pi.sh
    cd ..
}

# Function to deploy to Google Cloud Run
deploy_gcr() {
    PROJECT_ID=$1
    REGION=$2
    check_billing_enabled $PROJECT_ID
    enable_google_apis
    cd google_cloud
    ./deploy_gcr.sh $PROJECT_ID $REGION
    cd ..
}

# Function to deploy to AWS
deploy_aws() {
    PROJECT_ID=$1
    REGION=$2
    ensure_docker_running
    cd aws
    ./deploy_aws.sh $PROJECT_ID $REGION
    cd ..
}

# Ensure scripts have the right permissions
set_permissions

# Install Terraform if not installed
install_terraform

# Check deployment target
if [ "$1" == "pi" ]; then
    deploy_pi
elif [ "$1" == "gcr" ]; then
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo "Usage: $0 gcr <project_id> <region>"
        exit 1
    fi
    deploy_gcr $2 $3
elif [ "$1" == "aws" ]; then
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo "Usage: $0 aws <project_id> <region>"
        exit 1
    fi
    deploy_aws $2 $3
else
    echo "Usage: $0 {pi|gcr|aws} [project_id] [region]"
    exit 1
fi