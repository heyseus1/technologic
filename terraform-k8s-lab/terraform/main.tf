resource "kubernetes_namespace" "demo" {
  metadata {
    name = var.demo_namespace

    labels = {
      managed-by = "terraform"
      env        = "local"
    }
  }
}

resource "kubernetes_deployment" "demo_app" {
  metadata {
    name      = var.demo_app_name
    namespace = kubernetes_namespace.demo.metadata[0].name
    labels = {
      app = var.demo_app_name
    }
  }

  spec {
    replicas = var.demo_replicas

    selector {
      match_labels = {
        app = var.demo_app_name
      }
    }

    template {
      metadata {
        labels = {
          app = var.demo_app_name
        }
      }

      spec {
        container {
          name  = "nginx"
          image = "nginx:stable"

          port {
            container_port = 80
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }

            limits = {
              cpu    = "250m"
              memory = "256Mi"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "demo_app" {
  metadata {
    name      = "${var.demo_app_name}-svc"
    namespace = kubernetes_namespace.demo.metadata[0].name
  }

  spec {
    selector = {
      app = var.demo_app_name
    }

    port {
      port        = 80
      target_port = 80
    }

    type = "ClusterIP"
  }
}
