output "control_plane_public_ip" {
  value = aws_instance.control_plane.public_ip
}

output "worker_public_ips" {
  value = [for i in aws_instance.worker_nodes : i.public_ip]
}
