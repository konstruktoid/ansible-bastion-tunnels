# ansible-bastion-tunnels

This script provides functionality for managing [Ansible](https://www.ansible.com/)
connections through Microsoft Azure [Bastion tunnels](https://learn.microsoft.com/en-us/azure/bastion/).

It allows users to generate an inventory of Azure hosts and their connection
details, as well as list the tunnel processes for the current user.

The script requires the [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/)
to be installed and the user to have appropriate Azure CLI credentials.

## Note

Currently, the script has the following assumptions:
- the Azure resources are located in the 'AnsibleHosts' resource group.
- the target virtual machine is named 'Server01' and uses port 63933 for the tunnel.
- the Azure Bastion host is present in the same resource group as the target virtual machine.
- the Azure CLI is installed and the user has appropriate Azure CLI credentials.

## Usage

```py
python3 bastion_tunnels_inventory.py [-l] [-t]
```

### Options

```
    -h, --help          Show this help message and exit
    -l, --list          Print the inventory
    -t, --list-tunnels  List tunnel processes
```

## Example

`python bastion_tunnels_inventory.py --list`

