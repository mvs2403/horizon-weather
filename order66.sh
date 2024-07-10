#!/bin/bash

# Function to clean up Raspberry Pi deployment
cleanup_pi() {
    cd raspberry_pi
    ./cleanup_pi.sh
    cd ..
}

# Function to clean up Google Cloud Run deployment
cleanup_gcr() {
    PROJECT_ID=$1
    REGION=$2
    cd google_cloud
    ./cleanup_gcr.sh $PROJECT_ID $REGION
    cd ..
}

# Function to clean up AWS deployment
cleanup_aws() {
    PROJECT_ID=$1
    REGION=$2
    cd aws
    ./cleanup_aws.sh $PROJECT_ID $REGION
    cd ..
}

# Check deployment target
if [ "$1" == "pi" ]; then
    cleanup_pi
elif [ "$1" == "gcr" ]; then
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo "Usage: $0 gcr <project_id> <region>"
        exit 1
    fi
    cleanup_gcr $2 $3
elif [ "$1" == "aws" ]; then
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo "Usage: $0 aws <project_id> <region>"
        exit 1
    fi
    cleanup_aws $2 $3
else
    echo "Usage: $0 {pi|gcr|aws} [project_id] [region]"
    exit 1
fi