import os
import time
import sys

from kubernetes.client.rest import ApiException
from vsclient import VSClient

name = 'my-virtual-server'
namespace = os.environ.get('NAMESPACE', 'default')
username = os.environ.get('USERNAME')
password = os.environ.get('PASSWORD')

if username == None or password == None:
    print('USERNAME and PASSWORD environment variables are required')
    sys.exit()

my_virtualserver = {
    'apiVersion': f'{VSClient.GROUP}/{VSClient.VERSION}',
    'kind': 'VirtualServer',
    'metadata': {
      'name': name,
      'namespace': namespace,
      'annotations': {
        'external-dns.alpha.kubernetes.io/hostname': 'my-virtual-server.tenant-palatial-platform.coreweave.cloud'
      }
    },
    'spec': {
        'region': 'LGA1',  # ord1, ewr1, ewr2
        'os': {
            'enableUEFIBoot': False,
            'type': 'windows',
        },
        'resources': {
            'gpu': {
                'type': 'Quadro_RTX_4000',
                'count': 1
            },
            'cpu': {
                # GPU type and CPU type are mutually exclusive i.e. CPU type cannot be specified when GPU type is selected.
                # CPU is selected automatically based on GPU type.
                # 'type': 'amd-epyc-rome',
                'count': 4,
            },
            'memory': '32Gi'
        },
        # Add user
        # SSH public key is optional and allows to login without a password
        # Public key is located in $HOME/.ssh/id_rsa.pub
        # publicKey = `ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDEQCQpab6UWuA ... user@hostname`
        'users': [
            {
                'username': 'david',
                'sshpublickey': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDM/yQjHqoptqGIdndFkgCGCukjUzxLMziX09x0Q+ltJXlj1oeBSA9VYS8lHVSRW6gVNlMcYxnwl0zAy/HiUUxU8G2x0B8/JwHf7Ax0djHzwtFH2y3MIxdEjZZ+LRxwHGFSeGOhKOFDq3xqTSqtLNxEiWfPMp9kPKz8moIXAd31Wzzum/c5V6pkRacIIk4FWuS8DhU45LL7ylYzkLZPKmrHnI1U/h2eX9VK+gdoDRba1k6x0SWD5EKOwr5+ZFyTc97wCtYZY4XE3pOyeYe+h2je4ET5XlKf9fm1rkbw2X0GYW5bpE8oI1r0cWjUz4ogmGh7wvubD8uOZ1zPKZdXQKO6dmNDrOhq7R3ZwuBqqEsS0+287vLbKuecY/Y7f1rnyXRNA+ohrORzSrQKIJZon0T9jqXKywtI01Al0Ju3FXNNWJ6C57IQZ0hxxMeAdBaC0a+mMtErHp/11bXsCnFgJQfnwa6XIAtLAknooQwM+zlFnxX06LsFRYQCqfizc/8tums= employee@MSI'
            }
        ],
        # Add cloud config
        # more examples on https://cloudinit.readthedocs.io/en/latest/topics/examples.html
        'cloudInit': """
# Update packages
package_update: true
# Install packages
packages:
  - curl
  - git
# Run additional commands
runcmd:
  - [df, -h]
  - [git, version]
  - [curl, --version ]
""",
        'storage': {
            'root': {
                'size': '821Gi',
                'source': {
                    'pvc': {
                        'name': 'win10-master-20230627-lga1',
                        'namespace': 'vd-images'
                    }
                },
                'storageClassName': 'block-nvme-lga1',
                'volumeMode': 'Block',
                'accessMode': 'ReadWriteOnce',
                'source': {
                  'pvc': {
                    'name': 'new-2761',
                    'namespace': 'tenant-palatial-platform'
                  }
                }
            },
          'filesystems': [{
            'name': 'ue5storagehub',
            'spec': {
              'persistentVolumeClaim': {
                'claimName': 'ue5storagehub'
              }
            }
          }]
        },
        'network': {
             'public': True,
             'directAttachLoadBalancerIP': True
#            'tcp': {
#                'ports': [22, 443, 60443, 4172, 3389]
#            },
#            'udp': {
#                'ports': [4172, 3389]
#            }
        },
        'initializeRunning': True
    }
}


vsclient = VSClient()

try:
    vsclient.delete(namespace, name)
except ApiException as e:
    if e.status == 404:
        print(f'VirtualServer {name} in namespace {namespace} already deleted')
    else:
        print(f'VirtualServer delete exception {e}')
        exit(1)

# Create virtual server
import json

print(vsclient.create(my_virtualserver))

print(f'VirtualServer status: {vsclient.ready(namespace, name)}')

# Stop the Virtual Machine Instance to apply changes.
#print(vsclient.kubevirt_api.stop(namespace, name))
#print(f'VirtualServer status: {vsclient.ready(namespace, name, expected_state="Stopped")}')

# Update the manifest and attach directly to Load Balancer
#my_virtualserver['spec']['network']['tcp']['ports'] = []
#my_virtualserver['spec']['network']['udp']['ports'] = []
#my_virtualserver['spec']['network']['directAttachLoadBalancerIP'] = True
#print(vsclient.update(my_virtualserver))

#print(vsclient.kubevirt_api.start(namespace, name))
#print(f'VirtualServer status: {vsclient.ready(namespace, name)}')

# Delete virtual server
#vsclient.delete(namespace, name)

exit(0)
