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
from hcloud.images.domain import Image
from hcloud.floating_ips.client import BoundFloatingIP
from hcloud.locations.client import BoundLocation
from hcloud.networks.client import BoundNetwork
from hcloud.servers.client import BoundServer
from hcloud.server_types.domain import ServerType
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

from typing import Dict, List, Optional, Set, Any

from .options import HetznerCloudMachineOptions


INFECT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "nixos-infect")
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
        self.server_networks = {
            x.network: dict(x) for x in self.config.hetznerCloud.serverNetworks
        }
        self.volumes = {x.volume: dict(x) for x in self.config.hetznerCloud.volumes}
        self.ip_addresses = {x: None for x in self.config.hetznerCloud.ipAddresses}

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
    vm_id = attr_property("vmId", None, int)  # override type
    api_token = attr_property("hetznerCloud.apiToken", None)
    public_ipv4 = attr_property("publicIpv4", None)
    public_ipv6 = attr_property("publicIpv6", None)
    private_ipv4 = attr_property("privateIpv4", None)
    public_client_key = attr_property("hetznerCloud.publicClientKey", None)
    private_client_key = attr_property("hetznerCloud.privateClientKey", None)
    public_host_key = attr_property("hetznerCloud.publicHostKey", None)
    private_host_key = attr_property("hetznerCloud.privateHostKey", None)
    legacy_if_scheme = attr_property("legacyIfScheme", None, bool)
    labels = attr_property("hetznerCloud.labels", {}, "json")
    location = attr_property("hetznerCloud.location", None)
    server_name = attr_property("hetznerCloud.serverName", None)
    server_type = attr_property("hetznerCloud.serverType", None)
    server_networks = attr_property("hetznerCloud.serverNetworks", {}, "json")
    volumes = attr_property("hetznerCloud.volumes", {}, "json")
    ip_addresses = attr_property("hetznerCloud.ipAddresses", {}, "json")

    def __init__(self, depl: Deployment, name: str, id):
        MachineState.__init__(self, depl, name, id)
        self._client = None

    def cleanup_state(self) -> None:
        """ Discard all state pertaining to an instance. """
        with self.depl._db:
            self.vm_id = None
            self.public_ipv4 = None
            self.public_ipv6 = None
            self.private_client_key = None
            self.public_client_key = None
            self.private_host_key = None
            self.public_host_key = None
            self.legacy_if_scheme = None
            self.location = None
            self.server_name = None
            self.server_type = None
            self.server_networks = {}
            self.labels = {}
            self.volumes = {}
            self.ip_addresses = {}

    def show_type(self):
        s = super(HetznerCloudState, self).show_type()
        if self.location:
            s = "{0} [{1}; {2}]".format(s, self.location, self.server_type)
        return s

    @property
    def full_name(self) -> str:
        return "Hetzner Cloud Server ‘{0}’".format(self.name)

    def get_instance(self) -> BoundServer:
        try:
            return self.get_client().servers.get_by_id(self.vm_id)
        except APIException as e:
            if e.code == "not_found":
                self.logger.warn(
                    "{0} was deleted from outside of nixops".format(self.full_name)
                )
                return None
            else:
                raise

    def get_client(self) -> Client:
        """
        Generic method to get or create a Hetzner Cloud client.
        """
        if self._client:
            return self._client

        new_api_token = self.api_token or os.environ.get("HCLOUD_API_TOKEN")
        if new_api_token is not None:
            self.api_token = new_api_token

        if self.api_token is None:
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

    def get_ssh_private_key_file(self) -> str:
        return self._ssh_private_key_file or self.write_ssh_private_key(
            self.private_client_key
        )

    def get_ssh_flags(self, *args, **kwargs) -> List[str]:
        super_flags = super(HetznerCloudState, self).get_ssh_flags(*args, **kwargs)
        return super_flags + ["-i", self.get_ssh_private_key_file()]

    def get_udev_name(self, volume_id: str) -> str:
        return "/dev/disk/by-id/scsi-0HC_Volume_{0}".format(volume_id)

    def get_physical_spec(self) -> Dict[Any, Any]:

        ipv4 = [{"address": self.public_ipv4, "prefixLength": 32}]
        ipv6 = [{"address": self.public_ipv6[:-3], "prefixLength": 64}]
        for addr in self.ip_addresses.values():
            try:
                socket.inet_pton(socket.AF_INET, addr)
                ipv4.append({"address": addr, "prefixLength": 32})
            except socket.error:  # not a valid address ipv4
                ipv6.append({"address": addr, "prefixLength": 64})

        def get_interface_name(i: int) -> str:
            if self.legacy_if_scheme:
                return "ens" + str(10 + i)
            else:
                return "enp" + str(7 + i) + "s0"

        spec = {
            "imports": [RawValue("<nixpkgs/nixos/modules/profiles/qemu-guest.nix>")],
            ("boot", "loader", "grub", "device"): "nodev",
            ("fileSystems", "/"): {"device": "/dev/sda1", "fsType": "ext4"},
            **{
                ("fileSystems", v["mountPoint"]): {
                    "fsType": v["fsType"],
                    "device": v["device"],
                }
                for k, v in self.volumes.items()
                if v["mountPoint"]
            },
            # Hetzner Cloud networking defaults
            ("networking", "defaultGateway"): "172.31.1.1",
            ("networking", "nameservers"): [
                "213.133.98.98",
                "213.133.99.99",
                "213.133.100.100",
            ],
            (
                "networking",
                "interfaces",
                "ens3" if self.legacy_if_scheme else "enp1s0",
            ): {
                ("ipv4", "addresses"): ipv4,
                ("ipv6", "addresses"): ipv6,
                "useDHCP": True,
            },
            ("users", "extraUsers", "root", "openssh", "authorizedKeys", "keys"): [
                self.public_client_key
            ],
        }

        for i, v in enumerate(self.server_networks.values()):
            private_ipv4_addresses = [
                {"address": addr, "prefixLength": 32}
                for addr in [v["privateIP"]] + v["aliasIPs"]
            ]
            spec[("networking", "interfaces", get_interface_name(i))] = {
                ("ipv4", "addresses"): private_ipv4_addresses,
                "useDHCP": True,
            }

        for v in self.volumes.values():
            if v["fsType"] == "xfs":
                spec[("boot", "kernelModules")] = ["xfs"]
                break

        return spec

    def _update_attr(self, attr: str, k: str, v: Optional[Dict[str, Any]]) -> None:
        x = getattr(self, attr)
        if v is None:
            x.pop(k, None)
        else:
            x[k] = v
        setattr(self, attr, x)

    def _handle_changed_server_networks(
        self, defn: HetznerCloudDefinition, allow_recreate: bool
    ) -> None:
        """
        Detects and corrects any virtual network state desynchronisation.
        """
        instance = self.get_instance()

        attached = [x.network.id for x in instance.private_net]
        for name in self.server_networks.keys():
            network: BoundNetwork = self.get_client().networks.get_by_name(name)

            # Detect destroyed networks
            if network is None:
                if name not in defn.server_networks:  # we dont need it
                    self.logger.warn(
                        "forgetting about network ‘{0}’ that no longer exists and "
                        "is no longer needed by the deployment specification".format(
                            name
                        )
                    )
                    self._update_attr("server_networks", name, None)
                else:  # we do need it
                    raise Exception(
                        "network ‘{0}’ (used by {1}) no longer exists; run"
                        " ‘nixops deploy --check’ to update resource state".format(
                            name, self.full_name
                        )
                    )
            # Detect network detachment
            elif network.id not in attached:
                self.logger.warn(
                    "instance was manually detached from network ‘{0}’ [{1}]".format(
                        name, network.id
                    )
                )
                if name in defn.server_networks:
                    self._update_attr("server_networks", name, None)
            # Detach from existing networks if required.
            elif name not in defn.server_networks:
                self.logger.log(
                    "detaching from network ‘{0}’ [{1}]".format(name, network.id)
                )
                instance.detach_from_network(network).wait_until_finished()
                self._update_attr("server_networks", name, None)

        for name, x in defn.server_networks.items():
            if name not in self.server_networks:
                nw = self.get_client().networks.get_by_name(name)
                if nw is None:
                    raise Exception(
                        "tried to attach instance to network ‘{0}’"
                        " but it doesn't exist...".format(name)
                    )

                # NixOps will update machines in parallel, so retry
                # network attachment to deal with resource conflict.
                def attach_to_network() -> bool:
                    try:
                        action = self.get_instance().attach_to_network(
                            nw, x["privateIP"], x["aliasIPs"]
                        )
                        self.wait_on_action(action)
                    except APIException as e:
                        if e.code == "conflict":
                            return False
                        else:
                            raise
                    else:
                        self._update_attr("server_networks", x["network"], x)
                        return True

                self.logger.log(
                    "attaching instance to network ‘{0}’ [{1}]...".format(name, nw.id)
                )
                check_wait(attach_to_network)

    def _handle_changed_floating_ips(
        self, defn: HetznerCloudDefinition, allow_recreate: bool
    ) -> None:
        """
        Detects and corrects any floating IP state desynchronisation.
        """
        instance = self.get_instance()

        assigned: Set[str] = {x.name for x in instance.public_net.floating_ips}
        for name in self.ip_addresses.keys():
            fip: BoundFloatingIP = self.get_client().floating_ips.get_by_name(name)

            # Detect manually destroyed floating IPs
            if fip is None:
                if name not in defn.ip_addresses:  # we dont need it
                    self.logger.warn(
                        "forgetting about floating IP ‘{0}’ that no longer exists"
                        " and is no longer needed by the deployment specification".format(
                            name
                        )
                    )
                    self._update_attr("ip_addresses", name, None)
                else:
                    if name.startswith("nixops-"):
                        msg = (
                            "floating IP ‘{0}’ (used by {1}) no longer exists;"
                            "run ‘nixops deploy --check’ to update resource state"
                        )
                    else:
                        msg = "floating IP ‘{0}’ (used by {1}) was manually destroyed"
                    raise Exception(msg.format(name, self.full_name))

            # Detect unassigned floating IPs
            elif name not in assigned:
                if name not in defn.ip_addresses:  # we dont need it
                    self.logger.warn(
                        "forgetting about unassigned floating IP ‘{0}’ [{1}] "
                        "that is no longer needed by the deployment specification".format(
                            name, fip.id
                        )
                    )
                else:  # we do need it
                    self.logger.warn(
                        "floating IP ‘{0}’ [{1}] was manually unassigned; "
                        "will reassign it.".format(name, fip.id)
                    )
                    self._update_attr("ip_addresses", name, None)

        # Assign missing floating IPs.
        for name in defn.ip_addresses:
            if name not in self.ip_addresses:
                fip = self.get_client().floating_ips.get_by_name(name)
                if fip is None:
                    raise Exception(
                        "tried to assign floating IP ‘{0}’"
                        " but it doesn't exist...".format(name)
                    )
                self.logger.log(
                    "assigning floating IP ‘{0}’ [{1}]...".format(name, fip.id)
                )
                action = fip.assign(self.get_instance())
                self.wait_on_action(action)
                self._update_attr("ip_addresses", name, fip.ip)

    def _handle_changed_volumes(
        self, defn: HetznerCloudDefinition, allow_recreate: bool
    ) -> None:
        """
        Detects and corrects any volume state desynchronisation.
        """

        attached: Set[str] = {x.name for x in self.get_instance().volumes}
        for name in self.volumes.keys():
            volume: BoundVolume = self.get_client().volumes.get_by_name(name)

            # Detect destroyed volumes.
            if volume is None:
                if name not in defn.volumes:  # we dont need it
                    self.logger.warn(
                        "forgetting about volume ‘{0}’ that no longer exists and"
                        " is no longer needed by the deployment specification".format(
                            name
                        )
                    )
                else:
                    if name.startswith("nixops-"):
                        msg = (
                            "volume ‘{0}’ (used by {1}) no longer exists;"
                            "run ‘nixops deploy --check’ to update resource state"
                        )
                    else:
                        msg = "volume ‘{0}’ (used by {1}) was manually destroyed"
                    raise Exception(msg.format(name, self.full_name))

            # Detect detached volumes.
            elif name not in attached:
                if name not in defn.volumes:  # we dont need it
                    self.logger.warn(
                        "forgetting about detached volume ‘{0}’ [{1}] that is no"
                        " longer needed by the deployment specification".format(
                            name, volume.id
                        )
                    )
                else:  # we do need it
                    self.logger.warn(
                        "volume ‘{0}’ [{1}] was manually detached; will reattach it".format(
                            name, volume.id
                        )
                    )
                self._update_attr("volumes", name, None)
            # Detach existing attached volumes if required.
            elif name not in defn.volumes:
                self.logger.warn(
                    "detaching volume ‘{0}’ [{1}] that is no longer"
                    " needed by the deployment specification".format(name, volume.id)
                )
                volume.detach().wait_until_finished()
                self._update_attr("volumes", name, None)

        # Attach missing volumes. resize filesystems if required, before mounting.
        for name, v in defn.volumes.items():
            if name not in self.volumes:

                # Check if it exists. resources will have been created if user ran check,
                # but prexisting vols which got deleted may be gone (detected in code above)

                volume = self.get_client().volumes.get_by_name(name)
                if volume is None:
                    self.logger.warn(
                        "tried to attach non-NixOps managed volume ‘{0}’,"
                        " but it doesn't exist... skipping".format(name)
                    )
                    continue
                elif volume.location.name != self.location:
                    raise Exception(
                        "volume ‘{0}’ [{1}] is in a different location to {2};"
                        " attempting to attach it will fail.".format(
                            name, volume.id, self.full_name
                        )
                    )
                elif (
                    volume.server
                    and volume.server.id != self.vm_id
                    and self.depl.logger.confirm(
                        "volume ‘{0}’ is in use by instance ‘{1}’, "
                        "are you sure you want to attach this volume?".format(
                            name, volume.server.id
                        )
                    )
                ):  # noqa: E124
                    self.logger.log(
                        "detaching volume ‘{0}’ from instance ‘{1}’... ".format(
                            name, volume.server.id
                        )
                    )
                    volume.detach().wait_until_finished()
                    volume.server = None

                # Attach volume.

                self.logger.log(
                    "attaching volume ‘{0}’ [{1}]... ".format(name, volume.id)
                )
                volume.attach(self.get_instance()).wait_until_finished()

                # Wait until the device is visible in the instance.

                v["device"] = self.get_udev_name(volume.id)

                def check_device() -> bool:
                    res = self.run_command(
                        "test -e {0}".format(v["device"]), check=False
                    )
                    return res == 0

                if not check_wait(
                    check_device, initial=1, max_tries=10, exception=False
                ):
                    # If stopping times out, then do an unclean shutdown.
                    self.logger.log_end("(timed out)")
                    self.logger.log("can't find device ‘{0}’...".format(v["device"]))
                    self.logger.log("available devices:")
                    self.run_command("lsblk")
                    raise Exception("operation timed out")
                else:
                    self._update_attr("volumes", name, v)
                    self.logger.log_end("")

            # Grow filesystems on resource based volumes.

            # We want to grow the fs when its volume gets resized, but if the
            # volume isn't attached to any server at the time, thats not possible.
            # Blindly trying to grow all volumes when mounting them just in case
            # they got resized while they were orphaned is bad. Workaround:
            # the needsFSResize attribute of VolumeState is set when the volume
            # gets resized by NixOps. When attaching a volume NixOps will use this
            # flag to decide whether to grow the filesystem.

            if name.startswith("nixops-" + self.depl.uuid):
                res = self.depl.get_typed_resource(
                    name[44:], "hetznercloud-volume", VolumeState
                )
                # get correct option definitions for volume resources
                v["size"] = res._state["size"]
                v["fsType"] = res._state["fsType"]
                v["device"] = self.get_udev_name(res._state["resourceId"])

                question = (
                    "volume {0} was resized, do you wish to grow its"
                    " filesystem to fill the space?".format(name)
                )
                op = "umount {0} ; e2fsck -fy {0} && resize2fs {0}".format(v["device"])

                if (
                    v["fsType"] == "ext4"
                    and res.needsFSResize
                    and self.depl.logger.confirm(question)
                    and self.run_command(op, check=False) == 0
                ):
                    with res.depl._db:
                        res.needsFSResize = False

                self._update_attr("volumes", name, v)

            if v["mountPoint"]:
                volume = self.get_client().volumes.get_by_name(name)
                v["device"] = self.get_udev_name(volume.id)
                self._update_attr("volumes", name, v)

    def after_activation(self, defn: HetznerCloudDefinition) -> None:

        # Unlike ext4, xfs filesystems must be resized while the underlying drive is mounted.
        # Thus this operation is delayed until after activation.
        for name, v in self.volumes.items():
            if (
                name.startswith("nixops-" + self.depl.uuid)
                and v["mountPoint"]
                and v["fsType"] == "xfs"
            ):
                res = self.depl.get_typed_resource(
                    name[44:], "hetznercloud-volume", VolumeState
                )
                question = (
                    "volume {0} was resized, do you wish to grow its"
                    " filesystem to fill the space?".format(name)
                )
                op = "xfs_growfs {0}".format(v["mountPoint"])
                if (
                    res.needsFSResize
                    and self.depl.logger.confirm(question)
                    and self.run_command(op, check=False) == 0
                ):
                    with res.depl._db:
                        res.needsFSResize = False

    def create_after(
        self, resources, defn: HetznerCloudDefinition
    ) -> Set[HetznerCloudResourceState]:
        return {
            r
            for r in resources
            if isinstance(r, FloatingIPState)
            or isinstance(r, NetworkState)
            or isinstance(r, VolumeState)
        }

    def _create_ssh_key(self, public_key: str) -> BoundSSHKey:
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

    def _create_instance(self, defn) -> None:
        if not self.public_client_key:
            (private, public) = create_key_pair(type="ed25519")
            self.public_client_key = public
            self.private_client_key = private

        if not self.public_host_key:
            (private, public) = create_key_pair(type="ed25519")
            self.public_host_key = public
            self.private_host_key = private

        location: BoundLocation = self.get_client().locations.get_by_name(defn.location)

        ssh_keys: List[BoundSSHKey] = [self._create_ssh_key(self.public_client_key)]

        # Ensure host keys get injected into the base OS
        user_data = (
            "#cloud-config\n"
            "ssh_keys:\n"
            "  ed25519_public: {0}\n"
            "  ed25519_private: |\n"
            "    {1}"
        ).format(self.public_host_key, self.private_host_key.replace("\n", "\n    "))

        self.logger.log_start(
            "creating {0} server at {1}...".format(
                defn.server_type, location.description
            )
        )
        response = self.get_client().servers.create(
            name=defn.server_name,
            labels={**self.get_common_labels(), **dict(defn.labels)},
            location=location,
            server_type=ServerType(defn.server_type),
            ssh_keys=ssh_keys,
            user_data=user_data,
            image=Image(name="ubuntu-20.04"),  # for lustration
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
            self.legacy_if_scheme = defn.server_type.startswith("cx")
            self.location = defn.location
            self.labels = dict(defn.labels)
            self.private_host_key = None

        known_hosts.add(self.public_ipv4, self.public_host_key)
        self.logger.log_end("{0}".format(self.public_ipv4))

    def create(  # noqa: C901
        self,
        defn: HetznerCloudDefinition,
        check: bool,
        allow_reboot: bool,
        allow_recreate: bool,
    ) -> None:
        self.api_token = defn.api_token

        if self.state != self.UP:
            check = True

        self.set_common_state(defn)

        if self.api_token and self.api_token != defn.api_token:
            raise Exception("cannot change api token of an existing instance")

        # Destroy the instance (if allowed) to handle attribute changes which
        # require recreating i.e. location
        if (
            self.vm_id
            and allow_recreate
            and self.location != defn.location
            and self.depl.logger.confirm(
                "changing server location requires recreate, are you sure?"
            )
        ):
            self._destroy()

        # Stop the instance (if allowed) to handle attribute changes which
        # require rebooting i.e. server_type
        if self.vm_id and allow_reboot and self.server_type != defn.server_type:
            self.stop()
            check = True

        # Check whether the instance hasn't been killed behind our backs.
        # Handle changed server type.
        # Restart stopped instances.
        if self.vm_id and check:
            instance = self.get_instance()

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

            # Modify the server type, if desired. FIXME store disk size
            # in state to enable option to later downsize server type.
            if instance.status == "off" and self.server_type != defn.server_type:
                self.logger.log_start(
                    "changing server type from ‘{0}’ to ‘{1}’;"
                    " may take a few minutes...".format(
                        self.server_type, defn.server_type
                    )
                )
                instance.change_type(
                    ServerType(defn.server_type), upgrade_disk=True
                ).wait_until_finished()
                self.logger.log_end("done!")

                with self.depl._db:
                    self.server_type = defn.server_type

                self.logger.log("instance was stopped, restarting...")
                self.start()

        # Provision the instance.
        if not self.vm_id:
            self._create_instance(defn)
            self.wait_for_ssh()
            self.logger.log_start("running nixos-infect")
            self.state = self.RESCUE
            self.run_command("bash </dev/stdin 2>&1", stdin=open(INFECT_PATH))
            self.logger.log("rebooting into NixOS 😎")
            self.reboot_sync()
            self.state = self.UP

        if self.location != defn.location:
            raise Exception(
                "cannot change location of an existing instance (from ‘{0}‘ to ‘{1}‘);"
                " use ‘--allow-recreate’".format(self.location, defn.location)
            )

        if self.server_type != defn.server_type:
            raise Exception(
                "cannot change server type of a running instance (from ‘{0}‘ to ‘{1}‘);"
                " use ‘--allow-reboot’".format(self.server_type, defn.server_type)
            )

        # Update name or labels if they have changed.
        if self.server_name != defn.server_name or self.labels != defn.labels:
            self.logger.log("updating trivial modified attributes")
            self.get_instance().update(
                defn.server_name, {**self.get_common_labels(), **dict(defn.labels)}
            )

        self._handle_changed_floating_ips(defn, allow_recreate)
        self._handle_changed_volumes(defn, allow_recreate)
        self._handle_changed_server_networks(defn, allow_recreate)

    def _destroy(self) -> None:
        if self.state != self.UP:
            return
        self.logger.log("destroying {0}...".format(self.full_name))

        # Detach volumes
        for name, v in self.volumes.items():
            #            if not name.startswith("nixops-" + self.depl.uuid):
            self.logger.log("detaching volume {0}...".format(name))
            self.get_client().volumes.get_by_name(name).detach().wait_until_finished()

        instance = self.get_instance()
        if instance is not None:
            instance.delete()

        # Remove host ssh key.

        self.get_client().ssh_keys.get_by_name(
            "nixops-{0}-{1}".format(self.depl.uuid, self.name)
        ).delete()
        known_hosts.remove(self.public_ipv4, self.public_host_key)

        self.cleanup_state()

    def destroy(self, wipe: bool = False) -> bool:
        question = "are you sure you want to destroy {0}?"
        if not self.depl.logger.confirm(question.format(self.full_name)):
            return False
        self._destroy()
        return True

    def start(self) -> None:
        instance = self.get_instance()
        self.logger.log_start("powering on {0}...".format(self.full_name))
        self.wait_on_action(self.get_client().servers.power_on(instance))
        self.wait_for_ssh()
        self.state = self.UP

    def stop(self) -> None:
        question = "are you sure you want to stop {0}?"
        if not self.depl.logger.confirm(question.format(self.full_name)):
            return
        instance = self.get_instance()
        self.logger.log_start(
            "sending ACPI shutdown request to {0}...".format(self.full_name)
        )
        self.wait_on_action(self.get_client().servers.shutdown(instance))
        while not self._check_status("off"):
            time.sleep(1)
        self.state = self.STOPPED

    def reboot(self, hard: bool = False) -> None:
        question = "are you sure you want to reboot {0}?"
        if self.state == self.UP and not self.depl.logger.confirm(
            question.format(self.full_name)
        ):
            return
        instance = self.get_instance()
        if hard:
            self.logger.log_start("sending hard reset to {0}...".format(self.full_name))
            self.wait_on_action(self.get_client().servers.reset(instance))
        else:
            self.logger.log_start(
                "sending ACPI reboot request to {0}...".format(self.full_name)
            )
            self.wait_on_action(self.get_client().servers.reboot(instance))
        self.wait_for_ssh()
        self.state = self.UP

    def _check(self, res):
        if not self.vm_id:
            res.exists = False

    def _check_status(self, status) -> bool:
        instance = self.get_instance()
        return instance.status == status

    def wait_on_action(self, action: BoundAction) -> None:
        while action.status == "running":
            self.logger.log_continue(".")
            time.sleep(1)
            action = self.get_client().actions.get_by_id(action.id)
        self.logger.log_end("")
        if action.status != "success":
            raise Exception("unexpected status: {0}".format(action.status))
