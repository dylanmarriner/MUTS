terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 6.0"
    }
  }
}

# Get Ubuntu 22.04 ARM image for A1.Flex
data "oci_core_images" "ubuntu" {
  compartment_id           = var.compartment_id
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  shape                    = "VM.Standard.A1.Flex"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# Get the current compartment
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

# Get the first availability domain
locals {
  ad_name = data.oci_identity_availability_domains.ads.availability_domains[0].name
}

# Create a VCN
resource "oci_core_vcn" "main" {
  cidr_block     = "10.0.0.0/16"
  compartment_id = var.compartment_id
  display_name   = "dev-server-vcn"
  dns_label      = "devserver"
}

# Create an internet gateway
resource "oci_core_internet_gateway" "main" {
  compartment_id = var.compartment_id
  display_name   = "dev-server-ig"
  vcn_id         = oci_core_vcn.main.id
}

# Create a route table
resource "oci_core_route_table" "main" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.main.id
  display_name   = "dev-server-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.main.id
  }
}

# Create a security group
resource "oci_core_security_list" "main" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.main.id
  display_name   = "dev-server-sl"

  # Allow SSH traffic
  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    stateless   = false
    tcp_options {
      min = 22
      max = 22
    }
  }

  # Allow HTTP traffic
  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    stateless   = false
    tcp_options {
      min = 80
      max = 80
    }
  }

  # Allow HTTPS traffic
  ingress_security_rules {
    protocol    = "6"
    source      = "0.0.0.0/0"
    stateless   = false
    tcp_options {
      min = 443
      max = 443
    }
  }

  # Allow all outbound traffic
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
    stateless   = false
  }
}

# Create a subnet
resource "oci_core_subnet" "main" {
  availability_domain = local.ad_name
  cidr_block          = "10.0.1.0/24"
  display_name        = "dev-server-subnet"
  dns_label           = "devserver"
  compartment_id      = var.compartment_id
  vcn_id              = oci_core_vcn.main.id
  route_table_id      = oci_core_route_table.main.id
  security_list_ids   = [oci_core_security_list.main.id]
}

# Generate SSH key pair
resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Save the private key to user's SSH directory
resource "local_file" "private_key" {
  content         = tls_private_key.ssh_key.private_key_pem
  filename        = "${pathexpand("~")}/.ssh/oci-dev-key"
  file_permission = "0600"
}

# Create the VM instance (Free Tier A1.Flex - 4 OCPUs, 24GB RAM)
resource "oci_core_instance" "dev_server" {
  availability_domain = local.ad_name
  compartment_id      = var.compartment_id
  display_name        = "dev-server"
  shape               = "VM.Standard.A1.Flex" # Free Tier eligible - ARM-based

  create_vnic_details {
    subnet_id        = oci_core_subnet.main.id
    display_name     = "dev-server-vnic"
    assign_public_ip = true
  }

  source_details {
    source_type            = "image"
    source_id              = data.oci_core_images.ubuntu.images[0].id
    boot_volume_size_in_gbs = 200 # Free Tier max storage
  }

  metadata = {
    ssh_authorized_keys = tls_private_key.ssh_key.public_key_openssh
    user_data           = base64encode(templatefile("${path.module}/cloud-init.yml", {
      ssh_authorized_keys = tls_private_key.ssh_key.public_key_openssh
    }))
  }

  shape_config {
    ocpus         = 4  # Free Tier max
    memory_in_gbs = 24 # Free Tier max
  }
}

# Output the public IP and SSH key path
output "public_ip" {
  value = oci_core_instance.dev_server.public_ip
}

output "ssh_key_path" {
  value = local_file.private_key.filename
}

output "instance_name" {
  value = oci_core_instance.dev_server.display_name
}
