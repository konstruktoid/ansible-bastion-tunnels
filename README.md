# Using Azure Bastion tunnels with Ansible

This script provides concept functionality for managing [Ansible](https://www.ansible.com/)
connections through Microsoft Azure [Bastion tunnels](https://learn.microsoft.com/en-us/azure/bastion/).

It allows users to generate an inventory of Azure hosts and their connection
details, as well as list the tunnel processes for the current user.

The script requires the [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/)
with the `bastion` extension to be installed and the user to have appropriate
Azure CLI credentials.

On Azure; create a Resource Group, add the Bastion service and a VM in the
created Resource Group and ensure the VM is connected to the Bastion network.

> Note that the Bastion Host SKU must be Standard and `Native Client`
> (`enable_tunneling` if using the SDK) must be enabled, see [Configure Bastion for native client connections](https://learn.microsoft.com/en-us/azure/bastion/native-client).

> Note that you manually have to stop the tunnel processes when they are no longer needed,
> see [https://github.com/Azure/azure-cli-extensions/issues/7450](https://github.com/Azure/azure-cli-extensions/issues/7450).
> The script lists the tunnel processes for the current user with the `--list-tunnels` option.

## Usage

```
usage: bastion_tunnels_inventory.py [-h] [-c CONFIG_FILE] [-k] [-l] [-t]

Ansible connections through Microsoft Azure Bastion tunnels.

options:
  -h, --help            show this help message and exit
  -c, --config-file CONFIG_FILE
                        Config file
  -k, --kill-tunnels    Kill all active tunnel processes
  -l, --list            Print the inventory
  -t, --list-tunnels    List tunnel processes
```

## Configuration

In the configuration file, `ansible_bastion_tunnels.yml` by default,
`ansible_port` and `resource_group` are required.

`ansible_port` is the port number the Bastion tunnel will listen on.

`resource_group` is the Azure resource group the Bastion service and
VM are located in.


```yaml
---
bastion_tunnels:
  hosts:
    server01:
      ansible_host: 127.0.0.1
      ansible_port: 63931
      ansible_user: azureuser
      resource_group: AnsibleHosts
    server02:
      ansible_host: 127.0.0.1
      ansible_port: 63932
      ansible_user: azureuser
      resource_group: AnsibleHosts
```

## Examples

```
$ ansible-inventory -i bastion_tunnels_inventory.py --list
{
    "_meta": {
        "hostvars": {
            "server01": {
                "ansible_host": "127.0.0.1",
                "ansible_port": 63931,
                "ansible_user": "azureuser",
                "resource_group": "AnsibleHosts"
            },
            "server02": {
                "ansible_host": "127.0.0.1",
                "ansible_port": 63932,
                "ansible_user": "azureuser",
                "resource_group": "AnsibleHosts"
            }
        },
        "profile": "inventory_legacy"
    },
    "all": {
        "children": [
            "ungrouped",
            "bastion_tunnels"
        ]
    },
    "bastion_tunnels": {
        "hosts": [
            "server01",
            "server02"
        ]
    }
}
```

```sh
$ ansible -i bastion_tunnels_inventory.py -m ping all
server01 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.10"
    },
    "changed": false,
    "ping": "pong"
}
server02 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.10"
    },
    "changed": false,
    "ping": "pong"
}
```

```sh
$ ansible-playbook -i bastion_tunnels_inventory.py test.yml
PLAY [Azure Bastion Test Playbook] *********************************************

TASK [Gathering Facts] *********************************************************
ok: [server01]
ok: [server02]

TASK [Return host information] *************************************************
ok: [server01] => {
    "msg": "Hostname is server01.internal.cloudapp.net with ip 10.1.1.4"
}
ok: [server02] => {
    "msg": "Hostname is server02.internal.cloudapp.net with ip 10.1.1.5"
}
```
