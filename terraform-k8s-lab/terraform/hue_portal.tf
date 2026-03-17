resource "kubernetes_namespace" "hue" {
  metadata {
    name = "hue-system"

    labels = {
      managed-by = "terraform"
      app        = "hue-portal"
    }
  }
}

resource "kubernetes_secret" "hue_portal_env" {
  metadata {
    name      = "hue-portal-env"
    namespace = kubernetes_namespace.hue.metadata[0].name
  }

  data = {
    HUE_BRIDGE_IP      = var.hue_bridge_ip
    HUE_USERNAME       = var.hue_username
    WEB_USERNAME       = var.web_username
    WEB_PASSWORD       = var.web_password
    WEB_SESSION_SECRET = var.web_session_secret
    HOST               = "0.0.0.0"
    PORT               = "8000"
  }

  type = "Opaque"
}

resource "kubernetes_deployment" "hue_portal" {
  metadata {
    name      = "hue-portal"
    namespace = kubernetes_namespace.hue.metadata[0].name

    labels = {
      app = "hue-portal"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "hue-portal"
      }
    }

    template {
      metadata {
        labels = {
          app = "hue-portal"
        }
      }

      spec {
        container {
          name              = "hue-portal"
          image             = "hue-portal:dev"
          image_pull_policy = "IfNotPresent"

          port {
            container_port = 8000
          }

          env_from {
            secret_ref {
              name = kubernetes_secret.hue_portal_env.metadata[0].name
            }
          }

          readiness_probe {
            http_get {
              path = "/healthz"
              port = 8000
            }
            initial_delay_seconds = 5
            period_seconds        = 10
          }

          liveness_probe {
            http_get {
              path = "/healthz"
              port = 8000
            }
            initial_delay_seconds = 10
            period_seconds        = 15
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }

            limits = {
              cpu    = "300m"
              memory = "256Mi"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "hue_portal" {
  metadata {
    name      = "hue-portal"
    namespace = kubernetes_namespace.hue.metadata[0].name
  }

  spec {
    selector = {
      app = "hue-portal"
    }

    port {
      name        = "http"
      port        = 80
      target_port = 8000
    }

    type = "ClusterIP"
  }
}