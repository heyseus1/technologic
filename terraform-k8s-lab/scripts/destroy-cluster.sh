#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="terraform-lab"

if ! command -v kind >/dev/null 2>&1; then
  echo "kind is not installed"
  exit 1
fi

if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
  echo "Deleting kind cluster: ${CLUSTER_NAME}"
  kind delete cluster --name "${CLUSTER_NAME}"
  echo "Cluster deleted"
else
  echo "Cluster ${CLUSTER_NAME} does not exist"
fi
