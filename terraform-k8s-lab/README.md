# terraform-k8s-lab

A local Kubernetes lab built with kind, Terraform, Kubernetes, and Helm.

This project is designed to demonstrate platform engineering skills in a laptop environment:
- repeatable Kubernetes cluster creation
- Terraform-managed Kubernetes resources
- Terraform-managed Helm releases
- clean lifecycle management with apply and destroy

## Stack

- Docker Desktop
- kind
- kubectl
- Terraform
- Helm
- Kubernetes provider
- Helm provider

## Goals

- Create a local multi-node Kubernetes cluster
- Manage namespaces, deployments, and services with Terraform
- Build a clean local platform engineering lab on a laptop
- Prepare for later expansion into ingress, metrics, GitOps, and observability

---

## Prerequisites

This project assumes:
- macOS
- Homebrew installed
- GitHub repo already created

Install the required tools:

```bash
brew install --cask docker
brew install kind
brew install kubernetes-cli
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
brew install helm
```

## Validate

```bash

docker info
kind --version
kubectl version --client
terraform version
helm version

```

## initial repo setup

``` bash

mkdir terraform-k8s-lab
cd terraform-k8s-lab
git init

mkdir -p kind terraform scripts
touch README.md .gitignore Makefile
touch kind/cluster.yaml
touch scripts/create-cluster.sh scripts/destroy-cluster.sh
touch terraform/versions.tf
touch terraform/providers.tf
touch terraform/variables.tf
touch terraform/main.tf
touch terraform/outputs.tf
touch terraform/terraform.tfvars.example

```

