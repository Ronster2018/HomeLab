variable "region" {
  description = "AWS region to deploy"
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  default     = "t3a.small"
}
