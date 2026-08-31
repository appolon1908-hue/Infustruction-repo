locals {
  name = "codestra-stage6-staging-01"
  labels = {
    environment = "staging"
    role        = "stage6-runtime"
    production  = "false"
    klyrow      = "false"
    postal      = "false"
    managed-by  = "opentofu"
  }
}

resource "hcloud_firewall" "stage6" {
  name   = "${local.name}-deny-default"
  labels = local.labels

  rule {
    direction   = "in"
    protocol    = "tcp"
    port        = "22"
    source_ips  = sort(tolist(var.approved_ssh_source_cidrs))
    description = "SSH from approved operator or VPN ranges only"
  }

  rule {
    direction   = "in"
    protocol    = "icmp"
    source_ips  = sort(tolist(var.approved_private_cidrs))
    description = "Private-network diagnostics only"
  }

  rule {
    direction       = "out"
    protocol        = "tcp"
    port            = "443"
    destination_ips = sort(tolist(setunion(var.approved_private_cidrs, var.approved_bootstrap_egress_cidrs)))
    description     = "Approved staging services, signed package sources, GitHub and GHCR"
  }

  rule {
    direction       = "out"
    protocol        = "tcp"
    port            = "80"
    destination_ips = sort(tolist(var.approved_bootstrap_egress_cidrs))
    description     = "Approved signed package mirrors only"
  }

  rule {
    direction       = "out"
    protocol        = "tcp"
    port            = "53"
    destination_ips = sort(tolist(var.dns_resolver_cidrs))
    description     = "Approved DNS resolvers"
  }

  rule {
    direction       = "out"
    protocol        = "udp"
    port            = "53"
    destination_ips = sort(tolist(var.dns_resolver_cidrs))
    description     = "Approved DNS resolvers"
  }

  rule {
    direction       = "out"
    protocol        = "udp"
    port            = "123"
    destination_ips = sort(tolist(var.ntp_server_cidrs))
    description     = "Approved NTP servers"
  }

  rule {
    direction       = "out"
    protocol        = "tcp"
    port            = "1-65535"
    destination_ips = sort(tolist(var.approved_private_cidrs))
    description     = "Approved staging-private dependencies only"
  }
}

resource "hcloud_server" "stage6" {
  name               = local.name
  server_type        = var.server_type
  image              = var.image
  location           = var.location
  ssh_keys           = sort(tolist(var.approved_ssh_key_ids))
  labels             = local.labels
  backups            = true
  keep_disk          = true
  delete_protection  = true
  rebuild_protection = true
  user_data          = file("${path.module}/cloud-init.yaml")
  firewall_ids       = [hcloud_firewall.stage6.id]

  public_net {
    ipv4_enabled = true
    ipv6_enabled = false
  }

  lifecycle {
    prevent_destroy = true
    precondition {
      condition     = !contains(var.approved_ssh_source_cidrs, "0.0.0.0/0")
      error_message = "Global SSH exposure is forbidden."
    }
    precondition {
      condition     = !contains(var.approved_bootstrap_egress_cidrs, "0.0.0.0/0")
      error_message = "Global bootstrap egress is forbidden."
    }
  }
}

resource "hcloud_server_network" "stage6" {
  server_id  = hcloud_server.stage6.id
  network_id = var.private_network_id
  ip         = var.private_ip
}
