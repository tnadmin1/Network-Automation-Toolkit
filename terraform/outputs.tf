# ============================================================
# outputs.tf — values Terraform prints after building
# ============================================================
# After 'terraform apply', these IDs print to your terminal. They're proof the
# resources were really created, and you can paste them into the AWS console
# search to see each resource. Outputs are how Terraform surfaces useful
# results from the infrastructure it manages.
# ============================================================

output "vpc_id" {
  description = "ID of the created VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "Address space of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "subnet_id" {
  description = "ID of the public subnet"
  value       = aws_subnet.public.id
}

output "internet_gateway_id" {
  description = "ID of the internet gateway"
  value       = aws_internet_gateway.main.id
}

output "route_table_id" {
  description = "ID of the public route table"
  value       = aws_route_table.public.id
}
