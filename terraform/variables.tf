variable "aws_region" {
  type    = string
  default = "ap-southeast-1"
}

variable "project_name" {
  type    = string
  default = "aiops-bank"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "my_ip_cidr" {
  type        = string
  description = "IP public CIDR"
}

variable "ci_cd_ssh_cidr_blocks" {
  type        = list(string)
  description = "Additional CIDR blocks allowed to SSH from CI/CD runners"
  default     = []
}

variable "public_key_path" {
  type        = string
  description = "The path direct to file public key"
}

variable "private_key_path" {
  type        = string
  description = "The path direct to private key"
}

variable "ssh_user" {
  type    = string
  default = "ec2-user"
}

variable "monitor_instance_type" {
  type    = string
  default = "t3.small"
}

variable "web_instance_type" {
  type    = string
  default = "t2.micro"
}

variable "core_instance_type" {
  type    = string
  default = "t2.micro"
}

variable "root_volume_size" {
  type    = number
  default = 12
}