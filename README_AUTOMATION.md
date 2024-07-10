# Automation Setup
## Steps to set up and deploy the FastAPI application on Raspberry Pi, Google Cloud Run, or AWS.

### Raspberry Pi

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

2. **Run the Setup and Deployment Script**:
   ```bash
   chmod +x raspberry_pi/setup_docker.sh raspberry_pi/deploy_pi.sh
   ./raspberry_pi/setup_docker.sh
   ```
   - After the Raspberry Pi reboots, run:
   ```bash
   ./raspberry_pi/deploy_pi.sh
   ```

### Google Cloud Run

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

2. **Run the Deployment Script**:
   ```bash
   chmod +x google_cloud/deploy_gcr.sh
   ./deploy.sh gcr your-google-cloud-project-id your-region
   ```

### AWS

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

2. **Run the Deployment Script**:
   ```bash
   chmod +x aws/deploy_aws.sh
   ./deploy.sh aws your-aws-project-id your-region
   ```

### Master Deployment Script (`deploy.sh`)

The master script `deploy.sh` should be run with the appropriate arguments:

```bash
./deploy.sh {pi|gcr|aws} [project_id] [region]
```

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