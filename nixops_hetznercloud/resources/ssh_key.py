# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud SSH Keys.

from hcloud import APIException

from nixops.diff import Handler
from nixops.resources import ResourceDefinition
from nixops_hetznercloud.hetznercloud_common import HetznerCloudResourceState

from typing import Any, Dict, Sequence

from .types.ssh_key import SSHKeyOptions


class SSHKeyDefinition(ResourceDefinition):
    """
    Definition of an SSH Key.
    """

    config: SSHKeyOptions

    @classmethod
    def get_type(cls):
        return "hetznercloud-ssh-key"

    @classmethod
    def get_resource_type(cls):
        return "hetznerCloudSSHKeys"

    def show_type(self):
        return "{0}".format(self.get_type())


class SSHKeyState(HetznerCloudResourceState):
    """
    State of an SSH Key.
    """

    _resource_type = "ssh_keys"
    _reserved_keys = HetznerCloudResourceState.COMMON_HCLOUD_RESERVED + ["sshKeyId"]

    @classmethod
    def get_type(cls):
        return "hetznercloud-ssh-key"

    def __init__(self, depl, name, id):
        super(HetznerCloudResourceState, self).__init__(depl, name, id)
        self.ssh_key_id = self.resource_id
        self.handle_create_ssh_key = Handler(
            ["publicKey"], handle=self.realise_create_ssh_key,
        )
        self.handle_modify_labels = Handler(
            ["labels"],
            after=[self.realise_create_ssh_key],
            handle=super().realise_modify_labels,
        )

    def show_type(self):
        s = super(SSHKeyState, self).show_type()
        return "{0}".format(s)

    @property
    def resource_id(self):
        return self._state.get("sshKeyId", None)

    @property
    def full_name(self) -> str:
        return "Hetzner Cloud SSH Key {0}".format(self.resource_id)

    def prefix_definition(self, attr: Any) -> Dict[Sequence[str], Any]:
        return {("resources", "hetznerCloudSSHKeys"): attr}

    def get_physical_spec(self) -> Dict[Sequence[str], Any]:
        return {"sshKeyId": self.resource_id}

    def get_definition_prefix(self) -> str:
        return "resources.hetznerCloudSSHKeys."

    def cleanup_state(self) -> None:
        with self.depl._db:
            self.state = self.MISSING
            self._state["sshKeyId"] = None
            self._state["publicKey"] = ""  # None
            self._state["labels"] = None

    def _destroy(self) -> None:
        if self.state != self.UP:
            return
        self.logger.log("destroying {0}...".format(self.full_name))
        self.get_instance().delete()
        self.cleanup_state()

    def realise_create_ssh_key(self, allow_recreate: bool) -> None:
        """
        Handle both create and recreate of the ssh key resource.
        """
        defn: SSHKeyOptions = self.get_defn().config
        name = self.get_default_name()

        if self.state == self.UP:
            if not allow_recreate:
                raise Exception(
                    "{} definition changed and it needs to be recreated "
                    "use --allow-recreate if you want to create a new one".format(
                        self.full_name
                    )
                )
            self.warn("ssh_key definition changed, recreating...")
            self._destroy()
            self._client = None

        self.logger.log("creating ssh key '{}'...".format(name))
        try:
            self.ssh_key_id = (
                self.get_client()
                .ssh_keys.create(
                    name=name,
                    public_key=defn.publicKey,
                )
                .id
            )
        except APIException as e:
            if e.code == "invalid_input":
                raise Exception(
                    "couldn't create SSH Key Resource due to {}".format(e.message)
                )
            else:
                raise e

        with self.depl._db:
            self.state = self.STARTING
            self._state["sshKeyId"] = self.ssh_key_id
            self._state["publicKey"] = defn.publicKey

        self.wait_for_resource_available(self.ssh_key_id)

    def destroy(self, wipe: bool = False) -> bool:
        self._destroy()
        return True
