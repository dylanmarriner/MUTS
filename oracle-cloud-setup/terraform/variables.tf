variable "tenancy_ocid" {
  description = "The OCID of the tenancy"
  type        = string
  sensitive   = true
}

variable "user_ocid" {
  description = "The OCID of the user"
  type        = string
  sensitive   = true
}

variable "fingerprint" {
  description = "The fingerprint of the API key"
  type        = string
  sensitive   = true
}

variable "private_key_path" {
  description = "The path to the private API key file"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "The Oracle Cloud region"
  type        = string
  default     = "ap-sydney-1"
}

variable "compartment_id" {
  description = "The OCID of the compartment"
  type        = string
  sensitive   = true
}

variable "ubuntu_image_id" {
  description = "The OCID of the Ubuntu image"
  type        = string
  default     = "ocid1.image.oc1.ap-sydney-1.aaaaaaaa_example_ubuntu_image"
}

variable "instance_name" {
  description = "Name for the server instance"
  type        = string
  default     = "dev-server"
}
