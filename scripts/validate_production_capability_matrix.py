#!/usr/bin/env python3
import pathlib
import yaml

matrix = yaml.safe_load(pathlib.Path("PRODUCTION-SAFETY-CAPABILITY-MATRIX.yaml").read_text())
inventory = {line for line in pathlib.Path("PRODUCTION-WORKLOAD-INVENTORY-20260901.txt").read_text().splitlines() if line}
services = matrix["services"]
keys = {"advertising_write", "external_delivery", "social_publish", "external_model_call", "sms_delivery", "email_delivery", "pstn_dialing", "n8n_provider_write"}
assert len(inventory) == 64
assert set(services) == inventory
assert matrix["coverage"] == "64/64"
unknown = 0
for name, item in services.items():
    assert set(item["capabilities"]) == keys, name
    for value in item["capabilities"].values():
        assert value in (True, False, "UNKNOWN"), (name, value)
        unknown += value == "UNKNOWN"
assert unknown == 40, unknown
print("CAPABILITY_MATRIX_COVERAGE=64/64")
print("CAPABILITY_UNKNOWN_FIELDS=40")
