# -*- coding: utf-8 -*-

# Automatic provisioning of a Hetzner Cloud Server instance.

import os
import re
import time
import socket
import getpass

from hcloud import APIException
from hcloud import Client
from hcloud.actions.client import BoundAction
from hcloud.images.client import BoundImage
from hcloud.locations.client import BoundLocation
from hcloud.servers.client import BoundServer
from hcloud.server_types.client import BoundServerType
from hcloud.ssh_keys.client import BoundSSHKey
from hcloud.volumes.client import BoundVolume

from nixops import known_hosts
from nixops.backends import MachineDefinition, MachineState
from nixops.deployment import Deployment
from nixops.nix_expr import RawValue
from nixops.resources import ResourceEval
from nixops.util import attr_property, create_key_pair, check_wait

from nixops_hetznercloud.hetznercloud_common import HetznerCloudResourceState
from nixops_hetznercloud.resources.floating_ip import FloatingIPState
from nixops_hetznercloud.resources.network import NetworkState
from nixops_hetznercloud.resources.volume import VolumeState

from typing import Dict, List, Set, Any

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
        self.labels = dict(self.config.hetznerCloud.labels)
        self.location = self.config.hetznerCloud.location
        self.server_name = self.config.hetznerCloud.serverName
        self.server_type = self.config.hetznerCloud.serverType
        self.volumes = [dict(x) for x in self.config.hetznerCloud.volumes]
        # self.networks = self.config.hetznerCloud.networks
        # self.ip_address = self.config.hetznerCloud.ipAddress

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
    public_ipv4 = attr_property("publicIpv4", None)
    public_ipv6 = attr_property("publicIpv6", None)
    private_ipv4 = attr_property("privateIpv4", None)
    public_client_key = attr_property("hetznerCloud.publicClientKey", None)
    private_client_key = attr_property("hetznerCloud.privateClientKey", None)
    public_host_key = attr_property("hetznerCloud.publicHostKey", None)
    private_host_key = attr_property("hetznerCloud.privateHostKey", None)
    labels = attr_property("hetznerCloud.labels", {}, "json")
    location = attr_property("hetznerCloud.location", None)
    server_name = attr_property("hetznerCloud.serverName", None)
    server_type = attr_property("hetznerCloud.serverType", None)
    volumes = attr_property("hetznerCloud.volumes", [], "json")
    # networks = attr_property("hetznerCloud.networks", None)
    # ip_address = attr_property("hetznerCloud.ipAddress", None)

    def __init__(self, depl: Deployment, name: str, id):
        MachineState.__init__(self, depl, name, id)
        self._client = None

    def cleanup_state(self):
        """ Discard all state pertaining to an instance. """
        with self.depl._db:
            self.vm_id = None
            self.public_ipv4 = None
            self.public_ipv6 = None
            self.private_client_key = None
            self.public_client_key = None
            self.private_host_key = None
            self.public_host_key = None
            self.location = None
            self.server_name = None
            self.server_type = None
            self.labels = {}
            self.volumes = []
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
        try:
            return self.get_client().servers.get_by_id(self.vm_id)
        except APIException as e:
            if e.code == "not_found":
                self.warn(
                    "{0} was deleted from outside of nixops".format(self.full_name)
                )
            return None

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

    def get_udev_name(self, volume_id: str):
        return "/dev/disk/by-id/scsi-0HC_Volume_{0}".format(volume_id)

    def get_physical_spec(self):
        spec = {
            "imports": [RawValue("<nixpkgs/nixos/modules/profiles/qemu-guest.nix>")],
            ("boot", "loader", "grub", "device"): "nodev",
            ("fileSystems", "/"): {"device": "/dev/sda1", "fsType": "ext4"},
            **{
                ("fileSystems", v["mountPoint"], "device"): v["device"]
                for v in self.volumes
                if "device" in v
            },
            ("deployment", "hetznerCloud", "volumes"): self.volumes,
            ("users", "extraUsers", "root", "openssh", "authorizedKeys", "keys"): [
                self.public_client_key
            ],
        }
        print(spec)
        return spec

    def update_volume(self, v: Dict[str, Any]) -> None:
        volumes = list(self.volumes)
        for i, x in enumerate(volumes):
            if x["volume"] == v["volume"]:
                volumes[i] = v
                self.volumes = volumes
                return
        # doesn't exist, add new entry
        volumes.append(v)
        self.volumes = volumes

    def attach_volume(self, v: Dict[str, Any]) -> None:
        """
        Attaches an existing Hetzner Cloud Volume to this instance.
        """

        # Check volume exists and made available.

        volume: BoundVolume = self.get_client().volumes.get_by_name(v["volume"])
        if not volume:
            raise Exception(
                "volume {0} doesn't exist, run check to update the state of the volume".format(
                    v["volume"]
                )
            )
        if (
            volume.server
            and self.vm_id != volume.server.id
            and self.depl.logger.confirm(
                "volume ‘{0}’ is in use by instance ‘{1}’, "
                "are you sure you want to attach this volume?".format(
                    v["volume"], volume.server.id
                )
            )
        ):  # noqa: E124
            self.logger.log_start(
                "detaching volume ‘{0}’ from instance ‘{1}’... ".format(
                    v["volume"], volume.server.id
                )
            )
            volume.detach().wait_until_finished()

        # Attach volume.

        self.logger.log_start("attaching volume ‘{0}’... ".format(v["volume"]))
        volume = self.get_client().volumes.get_by_name(v["volume"])
        volume.attach(self._get_instance()).wait_until_finished()

        # Wait until the device is visible in the instance.

        v["device"] = self.get_udev_name(volume.id)

        def check_device():
            res = self.run_command("test -e {0}".format(v["device"]), check=False)
            return res == 0

        if not check_wait(check_device, initial=1, max_tries=10, exception=False):
            # If stopping times out, then do an unclean shutdown.
            self.logger.log_end("(timed out)")
            self.logger.log("can't find device ‘{0}’...".format(v["device"]))
            self.logger.log("available devices:")
            self.run_command("lsblk")
            raise Exception("operation timed out")
        else:
            self.logger.log_end("")

    def mount_volume(self, v: Dict[str, Any]) -> None:
        volume = self.get_client().volumes.get_by_name(v["volume"])
        v["device"] = self.get_udev_name(volume.id)

    def create_after(self, resources, defn) -> Set[HetznerCloudResourceState]:
        return {
            r
            for r in resources
            if isinstance(r, FloatingIPState)
            or isinstance(r, NetworkState)
            or isinstance(r, VolumeState)
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

    def create(  # noqa: C901
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
        if self.vm_id and allow_reboot and (self.server_type != defn.server_type):
            self.stop()
            check = True

        # Check whether the instance hasn't been killed behind our backs.
        # Handle changed server type.
        # Restart stopped instances.
        if self.vm_id and check:
            instance = self._get_instance()

            if instance is None or instance.status in {"deleting"}:
                if not allow_recreate:
                    raise Exception(
                        "{0} went away; use ‘--allow-recreate’ to create a new one".format(
                            self.full_name
                        )
                    )
                self.logger.log(
                    "{0} went away (state ‘{1}’), will recreate".format(
                        self.full_name, instance.status if instance else "gone"
                    )
                )
                self.cleanup_state()
                self.location = defn.location
            elif instance.status == "off":
                self.logger.log("instance was stopped, restarting...")

                # Modify the server type, if desired.
                if self.server_type != defn.server_type:
                    self.logger.log(
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
        if not self.vm_id:

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

            # TODO auto create vols
            # volumes: List[BoundVolume] = self._create_volumes()

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
                self.vm_id = response.server.id
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

        # We need to attach any missing volumes
        # 1. Expected attached volumes are given as a list of BoundVolume in self.volumes
        # 2. Really attached volumes are given as a list of DiskOption in self._get_instance().volumes
        # 3. Final attached volumes are given as a list of DiskOption in defn.volumes

        # identify volumes which got detached with 1-2

        self.volumes = defn.volumes

        # Attach missing volumes (3-2)

        attached: Set[str] = {x.name for x in self._get_instance().volumes}
        for v in defn.volumes:
            if v["volume"] not in attached:
                self.logger.log("missing volume: {0}".format(v["volume"]))
                self.attach_volume(v)
                self.update_volume(v)

        # Ensure filesystem devices are correct for all mounted volumes.

        # Hetzner Cloud volume device names follow a specification that
        # uses a fixed prefix suffixed by the volume id. Because this
        # isn't known until deployment, we delayed setting the
        # config.fileSystems.<name?>.device option. The workaround is to
        # define this option in the deployment's physical spec. After
        # attaching any volume which needs mounting, define a device
        # key/value entry for the volume entry in self.volumes. This will
        # get used when building the physical spec after instance creation.
        for v in defn.volumes:
            if v["mountPoint"]:
                self.mount_volume(v)
                self.update_volume(v)

    # def _destroy_volume(self, volume_id: str, allow_keep=False) -> None:
    #     if not self.depl.logger.confirm(
    #         "are you sure you want to destroy Hetzner Cloud volume ‘{0}’?".format(volume_id)
    #     ):
    #         if allow_keep:
    #             return
    #         else:
    #             raise Exception("not destroying Hetzner Cloud volume ‘{0}’".format(volume_id))
    #     self.logger.log("destroying Hetzner Cloud volume ‘{0}’...".format(volume_id))
    #     volume = self.get_client().volumes.get_by_id(volume_id, allow_missing=True)
    #     if volume is not None:
    #         volume.delete().wait_until_finished

    def _destroy(self) -> None:
        if self.state != self.UP:
            return
        self.logger.log("destroying {0}...".format(self.full_name))
        try:
            self.get_client().servers.get_by_id(self.vm_id).delete()
        except APIException as e:
            if e.code == "not_found":
                self.warn("{0} was already deleted".format(self.full_name))

        # remove host ssh key
        self.get_client().ssh_keys.get_by_name(
            "nixops-{0}-{1}".format(self.depl.uuid, self.name)
        ).delete()
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
