variable "region" {
  description = "AWS region to deploy"
  default     = "us-east-2"
}

variable "instance_type" {
  description = "EC2 instance type"
  default     = "t2.micro"
}
