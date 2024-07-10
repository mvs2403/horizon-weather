output "url" {
  value = aws_ecs_service.fastapi_service.load_balancer[0].dns_name
}