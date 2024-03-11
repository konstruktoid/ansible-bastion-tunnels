# Using Azure Bastion tunnels with Ansible

This script provides concept functionality for managing [Ansible](https://www.ansible.com/)
connections through Microsoft Azure [Bastion tunnels](https://learn.microsoft.com/en-us/azure/bastion/).

It allows users to generate an inventory of Azure hosts and their connection
details, as well as list the tunnel processes for the current user.

The script requires the [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/)
to be installed and the user to have appropriate Azure CLI credentials.

On Azure; create a Resource Group, add a VM and the Bastion service in the
created Resource Group.

Note that Bastion Host SKU must be Standard and Native Client
(`enable_tunneling` if using the SDK) must be enabled.

Update the script configuration file.

```
bastion_tunnels_inventory.py [-h] [-c CONFIG_FILE] [-l] [-t]

Ansible connections through Microsoft Azure Bastion tunnels.

options:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        Config file
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
      ansible_port: 63933
      ansible_user: azureuser
      resource_group: AnsibleHosts
    server02:
      ansible_port: 63932
      resource_group: AnsibleHosts
```

## Example

```
$ ansible-inventory -i bastion_tunnels_inventory.py --list --yaml
all:
  children:
    bastion_tunnels:
      hosts:
        server01:
          ansible_host: 127.0.0.1
          ansible_port: 63933
          ansible_user: azureuser
        server02:
          ansible_host: 127.0.0.1
          ansible_port: 63932
```

```sh
$ ansible -i bastion_tunnels_inventory.py -m ping all
server01 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3"
    },
    "changed": false,
    "ping": "pong"
}
server02 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3"
    },
    "changed": false,
    "ping": "pong"
}
```
