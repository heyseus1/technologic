variable "kubeconfig_path" {
  description = "Path to kubeconfig"
  type        = string
  default     = "~/.kube/config"
}

variable "kube_context" {
  description = "Kubernetes context name"
  type        = string
  default     = "kind-terraform-lab"
}

variable "demo_namespace" {
  description = "Namespace for demo resources"
  type        = string
  default     = "demo"
}

variable "demo_app_name" {
  description = "Name of the demo app"
  type        = string
  default     = "demo-nginx"
}

variable "demo_replicas" {
  description = "Replica count for demo app"
  type        = number
  default     = 2
}
