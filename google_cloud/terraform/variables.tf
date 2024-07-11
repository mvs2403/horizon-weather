variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "memory" {
  description = "The memory limit for the Cloud Run container"
  type        = string
  default     = "1Gi"
}