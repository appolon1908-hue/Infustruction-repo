variable "location" {
  description = "Hetzner location containing the approved private staging network."
  type        = string
  validation {
    condition     = contains(["fsn1", "nbg1", "hel1"], var.location)
    error_message = "Stage 6 must use an approved EU Hetzner location."
  }
}

variable "server_type" {
  description = "Reviewed minimum size for 22 workloads, migrations, and monitoring agents."
  type        = string
  default     = "cx43"
  validation {
    condition     = var.server_type == "cx43"
    error_message = "Changing the reviewed CX43 size requires a new sizing review."
  }
}

variable "image" {
  description = "Approved Ubuntu image or immutable snapshot identifier."
  type        = string
  default     = "ubuntu-24.04"
  validation {
    condition     = var.image == "ubuntu-24.04" || can(regex("^[0-9]+$", var.image))
    error_message = "Use Ubuntu 24.04 or a reviewed numeric snapshot identifier."
  }
}

variable "private_network_id" {
  description = "Existing approved Hetzner private-network ID."
  type        = number
  validation {
    condition     = var.private_network_id > 0
    error_message = "An existing private-network ID is required."
  }
}

variable "private_ip" {
  description = "Unused IP in the approved staging subnet; never a production address."
  type        = string
  validation {
    condition     = can(cidrhost("10.0.0.0/8", 1)) && can(regex("^10\\.", var.private_ip))
    error_message = "The staging private IP must be in RFC1918 10/8 space."
  }
}

variable "approved_ssh_key_ids" {
  description = "Existing Hetzner SSH-key IDs approved for Stage 6 operators."
  type        = set(number)
  validation {
    condition     = length(var.approved_ssh_key_ids) > 0 && alltrue([for id in var.approved_ssh_key_ids : id > 0])
    error_message = "At least one existing approved Hetzner SSH key is required."
  }
}

variable "approved_ssh_source_cidrs" {
  description = "Narrow operator or VPN CIDRs allowed to reach SSH."
  type        = set(string)
  validation {
    condition = length(var.approved_ssh_source_cidrs) > 0 && alltrue([
      for cidr in var.approved_ssh_source_cidrs :
      can(cidrhost(cidr, 0)) && !contains(["0.0.0.0/0", "::/0"], cidr)
    ])
    error_message = "SSH requires explicit non-global approved source CIDRs."
  }
}

variable "approved_private_cidrs" {
  description = "Approved staging-only private service and observability CIDRs."
  type        = set(string)
  validation {
    condition = length(var.approved_private_cidrs) > 0 && alltrue([
      for cidr in var.approved_private_cidrs : can(regex("^10\\.", cidr))
    ])
    error_message = "Only explicit 10/8 staging-private CIDRs are accepted."
  }
}

variable "approved_bootstrap_egress_cidrs" {
  description = "Reviewed package-mirror, GitHub, GHCR, DNS and NTP CIDRs; production providers are forbidden."
  type        = set(string)
  validation {
    condition = length(var.approved_bootstrap_egress_cidrs) > 0 && alltrue([
      for cidr in var.approved_bootstrap_egress_cidrs :
      can(cidrhost(cidr, 0)) && !contains(["0.0.0.0/0", "::/0"], cidr)
    ])
    error_message = "Bootstrap egress must be a reviewed, non-global CIDR allowlist."
  }
}

variable "dns_resolver_cidrs" {
  description = "Approved recursive DNS resolver CIDRs."
  type        = set(string)
  validation {
    condition = length(var.dns_resolver_cidrs) > 0 && alltrue([
      for cidr in var.dns_resolver_cidrs :
      can(cidrhost(cidr, 0)) && !contains(["0.0.0.0/0", "::/0"], cidr)
    ])
    error_message = "DNS must use explicit approved resolver CIDRs."
  }
}

variable "ntp_server_cidrs" {
  description = "Approved NTP server CIDRs."
  type        = set(string)
  validation {
    condition = length(var.ntp_server_cidrs) > 0 && alltrue([
      for cidr in var.ntp_server_cidrs :
      can(cidrhost(cidr, 0)) && !contains(["0.0.0.0/0", "::/0"], cidr)
    ])
    error_message = "NTP must use explicit approved server CIDRs."
  }
}

variable "forbidden_production_cidrs" {
  description = "Reviewed Klyrow, Postal, SMTP/SMS/PSTN, social, advertising and model-provider production CIDRs."
  type        = set(string)
  validation {
    condition = length(var.forbidden_production_cidrs) > 0 && alltrue([
      for cidr in var.forbidden_production_cidrs : can(cidrhost(cidr, 0))
    ])
    error_message = "A nonempty reviewed production-provider CIDR deny inventory is required."
  }
}
