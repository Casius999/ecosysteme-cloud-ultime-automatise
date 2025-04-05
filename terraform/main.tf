terraform {
  required_version = ">= 1.0.0"
  
  backend "s3" {
    bucket = var.state_bucket
    key    = "${var.environment}/terraform.tfstate"
    region = var.region
  }
}

provider "aws" {
  region = var.region
  
  default_tags {
    tags = var.default_tags
  }
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  
  name = "${var.environment}-vpc"
  cidr = var.vpc_cidr
  
  azs             = var.availability_zones
  private_subnets = var.private_subnet_cidrs
  public_subnets  = var.public_subnet_cidrs
  
  enable_nat_gateway = true
  single_nat_gateway = var.environment != "production"
  
  enable_vpn_gateway = false
  
  tags = merge(var.default_tags, {
    Environment = var.environment
  })
}