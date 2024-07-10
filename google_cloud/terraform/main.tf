provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_cloud_run_service" "default" {
  name     = "fastapi-service"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/fastapi-app"
        ports {
          container_port = 80
        }
        env {
          name  = "ENV_VAR"
          value = "VALUE"
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "noauth" {
  service = google_cloud_run_service.default.name
  location = google_cloud_run_service.default.location
  role    = "roles/run.invoker"
  member  = "allUsers"
}