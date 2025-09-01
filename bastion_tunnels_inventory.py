#!/usr/bin/env python3
"""Provides functionality for managing connections through Azure Bastion tunnels.

It allows users to generate an inventory of Azure hosts and their connection
details, as well as list the tunnel processes for the current user.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import psutil
import yaml
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import AzureCliCredential, CredentialUnavailableError
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.subscription import SubscriptionClient

try:
    import json
except ImportError:
    import simplejson as json

parser = argparse.ArgumentParser(
    description="Ansible connections through Microsoft Azure Bastion tunnels.",
)

parser.add_argument(
    "-c",
    "--config-file",
    help="Config file",
    default="ansible_bastion_tunnels.yml",
)

parser.add_argument(
    "-k",
    "--kill-tunnels",
    help="Kill all active tunnel processes",
    action="store_true",
)

parser.add_argument(
    "-l",
    "--list",
    help="Print the inventory",
    action="store_true",
)

parser.add_argument(
    "-t",
    "--list-tunnels",
    help="List tunnel processes",
    action="store_true",
)

args = parser.parse_args()

az_command = shutil.which("az")
if az_command is None:
    print("The Azure CLI is not installed.")
    sys.exit(1)


def check_extension() -> bool:
    """Check if the Azure CLI bastion extension is installed."""
    command = [az_command, "extension", "list"]
    try:
        output = subprocess.check_output(command, text=True)
        extensions = json.loads(output)
        for ext in extensions:
            if ext["name"] == "bastion":
                return True
        return False
    except subprocess.CalledProcessError:
        return False


def list_tunnels() -> list[str]:
    """List the tunnel processes for the current user."""
    tunnel_processes = []

    for proc in psutil.process_iter():
        tunnel = [
            "network",
            "bastion",
            "tunnel",
            "--resource-group",
            "--target-resource-id",
        ]

        if all(cmdline in proc.cmdline() for cmdline in tunnel):
            tunnel_processes.append(
                json.dumps(
                    {
                        "pid": proc.pid,
                        "cmdline": proc.cmdline(),
                        "status": proc.status(),
                    }
                )
            )

    return tunnel_processes


def generate_inventory(config: dict) -> dict:
    """Generate the inventory."""
    group_name = list(config.keys())[0]

    inventory = {}
    inventory[group_name] = []
    inventory["_meta"] = {}
    inventory["_meta"]["hostvars"] = {}
    inventory[group_name] = {"hosts": []}

    for host, value in config[group_name]["hosts"].items():
        if bastion_name(value["resource_group"]) is None:
            print(
                f"A valid bastion host was not found in resource group {value['resource_group']}.",
            )
            sys.exit(1)
        else:
            bastion = bastion_name(value["resource_group"])

        if resource_id(value["resource_group"], host) is None:
            pass
        else:
            target_id = resource_id(value["resource_group"], host)

            command = [
                az_command,
                "network",
                "bastion",
                "tunnel",
                "--name",
                bastion,
                "--resource-group",
                value["resource_group"],
                "--target-resource-id",
                target_id,
                "--resource-port",
                "22",
                "--port",
                str(value["ansible_port"]),
            ]

            subprocess.Popen(
                command,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                shell=False,
            )

            inventory[group_name]["hosts"].append(host)

            inventory["_meta"]["hostvars"][host] = {}

            for var, var_value in value.items():
                inventory["_meta"]["hostvars"][host][var] = var_value

    return inventory


def subscription_id() -> str:
    """Get the subscription ID from Azure CLI credentials."""
    credential = AzureCliCredential()
    subscription_client = SubscriptionClient(credential)
    sub_list = subscription_client.subscriptions.list()

    for group in list(sub_list):
        subscription_id = group.subscription_id

    return subscription_id


def resource_id(resource_group: str, vm_name: str) -> str | None:
    """Get the resource ID of a virtual machine."""
    client = ComputeManagementClient(
        credential=AzureCliCredential(),
        subscription_id=subscription_id(),
    )

    try:
        response = client.virtual_machines.get(
            resource_group_name=resource_group,
            vm_name=vm_name,
        )
    except ResourceNotFoundError:
        return None

    resource = response.as_dict()
    return resource["id"]


def bastion_name(resource_group: str) -> str | None:
    """Get the name of the Azure Bastion host."""
    bastion = None

    client = NetworkManagementClient(
        credential=AzureCliCredential(),
        subscription_id=subscription_id(),
    )

    response = client.bastion_hosts.list_by_resource_group(
        resource_group_name=resource_group,
    )

    for item in response:
        bastion = item.name

        if item.enable_tunneling is False:
            return None

    return bastion


if not args.list_tunnels and not args.kill_tunnels:
    if check_extension() is False:
        print("The Azure CLI bastion extension is not installed.")
        sys.exit(1)

    credential = AzureCliCredential()
    try:
        credential.get_token("https://management.azure.com/.default")
    except CredentialUnavailableError:
        sys.exit(1)

    with Path(args.config_file).open("r") as read_config:
        if not read_config:
            print(f"Config file {args.config_file} not found.")
            sys.exit(1)
        else:
            config = yaml.safe_load(read_config)

    inventory = generate_inventory(config)

    if args.list:
        json_output = json.dumps(inventory, sort_keys=True, indent=2)
    else:
        json_output = json.dumps(inventory, sort_keys=True)

    print(json_output)

if args.list_tunnels:
    if len(list_tunnels()) > 0:
        for t in range(len(list_tunnels())):
            print(list_tunnels()[t])
    else:
        print("No active tunnels found.")

if args.kill_tunnels:
    tunnel_pids = []
    for t in range(len(list_tunnels())):
        pid = tunnel_pids.append(json.loads(list_tunnels()[t])["pid"])

    if len(tunnel_pids) > 0:
        for tunnel_pid in tunnel_pids:
            process = psutil.Process(tunnel_pid)
            process.terminate()
            print(f"Terminated tunnel process with PID {tunnel_pid}.")
    else:
        print("No active tunnels found.")
