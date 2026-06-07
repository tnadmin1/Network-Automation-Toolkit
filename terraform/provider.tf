# ============================================================
# provider.tf — tells Terraform WHICH cloud to talk to and HOW
# ============================================================
# This file declares the AWS provider. Note there are NO credentials here.
# Terraform automatically reads them from ~/.aws/credentials (the file you
# created), so this code is completely safe to commit to a public repo.
# ============================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1" # matches the region in your ~/.aws/config
  # No access keys here on purpose — they come from ~/.aws/credentials.
}
