# -*- coding: utf-8 -*-

# Automatic provisioning of a Hetzner Cloud Server instance.

import os
import time

import hcloud
from hcloud import Client
from hcloud.images import BoundImage
from hcloud.locations import BoundLocation
from hcloud.ssh_keys.client import BoundSSHKey
from hcloud.servers.client import BoundServer
from hcloud.server_types.client import BoundServerType
from hcloud.actions.client import BoundAction

from nixops import known_hosts
from nixops.deployment import Deployment
from nixops.util import attr_property, create_key_pair
from nixops.nix_expr import RawValue
from nixops.backends import MachineDefinition, MachineState
from nixops.resources import ResourceEval

import nixops_hetznercloud.resources
from nixops_hetznercloud.resources.hetznercloud_common import HetznerCloudCommonState

from typing import Optional, List

from .options import HetznerCloudMachineOptions


INFECT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "nixos-infect")
)


class HetznerCloudDefinition(MachineDefinition):
    """
    Definition of a Hetzner Cloud machine.
    """

    config: HetznerCloudMachineOptions

    @classmethod
    def get_type(cls):
        return "hetznercloud"

    def __init__(self, name: str, config: ResourceEval):
        super().__init__(name, config)

        self.api_token = self.config.hetznerCloud.apiToken
        self.location = self.config.hetznerCloud.location
        self.server_type = self.config.hetznerCloud.serverType
        #        self.networks = self.config.hetznerCloud.networks
        #        self.ip_address = self.config.hetznerCloud.ipAddress
        #        self.ssh_keys = self.config.hetznerCloud.sshKeys
        #        self.block_device_mapping = {
        #            k: dict(v) for k, v in self.config.hetznerCloud.blockDeviceMapping.items()
        #        }
        #        boot_devices: List[str] = [
        #            k for k, v in self.block_device_mapping.items() if v["bootDisk"]
        #        ]
        #        if len(boot_devices) == 0:
        #            raise Exception("machine {0} must have a boot device.".format(self.name))
        #        if len(boot_devices) > 1:
        #            raise Exception(
        #                "machine {0} must have exactly one boot device.".format(self.name)
        #            )
        self.labels = dict(self.config.hetznerCloud.labels)

    def show_type(self):
        return "{0} [{1}]".format(self.get_type(), self.location or "???")


class HetznerCloudState(MachineState[HetznerCloudDefinition], HetznerCloudCommonState):
    """
    State of a Hetzner Cloud machine.
    """

    @classmethod
    def get_type(cls):
        return "hetznercloud"

    state = attr_property("state", MachineState.MISSING, int)  # override
    api_token = attr_property("hetznerCloud.apiToken", None)

    server_id = attr_property("serverId", None, int)
    public_ipv4 = attr_property("publicIpv4", None)
    public_ipv6 = attr_property("publicIpv6", None)
    private_ipv4 = attr_property("privateIpv4", None)

    public_client_key = attr_property("hetznerCloud.publicClientKey", None)
    private_client_key = attr_property("hetznerCloud.privateClientKey", None)

    public_host_key = attr_property("hetznerCloud.publicHostKey", None)
    private_host_key = attr_property("hetznerCloud.privateHostKey", None)

    location = attr_property("hetznerCloud.location", None)
    server_type = attr_property("hetznerCloud.serverType", None)

    #    block_device_mapping = attr_property("hetznerCloud.blockDeviceMapping", {}, "json")
    #    networks = attr_property("hetznerCloud.networks", None)
    #    ip_address = attr_property("hetznerCloud.ipAddress", None)
    #    ssh_keys = attr_property("hetznerCloud.sshKeys", None)

    def __init__(self, depl: Deployment, name: str, id):
        MachineState.__init__(self, depl, name, id)
        self._client = None

    def cleanup_state(self):
        """ Discard all state pertaining to an instance. """
        with self.depl._db:
            self.server_id = None
            self.public_ipv4 = None
            self.public_ipv6 = None
            
            self.private_client_key = None
            self.public_client_key = None
            self.private_host_key = None
            self.public_host_key = None

            self.location = None
            self.server_type = None

    #            self.blockDeviceMapping = None
    #            self.ip_address = None
    #            self.networks = None
    #            self.ssh_keys = None

    def show_type(self):
        s = super(HetznerCloudState, self).show_type()
        if self.location:
            s = "{0} [{1}; {2}]".format(s, self.location, self.server_type)
        return s

    @property
    def resource_id(self) -> Optional[str]:
        return self.server_id

    @property
    def full_name(self) -> str:
        return "Hetzner Cloud Server '{0}'".format(self.name)

    def _get_instance(self) -> BoundServer:
        return self.get_client().servers.get_by_id(self.resource_id)

    def get_client(self) -> Client:
        """
        Generic method to get or create a Hetzner Cloud client.
        """
        if self._client:
            return self._client

        new_api_token = self.api_token or os.environ.get("HCLOUD_API_TOKEN")
        if new_api_token is not None:
            self.api_token = new_api_token
        else:
            raise Exception("please set ‘apiToken’ or $HCLOUD_API_TOKEN")

        self._client = Client(token=self.api_token)
        return self._client

    def get_ssh_name(self) -> str:
        if not self.public_ipv4:
            raise Exception(
                "{0} does not have a public IP address (yet)".format(self.full_name)
            )
        return self.public_ipv4

    def get_ssh_private_key_file(self):
        return self._ssh_private_key_file or self.write_ssh_private_key(
            self.private_client_key
        )

    def get_ssh_flags(self, *args, **kwargs) -> List[str]:
        super_flags = super(HetznerCloudState, self).get_ssh_flags(*args, **kwargs)
        return super_flags + [
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            "StrictHostKeyChecking=no",
            "-i",
            self.get_ssh_private_key_file(),
        ]

    def get_physical_spec(self):
        return {
            "imports": [RawValue("<nixpkgs/nixos/modules/profiles/qemu-guest.nix>")],
            ("boot", "loader", "grub", "device"): "nodev",
            ("fileSystems", "/"): {"device": "/dev/sda1", "fsType": "ext4"},
            ("users", "extraUsers", "root", "openssh", "authorizedKeys", "keys"): [
                self.public_client_key
            ],
        }

    #    def get_ssh_public_keys(self):
    #        bound_keys = []
    #        for key_name in self.ssh_keys:
    #            bound_keys.append(self.get_client().ssh-keys.get_by_name(key_name))
    #        return bound_keys

    #    def attach_volume(self):
    #        pass

    #    def attach_server_network(self):
    #        pass

    #    def assign_floating_ip(self):
    #        pass

    #    def update_block_device_mapping(self):
    #        pass

    def create_after(self, resources, defn):# -> Dict[str, HetznerCloudCommonState]:
        print(type(resources))
        return {
            r
            for r in resources
            if isinstance(
                r, nixops_hetznercloud.resources.ssh_key.HetznerCloudSSHKeyState
            )
            or isinstance(
                r, nixops_hetznercloud.resources.floating_ip.HetznerCloudFloatingIPState
            )
            or isinstance(
                r, nixops_hetznercloud.resources.network.HetznerCloudNetworkState
            )
            or isinstance(
                r, nixops_hetznercloud.resources.volume.HetznerCloudVolumeState
            )
        }

    def _create_ssh_key(self, public_key) -> BoundSSHKey:
        """Create or get a hetzner cloud ssh key."""
        public_key = public_key.strip()
        hetzner_ssh_keys: List[BoundSSHKey] = self.get_client().ssh_keys.get_all()
        name = "nixops-{0}-{1}".format(self.depl.uuid, self.name)
        for key in hetzner_ssh_keys:
            if key.public_key.strip() == public_key:
                return key
            elif key.name == name:
                self.get_client().ssh_keys.delete(key)
        ssh_key: BoundSSHKey = self.get_client().ssh_keys.create(
            name=name, public_key=public_key,
        )
        return ssh_key

    def create(self, defn: HetznerCloudDefinition, check, allow_reboot, allow_recreate) -> None:

        self.api_token = defn.api_token

        if self.state != self.UP:
            check = True

        self.set_common_state(defn)

        if self.resource_id is not None:
            return

        # create ssh keypairs

        if not self.public_client_key:
            (private, public) = create_key_pair()
            self.public_client_key = public
            self.private_client_key = private

        if not self.public_host_key:
            (private, public) = create_key_pair(type="ed25519")
            self.public_host_key = public
            self.private_host_key = private

        location: BoundLocation = self.get_client().locations.get_by_name(defn.location)
        server_type: BoundServerType = self.get_client().server_types.get_by_name(defn.server_type)
        ssh_key: BoundSSHKey = self._create_ssh_key(self.public_client_key)
        image: BoundImage = self.get_client().images.get_by_name("ubuntu-18.04") # for lustration
        user_data = (
            '''
            #cloud-config
              ssh_keys:
                ed25519_public: | {0}
                ed25519_private: | {1}
              ssh_authorized_keys:
                - {2}
            '''.format(
                self.public_host_key,
                self.private_host_key.replace("\n", "|"),
                self.public_client_key
            )
        )

        self.logger.log_start(
            "creating {0} server at {1}...".format(
                server_type.name, location.description
            )
        )
        response = self.get_client().servers.create(
            name=self.name,
            labels={**self.get_common_labels(), **dict(defn.labels)},
            location=location,
            server_type=server_type,
            ssh_keys=[ssh_key],
            user_data=user_data,
            image=image,
            start_after_create=True,
        )

        self.state = self.STARTING
        self.wait_on_action(response.action)

        # store instance state

        with self.depl._db:
            self.server_id = response.server.id
            self.public_ipv4 = response.server.public_net.ipv4.ip
            self.public_ipv6 = response.server.public_net.ipv6.ip

            self.server_type = defn.server_type
            self.location = defn.location
            self.labels = defn.labels

            # self.ip_address = defn.ip_address
            # self.networks = defn.networks
            # self.ssh_keys = defn.ssh-keys

        self.logger.log_end("{0}".format(self.public_ipv4))
#        known_hosts.add(self.public_ipv4, self.public_host_key)
        self.wait_for_ssh()
        self.logger.log_start("running nixos-infect")
        self.run_command('bash </dev/stdin 2>&1', stdin=open(INFECT_PATH))
        self.reboot_sync()
        self.state = self.UP

    def _destroy(self) -> None:
        if self.state != self.UP:
            return
        self.logger.log("destroying {0}...".format(self.full_name))
        try:
            self.get_client().servers.get_by_id(self.resource_id).delete()
        except hcloud.APIException as e:
            if e.code == "not_found":
                self.warn("{0} was already deleted".format(self.full_name))
            else:
                raise e
        # known_hosts.remove(self.public_ipv4, self.public_host_key)
        self.cleanup_state()

    def destroy(self, wipe=False) -> bool:
        question = "are you sure you want to destroy {0}?"
        if not self.depl.logger.confirm(question.format(self.full_name)):
            return False

        self._destroy()
        return True

    def start(self) -> None:
        instance = self._get_instance()
        self.logger.log("powering on {0}...".format(self.full_name))
        self.wait_on_action(self.get_client().servers.power_on(instance))
        self.wait_for_ssh()
        self.state = self.STARTING

    def stop(self) -> None:
        instance = self._get_instance()
        self.logger.log(
            "sending ACPI shutdown request to {0}...".format(self.full_name)
        )
        self.wait_on_action(self.get_client().servers.shutdown(instance))
        self.state = self.STOPPED

    def reboot(self, hard=False) -> None:
        instance = self._get_instance()
        if hard:
            self.logger.log("sending hard reset to {0}...".format(self.full_name))
            self.wait_on_action(self.get_client().servers.reset(instance))
            self.wait_for_ssh()
            self.state = self.STARTING
        else:
            self.logger.log(
                "sending ACPI reboot request to {0}...".format(self.full_name)
            )
            self.wait_on_action(self.get_client().servers.reboot(instance))
            self.wait_for_ssh()
            self.state = self.STARTING

    def _check(self):
        pass

    def wait_on_action(self, action: BoundAction) -> None:
        while action.status == "running":
            self.logger.log_continue(".")
            time.sleep(1)
            action = self.get_client().actions.get_by_id(action.id)
        if action.status != "success":
            raise Exception("unexpected status: {0}".format(action.status))
