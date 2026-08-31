output "staging_host_id" {
  value = hcloud_server.stage6.id
}

output "staging_host_name" {
  value = hcloud_server.stage6.name
}

output "staging_host_ipv4" {
  value = hcloud_server.stage6.ipv4_address
}

output "staging_host_private_ip" {
  value = hcloud_server_network.stage6.ip
}

output "staging_firewall_id" {
  value = hcloud_firewall.stage6.id
}

output "staging_network_id" {
  value = hcloud_server_network.stage6.network_id
}
