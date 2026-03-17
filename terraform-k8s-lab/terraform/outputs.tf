output "namespace" {
  value = kubernetes_namespace.demo.metadata[0].name
}

output "deployment_name" {
  value = kubernetes_deployment.demo_app.metadata[0].name
}

output "service_name" {
  value = kubernetes_service.demo_app.metadata[0].name
}
