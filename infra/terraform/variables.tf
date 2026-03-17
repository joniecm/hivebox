variable "location" {
  description = "Azure region for all resources."
  type        = string
  default     = "westeurope"
}

variable "resource_group_name" {
  description = "Resource group name."
  type        = string
  default     = "rg-hivebox-aks"
}

variable "cluster_name" {
  description = "AKS cluster name."
  type        = string
  default     = "aks-hivebox"
}

variable "dns_prefix" {
  description = "DNS prefix for AKS."
  type        = string
  default     = "hivebox"
}

variable "kubernetes_version" {
  description = "AKS Kubernetes version."
  type        = string
  default     = "1.32.10"
}

variable "node_count" {
  description = "Default node pool count."
  type        = number
  default     = 2
}

variable "node_vm_size" {
  description = "AKS node VM size."
  type        = string
  default     = "Standard_DS2_v2"
}

variable "vnet_cidr" {
  description = "VNet address space."
  type        = string
  default     = "10.10.0.0/16"
}

variable "subnet_cidr" {
  description = "Subnet address space."
  type        = string
  default     = "10.10.1.0/24"
}

variable "tags" {
  description = "Common resource tags."
  type        = map(string)
  default = {
    project = "hivebox"
    owner   = "devops"
  }
}
