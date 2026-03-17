CLUSTER_NAME=terraform-lab
TF_DIR=terraform

.PHONY: cluster-up cluster-down tf-init tf-plan tf-apply tf-destroy tf-fmt tf-validate kube-nodes kube-pods

cluster-up:
	bash scripts/create-cluster.sh

cluster-down:
	bash scripts/destroy-cluster.sh

tf-init:
	cd $(TF_DIR) && terraform init

tf-plan:
	cd $(TF_DIR) && terraform plan

tf-apply:
	cd $(TF_DIR) && terraform apply -auto-approve

tf-destroy:
	cd $(TF_DIR) && terraform destroy -auto-approve

tf-fmt:
	cd $(TF_DIR) && terraform fmt -recursive

tf-validate:
	cd $(TF_DIR) && terraform validate

kube-nodes:
	kubectl get nodes

kube-pods:
	kubectl get pods -A
