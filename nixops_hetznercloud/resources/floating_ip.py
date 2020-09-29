# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Floating IPs.

from hcloud.actions.domain import ActionFailedException, ActionTimeoutException

from nixops.diff import Handler
from nixops.util import attr_property
from nixops.resources import ResourceDefinition
from nixops_hetznercloud.hetznercloud_common import HetznerCloudResourceState

from typing import Any, Dict, Sequence

from .types.floating_ip import FloatingIPOptions


class FloatingIPDefinition(ResourceDefinition):
    """
    Definition of a Hetzner Cloud floating IP address.
    """

    config: FloatingIPOptions

    @classmethod
    def get_type(cls):
        return "hetznercloud-floating-ip"

    @classmethod
    def get_resource_type(cls):
        return "hetznerCloudFloatingIPs"

    def show_type(self):
        return "{0}".format(self.get_type())


class FloatingIPState(HetznerCloudResourceState):
    """
    State of a Hetzner Cloud Floating IP.
    """

    definition_type = FloatingIPDefinition

    floating_ip_id = attr_property("floatingIpId", None)
    
    _resource_type = "floating_ips"
    _reserved_keys = HetznerCloudResourceState.COMMON_HCLOUD_RESERVED + [
        "floatingIpId",
        "address",
    ]

    @classmethod
    def get_type(cls):
        return "hetznercloud-floating-ip"

    def __init__(self, depl, name, id):
        super(HetznerCloudResourceState, self).__init__(depl, name, id)
        self.floating_ip_id = self.resource_id
        self.handle_create_floating_ip = Handler(
            ["location", "type"], handle=self.realise_create_floating_ip,
        )
        self.handle_modify_description = Handler(
            ["description"],
            after=[self.handle_create_floating_ip],
            handle=self.realise_modify_description,
        )
        self.handle_modify_labels = Handler(
            ["labels"],
            after=[self.handle_modify_description],
            handle=super().realise_modify_labels,
        )

    def show_type(self):
        s = super(FloatingIPState, self).show_type()
        location = self._state.get("location", None)
        if self.state == self.UP:
            s = "{0} [{1}]".format(s, location)
        return s

    @property
    def resource_id(self):
        return self._state.get("floatingIpId", None)

    @property
    def full_name(self) -> str:
        return "Hetzner Cloud Floating IP {0} [{1}]".format(
            self.resource_id, self._state.get("address", None)
        )

    def prefix_definition(self, attr: Any) -> Dict[Sequence[str], Any]:
        return {("resources", "hetznerCloudFloatingIPs"): attr}

    def get_definition_prefix(self) -> str:
        return "resources.hetznerCloudFloatingIPs."

    def get_physical_spec(self) -> Dict[str, Any]:
        return {
            "floatingIpId": self.resource_id,
            "address": self._state.get("address", None),
        }

    def cleanup_state(self) -> None:
        with self.depl._db:
            self.state = self.MISSING
            self._state["floatingIpId"] = None
            self._state["address"] = None
            self._state["description"] = None
            self._state["labels"] = None
            self._state["location"] = None
            self._state["type"] = None

    def _destroy(self) -> None:
        instance = self.get_instance()
        if instance is not None:
            self.logger.log("destroying {0}...".format(self.full_name))
            instance.delete()
        self.cleanup_state()

    def realise_create_floating_ip(self, allow_recreate: bool) -> None:
        defn: FloatingIPOptions = self.get_defn().config

        if self.state == self.UP:
            if self._state["location"] != defn.location:
                raise Exception("changing a floating IP's location isn't supported.")
            if not allow_recreate:
                raise Exception(
                    "{0} definition changed and it needs to be recreated "
                    "use --allow-recreate if you want to create a new one".format(
                        self.full_name
                    )
                )
            self.warn("floating IP definition changed, recreating...")
            self._destroy()
            self._client = None

        location = self.get_client().locations.get_by_name(defn.location)

        self.logger.log("creating floating IP at {0}...".format(location.description))
        try:
            response = self.get_client().floating_ips.create(
                name=self.get_default_name(), type=defn.type, home_location=location,
            )
            if response.action:
                response.action.wait_until_finished()
            self.floating_ip_id = response.floating_ip.id
            address = response.floating_ip.ip
            self.logger.log("IP address is {0}".format(self.address))
        except ActionFailedException:
            raise Exception(
                "Failed to create Hetzner Cloud floating IP resource "
                "with following error: {0}".format(response.action.error)
            )
        except ActionTimeoutException:
            raise Exception(
                "failed to create Hetzner Cloud floating IP;"
                " timeout, maximium retries reached (100)"
            )

        with self.depl._db:
            self.state = self.STARTING
            self._state["floatingIpId"] = self.floating_ip_id
            self._state["location"] = defn.location
            self._state["type"] = defn.type
            self._state["address"] = address

        self.wait_for_resource_available(self.floating_ip_id)

    def realise_modify_description(self, allow_recreate: bool) -> None:
        defn: FloatingIPOptions = self.get_defn().config
        self.logger.log("updating floating IP description")
        self.get_instance().update(description=defn.description)
        with self.depl._db:
            self._state["description"] = defn.description

    def destroy(self, wipe: bool = False) -> bool:
        self._destroy()
        return True
