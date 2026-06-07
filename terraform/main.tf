# ============================================================
# main.tf — defines the network infrastructure to build in AWS
# ============================================================
# This describes a small, standard cloud network — the same building blocks
# you'd configure by hand in the AWS console, but expressed as code that
# Terraform creates, tracks, and can tear down on command.
#
# Every resource here is FREE. AWS does not charge for VPCs, subnets, route
# tables, or internet gateways. (Charges only start with things like EC2
# instances or NAT gateways, which we deliberately do NOT create.)
#
# The structure mirrors on-prem networking concepts you already know:
#   VPC              = your overall network / address space
#   Subnet           = a segment within it (like a VLAN's subnet)
#   Internet Gateway = the router's link to the outside world
#   Route Table      = where to send traffic (the routing table)
# ============================================================

# 1. The VPC — your isolated virtual network and its address space.
resource "aws_vpc" "main" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name      = "nat-lab-vpc"
    ManagedBy = "terraform"
    Project   = "network-automation-toolkit"
  }
}

# 2. A subnet inside the VPC — one segment of the address space.
resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.20.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name      = "nat-lab-public-subnet"
    ManagedBy = "terraform"
  }
}

# 3. Internet gateway — the VPC's connection to the public internet.
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name      = "nat-lab-igw"
    ManagedBy = "terraform"
  }
}

# 4. Route table — sends all outbound traffic (0.0.0.0/0) to the gateway.
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name      = "nat-lab-public-rt"
    ManagedBy = "terraform"
  }
}

# 5. Associate the route table with the subnet so the subnet uses these routes.
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}
