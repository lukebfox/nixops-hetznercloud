# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Volumes.

import hcloud
import time

from nixops.diff import Handler
from nixops.util import attr_property
from nixops.resources import ResourceDefinition, ResourceState, DiffEngineResourceState
from nixops_hetznercloud.resources.hetznercloud_common import HetznerCloudCommonState

from .types.volume import HetznerCloudVolumeOptions


class HetznerCloudVolumeDefinition(ResourceDefinition):
    """
    Definition of a Hetzner Cloud volume.
    """

    config: HetznerCloudVolumeOptions

    @classmethod
    def get_type(cls):
        return "hetznercloud-volume"

    @classmethod
    def get_resource_type(cls):
        return "hetznerCloudVolumes"

    def show_type(self):
        return "{0}".format(self.get_type())


class HetznerCloudVolumeState(DiffEngineResourceState, HetznerCloudCommonState):
    """
    State of a Hetzner Cloud Volume.
    """

    state = attr_property("state", ResourceState.MISSING, int)
    api_token = attr_property("apiToken", None)
    _reserved_keys = HetznerCloudCommonState.COMMON_HCLOUD_RESERVED + ["volumeId"]

    @classmethod
    def get_type(cls):
        return "hetznercloud-volume"

    def __init__(self, depl, name, id):
        DiffEngineResourceState.__init__(self, depl, name, id)
        self.volume_id = self.resource_id
        self.handle_create_volume = Handler(
            ["location", "format"], handle=self.realise_create_volume
        )
        self.handle_resize_volume = Handler(
            ["size"],
            after=[self.handle_create_volume],
            handle=self.realise_resize_volume,
        )
        self.handle_modify_volume_labels = Handler(
            ["labels"],
            after=[self.handle_resize_volume],
            handle=self.realise_modify_volume_labels,
        )

    def show_type(self):
        s = super(HetznerCloudVolumeState, self).show_type()
        if self.state == self.UP:
            s = "{0} [{1}; {2} GiB]".format(
                s, self._state["location"], self._state["size"]
            )
        return s

    @property
    def resource_id(self):
        return self._state.get("volumeId", None)

    @property
    def full_name(self):
        return "Hetzner Cloud Volume {0} [{1}]".format(
            self.resource_id, self._state.get("location", None)
        )

    def prefix_definition(self, attr):
        return {("resources", "hetznerCloudVolumes"): attr}

    def get_definition_prefix(self):
        return "resources.hetznerCloudVolumes."

    def get_physical_spec(self):
        return {"volumeId": self.resource_id}

    def cleanup_state(self):
        with self.depl._db:
            self.state = self.MISSING
            self._state["volumeId"] = None
            self._state["location"] = None
            self._state["size"] = None
            self._state["format"] = None
            self._state["labels"] = None

    def _check(self):
        if self.resource_id is None:
            return
        try:
            self.get_client().volumes.get_by_id(self.resource_id)
        except hcloud.APIException as e:
            if e.code == "not_found":
                self.warn(
                    "{0} was deleted from outside nixops,"
                    " it needs to be recreated...".format(self.full_name)
                )
                self.cleanup_state()
                return
        if self.state == self.STARTING:
            self.wait_for_resource_available(self.get_client().volumes, self.resource_id)

    def _destroy(self):
        self.logger.log("destroying {0}...".format(self.full_name))
        try:
            self.get_client().volumes.get_by_id(self.resource_id).delete()
        except hcloud.APIException as e:
            if e.code == "not_found":
                self.warn("{0} was already deleted".format(self.full_name))
            else:
                raise e
        self.cleanup_state()

    def realise_create_volume(self, allow_recreate):
        config = self.get_defn()

        if self.state == self.UP:
            if self._state["location"] != config.location:
                raise Exception("changing a volume's location isn't supported.")
            if self._state["format"] != config.format:
                raise Exception("reformatting a volume isn't supported.")
            if not allow_recreate:
                raise Exception(
                    "{0} definition changed and it needs to be recreated "
                    "use --allow-recreate if you want to create a new one".format(
                        self.full_name
                    )
                )
            self.warn("volume definition changed, recreating...")
            self._destroy()
            self._client = None

        location = self.get_client().locations.get_by_name(config.location)
        name = self.get_default_name()

        self.logger.log(
            "creating volume '{0}' at {1}...".format(name, location.description)
        )
        try:
            response = self.get_client().volumes.create(
                location=location, name=name, size=config.size, format=config.format,
            )
            if response.action:
                response.action.wait_until_finished()
            self.volume_id = response.volume.id
        except hcloud.ActionFailedException:
            raise Exception(
                "Failed to create Hetzner Cloud volume resource "
                "with following error: {0}".format(response.action.error)
            )
        except hcloud.ActionTimeoutException:
            raise Exception(
                "failed to create Hetzner Cloud volume;"
                " timeout, maximium retries reached (100)"
            )

        with self.depl._db:
            self.state = self.STARTING
            self._state["volumeId"] = self.volume_id
            self._state["location"] = config.location
            self._state["size"] = config.size
            self._state["format"] = config.format

        self.wait_for_resource_available(self.get_client().volumes, self.volume_id)

    def realise_resize_volume(self, allow_recreate):
        config = self.get_defn()
        size = self._state["size"]
        if size > config.size:
            raise Exception("decreasing a volume's size isn't supported.")
        elif size < config.size:
            self.logger.log(
                "increasing volume size from {0} GiB to {1} GiB".format(
                    size, config.size
                )
            )

            self.get_client().volumes.get_by_id(self.resource_id).resize(
                config.size
            ).wait_until_finished()

            with self.depl._db:
                self._state["size"] = config.size

    def realise_modify_volume_labels(self, allow_recreate):
        config = self.get_defn()

        self.logger.log("updating volume labels")
        self.get_client().volumes.get_by_id(self.resource_id).update(
            labels={**self.get_common_labels(), **dict(config.labels)}
        )

        with self.depl._db:
            self._state["labels"] = dict(config.labels)

    def destroy(self, wipe=False):
        self._destroy()
        return True
