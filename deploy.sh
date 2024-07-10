#!/bin/bash

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
    cd google_cloud
    ./deploy_gcr.sh $PROJECT_ID $REGION
    cd ..
}

# Function to deploy to AWS
deploy_aws() {
    PROJECT_ID=$1
    REGION=$2
    cd aws
    ./deploy_aws.sh $PROJECT_ID $REGION
    cd ..
}

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