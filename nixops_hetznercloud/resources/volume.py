# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Volumes.

from hcloud.actions.domain import ActionFailedException, ActionTimeoutException

from nixops.diff import Handler
from nixops.resources import ResourceDefinition
from nixops_hetznercloud.hetznercloud_common import HetznerCloudResourceState

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

    def show_type(self):
        return "{0}".format(self.get_type())


class VolumeState(HetznerCloudResourceState):
    """
    State of a Hetzner Cloud Volume.
    """

    _resource_type = "volumes"
    _reserved_keys = HetznerCloudResourceState.COMMON_HCLOUD_RESERVED + ["volumeId"]

    @classmethod
    def get_type(cls):
        return "hetznercloud-volume"

    def __init__(self, depl, name, id):
        super(HetznerCloudResourceState, self).__init__(depl, name, id)
        self.volume_id = self.resource_id
        self.handle_create_volume = Handler(
            ["location", "fsType"], handle=self.realise_create_volume
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
        s = super(VolumeState, self).show_type()
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
            self._state["fsType"] = None
            self._state["labels"] = None

    def _check(self):
        if self.resource_id is None:
            pass
        elif self.get_instance() is None:
            self.warn(" it needs to be recreated...")
            self.cleanup_state()
        elif self.state == self.STARTING:
            self.wait_for_resource_available(self.resource_id)

    def _destroy(self):
        instance = self.get_instance()
        if instance is not None:
            self.logger.log("detaching {0}...".format(self.full_name))
            instance.detach().wait_until_finished()
            self.logger.log("destroying {0}...".format(self.full_name))
            instance.delete()
        self.cleanup_state()

    def realise_create_volume(self, allow_recreate):
        config = self.get_defn()

        if self.state == self.UP:
            if self._state["location"] != config.location:
                raise Exception("changing a volume's location isn't supported.")
            if self._state["fsType"] != config.fsType:
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
            "creating {0}GB volume at {1}...".format(config.size, location.description)
        )
        try:
            response = self.get_client().volumes.create(
                location=location, name=name, size=config.size, format=config.fsType,
            )
            if response.action:
                response.action.wait_until_finished()
            self.volume_id = response.volume.id
        except ActionFailedException:
            raise Exception(
                "Failed to create Hetzner Cloud volume resource "
                "with following error: {0}".format(response.action.error)
            )
        except ActionTimeoutException:
            raise Exception(
                "failed to create Hetzner Cloud volume;"
                " timeout, maximium retries reached (100)"
            )

        with self.depl._db:
            self.state = self.STARTING
            self._state["volumeId"] = self.volume_id
            self._state["location"] = config.location
            self._state["size"] = config.size
            self._state["fsType"] = config.fsType

        self.wait_for_resource_available(self.volume_id)

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

            self.get_instance().resize(config.size).wait_until_finished()

            with self.depl._db:
                self._state["size"] = config.size

    def realise_modify_volume_labels(self, allow_recreate):
        config = self.get_defn()

        self.logger.log("updating volume labels")
        self.get_instance().update(
            labels={**self.get_common_labels(), **dict(config.labels)}
        )

        with self.depl._db:
            self._state["labels"] = dict(config.labels)

    def destroy(self, wipe=False):
        self._destroy()
        return True
