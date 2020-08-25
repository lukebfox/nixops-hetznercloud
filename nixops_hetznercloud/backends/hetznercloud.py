# -*- coding: utf-8 -*-

# Automatic provisioning of a Hetzner Cloud Server instance.

import os
import re
import time
import socket
import getpass

import hcloud
from hcloud import Client
from hcloud.images.client import BoundImage
from hcloud.locations.client import BoundLocation
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
from nixops_hetznercloud.hetznercloud_common import HetznerCloudResourceState

from typing import List
from typing import Dict
from typing import Set

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
        self.server_name = self.config.hetznerCloud.serverName
        self.server_type = self.config.hetznerCloud.serverType
        # self.networks = self.config.hetznerCloud.networks
        # self.ip_address = self.config.hetznerCloud.ipAddress
        # self.block_device_mapping = {
        #     k: dict(v) for k, v in self.config.hetznerCloud.blockDeviceMapping.items()
        # }
        # boot_devices: List[str] = [
        #     k for k, v in self.block_device_mapping.items() if v["bootDisk"]
        # ]
        # if len(boot_devices) == 0:
        #     raise Exception("machine {0} must have a boot device.".format(self.name))
        # if len(boot_devices) > 1:
        #     raise Exception(
        #         "machine {0} must have exactly one boot device.".format(self.name)
        #     )
        self.labels = dict(self.config.hetznerCloud.labels)

    def show_type(self):
        return "{0} [{1}]".format(self.get_type(), self.location or "???")


class HetznerCloudState(MachineState[HetznerCloudDefinition]):
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
    server_name = attr_property("hetznerCloud.serverName", None)
    server_type = attr_property("hetznerCloud.serverType", None)
    # block_device_mapping = attr_property("hetznerCloud.blockDeviceMapping", {}, "json")
    # networks = attr_property("hetznerCloud.networks", None)
    # ip_address = attr_property("hetznerCloud.ipAddress", None)
    labels = attr_property("hetznerCloud.labels", {}, "json")

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
            self.server_name = None
            self.server_type = None
            # self.blockDeviceMapping = None
            # self.ip_address = None
            # self.networks = None

    def show_type(self):
        s = super(HetznerCloudState, self).show_type()
        if self.location:
            s = "{0} [{1}; {2}]".format(s, self.location, self.server_type)
        return s

    @property
    def full_name(self) -> str:
        return "Hetzner Cloud Server '{0}'".format(self.name)

    def _get_instance(self) -> BoundServer:
        return self.get_client().servers.get_by_id(self.server_id)

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

    def get_common_labels(self) -> Dict[str, str]:
        labels = {
            "CharonNetworkUUID": self.depl.uuid,
            "CharonInstanceName": self.name,
            "CharonStateFileHost": socket.gethostname(),
            "CharonStateFileUser": getpass.getuser(),
        }
        pattern = "^$|(?i)((?=^[a-z0-9])[a-z0-9._-]{0,63}[a-z0-9]$)"
        file_name = os.path.basename(self.depl._db.db_file)
        if re.match(pattern, file_name):
            labels["CharonStateFileName"] = file_name
        if self.depl.name:
            labels["CharonNetworkName"] = self.depl.name
        return labels

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
        return super_flags + ["-i", self.get_ssh_private_key_file()]

    def get_physical_spec(self):
        return {
            "imports": [RawValue("<nixpkgs/nixos/modules/profiles/qemu-guest.nix>")],
            ("boot", "loader", "grub", "device"): "nodev",
            ("fileSystems", "/"): {"device": "/dev/sda1", "fsType": "ext4"},
            ("users", "extraUsers", "root", "openssh", "authorizedKeys", "keys"): [
                self.public_client_key
            ],
        }

    #    def attach_volume(self):
    #        pass
    #    def attach_server_network(self):
    #        pass
    #    def assign_floating_ip(self):
    #        pass
    #    def update_block_device_mapping(self):
    #        pass

    def create_after(self, resources, defn) -> Set[HetznerCloudResourceState]:
        return {
            r
            for r in resources
            if isinstance(r, nixops_hetznercloud.resources.floating_ip.FloatingIPState)
            or isinstance(r, nixops_hetznercloud.resources.network.NetworkState)
            or isinstance(r, nixops_hetznercloud.resources.volume.VolumeState)
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

    def create(
        self, defn: HetznerCloudDefinition, check, allow_reboot, allow_recreate
    ) -> None:

        self.api_token = defn.api_token

        if self.state != self.UP:
            check = True

        self.set_common_state(defn)

        if self.api_token and self.api_token != defn.api_token:
            raise Exception("cannot change api token of an existing instance")

        # Stop the instance (if allowed) to change instance attributes
        # such as the server type.
        if self.server_id and allow_reboot and (self.server_type != defn.server_type):
            self.stop()
            check = True

        # Check whether the instance hasn't been killed behind our backs.
        # Handle changed server type.
        # Restart stopped instances.
        if self.server_id and check:
            instance = self._get_instance()

            if instance is None or instance.status in {"deleting"}:
                if not allow_recreate:
                    raise Exception(
                        "{0} went away; use ‘--allow-recreate’ to create a new one".format(
                            self.full_name
                        )
                    )
                self.log(
                    "{0} went away (state ‘{1}’), will recreate".format(
                        self.full_name, instance.status if instance else "gone"
                    )
                )
                self.cleanup_state()
                self.location = defn.location
            elif instance.status == "off":
                self.log("instance was stopped, restarting...")

                # Modify the server type, if desired.
                if self.server_type != defn.server_type:
                    self.log(
                        "changing server type from ‘{0}’ to ‘{1}’...".format(
                            self.server_type, defn.server_type
                        )
                    )
                    self.logger.warn(
                        "nixops does not currently support server type upgrade rollbacks"
                    )
                    # FIXME store disk size in state to enable downsizing server type
                    instance.change_type(defn.server_type, upgrade_disk=True)
                    self.server_type = defn.server_type

                self.start()

        # create the instance.
        if not self.server_id:

            if not self.public_client_key:
                (private, public) = create_key_pair()
                self.public_client_key = public
                self.private_client_key = private

            if not self.public_host_key:
                (private, public) = create_key_pair(type="ed25519")
                self.public_host_key = public
                self.private_host_key = private

            location: BoundLocation = self.get_client().locations.get_by_name(
                defn.location
            )

            server_type: BoundServerType = self.get_client().server_types.get_by_name(
                defn.server_type
            )

            ssh_keys: List[BoundSSHKey] = [self._create_ssh_key(self.public_client_key)]

            image: BoundImage = self.get_client().images.get_by_name(
                "ubuntu-20.04"
            )  # for lustration

            # Ensure host keys get injected into the base OS
            user_data = (
                "#cloud-config\n"
                "ssh_keys:\n"
                "  ed25519_public: {0}\n"
                "  ed25519_private: |\n"
                "    {1}"
            ).format(
                self.public_host_key, self.private_host_key.replace("\n", "\n    ")
            )

            self.logger.log_start(
                "creating {0} server at {1}...".format(
                    server_type.name, location.description
                )
            )
            response = self.get_client().servers.create(
                name=defn.server_name,
                labels={**self.get_common_labels(), **dict(defn.labels)},
                location=location,
                server_type=server_type,
                ssh_keys=ssh_keys,
                user_data=user_data,
                image=image,
                start_after_create=True,
            )

            self.state = self.STARTING
            self.wait_on_action(response.action)

            with self.depl._db:
                self.server_id = response.server.id
                self.public_ipv4 = response.server.public_net.ipv4.ip
                self.public_ipv6 = response.server.public_net.ipv6.ip
                self.server_name = defn.server_name
                self.server_type = defn.server_type
                self.location = defn.location
                self.labels = dict(defn.labels)
                # self.ip_address = defn.ip_address
                # self.networks = defn.networks
                self.private_host_key = None

            known_hosts.add(self.public_ipv4, self.public_host_key)

            self.logger.log_end("{0}".format(self.public_ipv4))
            self.wait_for_ssh()
            self.logger.log_start("running nixos-infect")
            self.state = self.RESCUE
            self.run_command("bash </dev/stdin 2>&1", stdin=open(INFECT_PATH))
            self.logger.log("rebooting into NixOS 😎")
            self.reboot_sync()
            self.state = self.UP

        # Warn about some options that we cannot update for an existing instance
        if self.location != defn.location:
            self.warn(
                "cannot change location of a running instance (from ‘{0}‘ to ‘{1}‘):"
                "use ‘--allow-recreate’".format(self.location, defn.location)
            )
        if self.server_type != defn.server_type:
            self.warn(
                "cannot change type of a running instance (from ‘{0}‘ to ‘{1}‘):"
                "use ‘--allow-reboot’".format(self.server_type, defn.server_type)
            )

        # Update name or labels if they have changed.
        if self.server_name != defn.server_name or self.labels != defn.labels:
            self.logger.log("updating trivial modified attributes")
            self._get_instance().update(
                defn.server_name, {**self.get_common_labels(), **dict(defn.labels)}
            )

    def _destroy(self) -> None:
        if self.state != self.UP:
            return
        self.logger.log("destroying {0}...".format(self.full_name))
        try:
            self.get_client().servers.get_by_id(self.server_id).delete()
        except hcloud.APIException as e:
            if e.code == "not_found":
                self.warn("{0} was already deleted".format(self.full_name))
        known_hosts.remove(self.public_ipv4, self.public_host_key)
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

    def stop(self) -> None:
        question = "are you sure you want to stop {0}?"
        if not self.depl.logger.confirm(question.format(self.full_name)):
            return
        instance = self._get_instance()
        self.logger.log(
            "sending ACPI shutdown request to {0}...".format(self.full_name)
        )
        self.wait_on_action(self.get_client().servers.shutdown(instance))
        self.state = self.STOPPED

    def reboot(self, hard=False) -> None:
        question = "are you sure you want to reboot {0}?"
        if self.state == self.UP and not self.depl.logger.confirm(
            question.format(self.full_name)
        ):
            return
        instance = self._get_instance()
        if hard:
            self.logger.log("sending hard reset to {0}...".format(self.full_name))
            self.wait_on_action(self.get_client().servers.reset(instance))
            self.wait_for_ssh()
        else:
            self.logger.log(
                "sending ACPI reboot request to {0}...".format(self.full_name)
            )
            self.wait_on_action(self.get_client().servers.reboot(instance))
            self.wait_for_ssh()

    def _check(self):
        pass

    def wait_on_action(self, action: BoundAction) -> None:
        while action.status == "running":
            self.logger.log_continue(".")
            time.sleep(1)
            action = self.get_client().actions.get_by_id(action.id)
        if action.status != "success":
            raise Exception("unexpected status: {0}".format(action.status))
