#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="terraform-lab"
CONFIG_FILE="kind/cluster.yaml"

if ! command -v kind >/dev/null 2>&1; then
  echo "kind is not installed"
  exit 1
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl is not installed"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not installed"
  exit 1
fi

if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
  echo "Cluster ${CLUSTER_NAME} already exists"
  exit 0
fi

echo "Creating kind cluster: ${CLUSTER_NAME}"
kind create cluster --config "${CONFIG_FILE}"

echo "Cluster created successfully"
kubectl cluster-info --context "kind-${CLUSTER_NAME}"
kubectl get nodes
