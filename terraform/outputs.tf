output "monitor_public_ip" {
  value = aws_eip.monitor.public_ip
  description = "Elastic IP of monitor instance (static)"
}

output "web_public_ip" {
  value = aws_eip.web.public_ip
  description = "Elastic IP of web instance (static)"
}

output "core_public_ip" {
  value = aws_eip.core.public_ip
  description = "Elastic IP of core instance (static)"
}

output "monitor_private_ip" {
  value = aws_instance.monitor.private_ip
}

output "web_private_ip" {
  value = aws_instance.web.private_ip
}

output "core_private_ip" {
  value = aws_instance.core.private_ip
}

output "ssh_commands" {
  value = <<-EOT
  SSH monitor:
  ssh -i "${var.private_key_path}" ${var.ssh_user}@${aws_eip.monitor.public_ip}

  SSH web:
  ssh -i "${var.private_key_path}" ${var.ssh_user}@${aws_eip.web.public_ip}

  SSH core:
  ssh -i "${var.private_key_path}" ${var.ssh_user}@${aws_eip.core.public_ip}
  EOT
}

output "ansible_inventory" {
  value = <<-EOT
  [monitor]
  monitor-ai-01 ansible_host=${aws_eip.monitor.public_ip} ansible_user=${var.ssh_user}

  [web]
  bank-web-01 ansible_host=${aws_eip.web.public_ip} ansible_user=${var.ssh_user}

  [core]
  bank-core-01 ansible_host=${aws_eip.core.public_ip} ansible_user=${var.ssh_user}

  [app:children]
  web
  core

  [all:vars]
  ansible_python_interpreter=/usr/bin/python3
  ansible_ssh_private_key_file=${var.private_key_path}
  EOT
}

output "elastic_ips" {
  value = {
    monitor_eip = aws_eip.monitor.public_ip
    web_eip     = aws_eip.web.public_ip
    core_eip    = aws_eip.core.public_ip
  }
  description = "Elastic IPs (static public IPs) for each instance"
}

output "elastic_ips_info" {
  value = <<-EOT
  ✓ Elastic IPs have been allocated (Static Public IPs)
  
  Monitor: ${aws_eip.monitor.public_ip} (Allocation ID: ${aws_eip.monitor.id})
  Web:     ${aws_eip.web.public_ip} (Allocation ID: ${aws_eip.web.id})
  Core:    ${aws_eip.core.public_ip} (Allocation ID: ${aws_eip.core.id})
  
  Note: These IPs will NOT change when instances are stopped/started!
  EOT
}