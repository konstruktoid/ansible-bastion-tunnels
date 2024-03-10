#!/usr/bin/env python3
"""Provides functionality for managing Ansible connections through
Microsoft Azure Bastion tunnels.

It allows users to generate an inventory of Azure hosts and their connection
details, as well as list the tunnel processes for the current user.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

import psutil
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

RESOURCE_GROUP = "AnsibleHosts"
VM_NAME = "Server01"
PORT = 63933

az_command = shutil.which("az")
if az_command is None:
    print("The Azure CLI is not installed.")
    sys.exit(1)


def subscription_id() -> str:
    """Get the subscription ID from Azure CLI credentials."""
    credential = AzureCliCredential()
    subscription_client = SubscriptionClient(credential)
    sub_list = subscription_client.subscriptions.list()

    for group in list(sub_list):
        subscription_id = group.subscription_id

    return subscription_id


def resource_id(resource_group: str, vm_name: str) -> str:
    """Get the resource ID of a virtual machine."""
    client = ComputeManagementClient(
        credential=AzureCliCredential(),
        subscription_id=subscription_id(),
    )

    response = client.virtual_machines.get(
        resource_group_name=resource_group,
        vm_name=vm_name,
    )
    resource = response.as_dict()
    return resource["id"]


def bastion_name(resource_group: str) -> str:
    """Get the name of the Azure Bastion host."""
    client = NetworkManagementClient(
        credential=AzureCliCredential(),
        subscription_id=subscription_id(),
    )

    response = client.bastion_hosts.list_by_resource_group(
        resource_group_name=resource_group,
    )

    for item in response:
        bastion = item.as_dict()

    return bastion["name"]


def list_tunnels() -> str:
    """List the tunnel processes for the current user."""
    current_user = os.getlogin()

    for proc in psutil.process_iter():
        if proc.username == current_user:
            tunnel = [
                "network",
                "bastion",
                "tunnel",
                "--resource-group",
                "--target-resource-id",
            ]
            if all(cmdline in proc.cmdline() for cmdline in tunnel):
                print(f"Pid: {proc.pid} Process: {proc.cmdline()}")


def generate_inventory(
    resource_group: str,
    vm_name: str,
    bastion_name: str,
    resource_id: str,
    port: int,
) -> dict:
    """Generate the inventory."""
    command = [
        az_command,
        "network",
        "bastion",
        "tunnel",
        "--name",
        bastion_name,
        "--resource-group",
        resource_group,
        "--target-resource-id",
        resource_id,
        "--resource-port",
        "22",
        "--port",
        str(port),
    ]

    subprocess.Popen(
        command,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        shell=False,  # noqa: S603
    )

    name = f"{vm_name}"

    inventory = {}
    inventory["azure_hosts"] = []
    inventory["_meta"] = {}
    inventory["_meta"]["hostvars"] = {}
    inventory["azure_hosts"].append(name)
    inventory["_meta"]["hostvars"][name] = {}
    inventory["_meta"]["hostvars"][name]["ansible_host"] = "127.0.0.1"
    inventory["_meta"]["hostvars"][name]["ansible_user"] = "azureuser"
    inventory["_meta"]["hostvars"][name]["ansible_port"] = port

    return inventory


if not args.list_tunnels:

    credential = AzureCliCredential()
    try:
        credential.get_token("https://management.azure.com/.default")
    except CredentialUnavailableError:
        sys.exit(1)

    BASTION_NAME = bastion_name(RESOURCE_GROUP)
    RESOURCE_ID = resource_id(RESOURCE_GROUP, VM_NAME)
    inventory = generate_inventory(
        RESOURCE_GROUP,
        VM_NAME,
        BASTION_NAME,
        RESOURCE_ID,
        PORT,
    )

    if args.list:
        json_output = json.dumps(inventory, sort_keys=True, indent=2)
    else:
        json_output = json.dumps(inventory, sort_keys=True)

    print(json_output)

if args.list_tunnels:
    list_tunnels()
