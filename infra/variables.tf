variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-southeast-2"
}

variable "app_name" {
  description = "Application name used as a prefix for all resource names"
  type        = string
  default     = "coffee-card"
}

variable "environment" {
  description = "Deployment environment (e.g. production, staging)"
  type        = string
}

variable "cors_allow_origins" {
  description = "Allowed CORS origins for the API Gateway"
  type        = list(string)
  default     = ["*"]
}
