# Automation Setup
## Steps to set up and deploy the FastAPI application on Raspberry Pi, Google Cloud Run, or AWS.

### Prerequisites
1. Ensure you have the necessary tools installed:
   - **Google Cloud SDK** for Google Cloud Run.
   - **AWS CLI** for AWS.
   - **Docker** and **Docker Compose** for Raspberry Pi.

2. Ensure you have authenticated with Google Cloud and AWS if applicable:
   - **Google Cloud**:
     ```bash
     gcloud auth login
     gcloud config set project your-google-cloud-project-id
     ```
   - **AWS**:
     ```bash
     aws configure
     ```

### Steps to Run `deploy.sh`

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

2. **Make the `deploy.sh` Script Executable**:
   ```bash
   chmod +x deploy.sh
   ```

3. **Run the Deployment Script**:
   - For Raspberry Pi:
     ```bash
     ./deploy.sh pi
     ```
   - For Google Cloud Run:
     ```bash
     ./deploy.sh gcr your-google-cloud-project-id your-region
     ```
   - For AWS:
     ```bash
     ./deploy.sh aws your-aws-project-id your-region
     ```

### Summary of `deploy.sh` Script Actions

- **Raspberry Pi**: 
  - Installs Docker and Docker Compose.
  - Builds and runs the Docker containers.

- **Google Cloud Run**: 
  - Builds and pushes the Docker image to Google Container Registry.
  - Deploys the application using Terraform.

- **AWS**: 
  - Builds and pushes the Docker image to AWS ECR.
  - Deploys the application using Terraform.

### Example Commands

#### For Raspberry Pi:

```bash
./deploy.sh pi
```

#### For Google Cloud Run:

```bash
./deploy.sh gcr your-google-cloud-project-id us-central1
```

#### For AWS:

```bash
./deploy.sh aws your-aws-project-id us-west-2
```

This setup will automate the deployment of your FastAPI application to the chosen platform (Raspberry Pi, Google Cloud Run, or AWS).

## Steps to Cleanup FastAPI App using Order66

### Prerequisites
1. Ensure you have the necessary tools installed:
   - **Google Cloud SDK** for Google Cloud Run.
   - **AWS CLI** for AWS.

2. Ensure you have authenticated with Google Cloud and AWS if applicable:
   - **Google Cloud**:
     ```bash
     gcloud auth login
     gcloud config set project your-google-cloud-project-id
     ```
   - **AWS**:
     ```bash
     aws configure
     ```

### Steps to Run `order66.sh`

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

2. **Make the `order66.sh` Script Executable**:
   ```bash
   chmod +x order66.sh
   ```

3. **Run the Cleanup Script**:
   - For Raspberry Pi:
     ```bash
     ./order66.sh pi
     ```
   - For Google Cloud Run:
     ```bash
     ./order66.sh gcr your-google-cloud-project-id your-region
     ```
   - For AWS:
     ```bash
     ./order66.sh aws your-aws-project-id your-region
     ```

### Summary of `order66.sh` Script Actions

- **Raspberry Pi**: Stops and removes Docker containers and images.
- **Google Cloud Run**: Destroys the infrastructure using Terraform and removes Docker images from Google Container Registry.
- **AWS**: Destroys the infrastructure using Terraform and removes Docker images from AWS ECR.

### Example Commands

#### For Raspberry Pi:

```bash
./order66.sh pi
```

#### For Google Cloud Run:

```bash
./order66.sh gcr your-google-cloud-project-id us-central1
```

#### For AWS:

```bash
./order66.sh aws your-aws-project-id us-west-2
```

This process will ensure that all resources created during the deployment are cleaned up automatically.


Sure! Here's a summary of how to run the `deploy.sh` script to deploy your FastAPI application on Raspberry Pi, Google Cloud Run, and AWS.



### Repository Structure
Your repository should have the following structure:

```
your-repo/
├── .env
├── README.md
├── Dockerfile
├── docker-compose.yml
├── horizon-weather-firebase-admin.json
├── main.py
├── requirements.txt
├── deploy.sh
├── order66.sh
├── raspberry_pi/
│   ├── setup_docker.sh
│   ├── deploy_pi.sh
│   └── cleanup_pi.sh
├── google_cloud/
│   ├── deploy_gcr.sh
│   ├── cleanup_gcr.sh
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   └── variables.tf
└── aws/
    ├── deploy_aws.sh
    ├── cleanup_aws.sh
    ├── terraform/
    │   ├── main.tf
    │   ├── outputs.tf
    │   └── variables.tf
```



### Detailed Script Content

#### deploy.sh

```bash
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
```

### Raspberry Pi Deployment Scripts

#### raspberry_pi/setup_docker.sh

```bash
#!/bin/bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get install -y libffi-dev libssl-dev
sudo apt-get install -y python3 python3-pip
sudo pip3 install docker-compose

# Reboot to apply Docker group changes
echo "Rebooting to apply Docker group changes. Please run ./deploy_pi.sh after reboot."
sudo reboot
```

#### raspberry_pi/deploy_pi.sh

```bash
#!/bin/bash
# Navigate to the repository directory
cd "$(dirname "$0")/.."

# Run Docker Compose
docker-compose up --build -d
```

### Google Cloud Deployment Scripts

#### google_cloud/deploy_gcr.sh

```bash
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
```

### AWS Deployment Scripts

#### aws/deploy_aws.sh

```bash
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
```

This setup ensures that you can quickly deploy your FastAPI application to Raspberry Pi, Google Cloud Run, or AWS by running the appropriate commands.