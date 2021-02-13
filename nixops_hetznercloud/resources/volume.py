# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Volumes.

from hcloud import APIException
from hcloud.volumes.domain import CreateVolumeResponse
from hcloud.locations.client import BoundLocation
from hcloud.actions.domain import ActionFailedException, ActionTimeoutException

from nixops.diff import Handler
from nixops.util import attr_property, check_wait
from nixops.resources import ResourceDefinition
from nixops_hetznercloud.hetznercloud_common import HetznerCloudResourceState

from typing import Any, Dict, Sequence

from .types.volume import VolumeOptions


class VolumeDefinition(ResourceDefinition):
    """
    Definition of a Hetzner Cloud volume.
    """

    config: VolumeOptions

    @classmethod
    def get_type(cls):
        return "hetznercloud-volume"

    @classmethod
    def get_resource_type(cls):
        return "hetznerCloudVolumes"


class VolumeState(HetznerCloudResourceState):
    """
    State of a Hetzner Cloud Volume.
    """

    definition_type = VolumeDefinition

    _resource_type = "volumes"
    _reserved_keys = HetznerCloudResourceState.COMMON_HCLOUD_RESERVED + [
        "needsFSResize",
    ]

    needsFSResize = attr_property("needsFSResize", None, bool)

    @classmethod
    def get_type(cls):
        return "hetznercloud-volume"

    def __init__(self, depl, name, id):
        super(HetznerCloudResourceState, self).__init__(depl, name, id)
        self.handle_create_volume = Handler(
            ["location", "fsType"], handle=self.realise_create_volume
        )
        self.handle_resize_volume = Handler(
            ["size"],
            after=[self.handle_create_volume],
            handle=self.realise_resize_volume,
        )
        self.handle_modify_labels = Handler(
            ["labels"],
            after=[self.handle_resize_volume],
            handle=super().realise_modify_labels,
        )

    def show_type(self):
        s = f"{super(VolumeState, self).show_type()}"
        if self.state == self.UP:
            location = self._state["location"]
            size = self._state["size"]
            s += f" [{location}; {size}GiB]"
        return s

    @property
    def full_name(self) -> str:
        location = self._state.get("location", None)
        return f"Hetzner Cloud Volume {self.resource_id} [{location}]"

    def prefix_definition(self, attr: Any) -> Dict[Sequence[str], Any]:
        return {("resources", "hetznerCloudVolumes"): attr}

    def get_definition_prefix(self) -> str:
        return "resources.hetznerCloudVolumes."

    def cleanup_state(self) -> None:
        with self.depl._db:
            self.state = self.MISSING
            self.resource_id = None
            self.needsFSResize = None
            self._state["location"] = None
            self._state["size"] = None
            self._state["fsType"] = None
            self._state["labels"] = None

    def _destroy(self) -> None:
        instance = self.get_instance()

        def detach_volume() -> bool:
            self.logger.log(f"detaching {self.full_name}...")
            try:
                instance.detach().wait_until_finished()
            except APIException as e:
                if e.code == "locked":
                    return False
                else:
                    raise
            else:
                return True

        def destroy_volume() -> bool:
            self.logger.log(f"destroying {self.full_name}...")
            try:
                instance.delete()
            except APIException as e:
                if e.code == "locked":
                    return False
                else:
                    raise
            else:
                return True

        if instance is not None:
            # can't trust api for volume attach status, have to check server api
            if instance.server and self.get_client().servers.get_by_id(instance.server):
                check_wait(detach_volume)
            check_wait(destroy_volume)

        self.cleanup_state()

    def realise_create_volume(self, allow_recreate: bool) -> None:
        defn: VolumeOptions = self.get_defn().config

        if self.state == self.UP:
            if self._state["location"] != defn.location:
                raise Exception("changing a volume's location isn't supported.")
            if self._state["fsType"] != defn.fsType:
                raise Exception("reformatting a volume isn't supported.")
            if not allow_recreate:
                raise Exception(
                    f"{self.full_name} definition changed and it needs to be "
                    "recreated use --allow-recreate if you want to create a new one"
                )
            self.warn("volume definition changed, recreating...")
            self._destroy()
            self._client = None

        location: BoundLocation = self.get_client().locations.get_by_name(defn.location)
        name: str = self.get_default_name()

        self.logger.log(f"creating {defn.size}GB volume at {location.description}...")
        try:
            response: CreateVolumeResponse = self.get_client().volumes.create(
                location=location, name=name, size=defn.size, format=defn.fsType,
            )
            response.action and response.action.wait_until_finished()
            self.resource_id = response.volume.id
        except ActionFailedException:
            raise Exception(
                "Failed to create Hetzner Cloud volume resource "
                f"with following error: {response.action.error}"
            )
        except ActionTimeoutException:
            raise Exception(
                "failed to create Hetzner Cloud volume;"
                " timeout, maximium retries reached (100)"
            )

        with self.depl._db:
            self.state = self.STARTING
            self._state["location"] = defn.location
            self._state["size"] = defn.size
            self._state["fsType"] = defn.fsType

        self.wait_for_resource_available(self.resource_id)

    def realise_resize_volume(self, allow_recreate: bool) -> None:
        defn: VolumeOptions = self.get_defn().config
        size: int = self._state["size"]
        if size > defn.size:
            raise Exception("decreasing a volume's size isn't supported.")
        elif size < defn.size:
            self.logger.log(
                f"increasing volume size from {size} GiB to {defn.size} GiB"
            )

            self.get_instance().resize(defn.size).wait_until_finished()

            with self.depl._db:
                self._state["size"] = defn.size
                self.needsFSResize = True

    def destroy(self, wipe: bool = False) -> bool:
        question = f"are you sure you want to destroy {self.full_name}?"
        if not self.depl.logger.confirm(question):
            return False
        self._destroy()
        return True
