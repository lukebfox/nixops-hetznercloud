# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Floating IPs.

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


class FloatingIPState(HetznerCloudResourceState):
    """
    State of a Hetzner Cloud Floating IP.
    """

    definition_type = FloatingIPDefinition

    _resource_type = "floating_ips"
    _reserved_keys = HetznerCloudResourceState.COMMON_HCLOUD_RESERVED + [
        "address",
    ]

    address = attr_property("address", None)

    @classmethod
    def get_type(cls):
        return "hetznercloud-floating-ip"

    def __init__(self, depl, name, id):
        super(HetznerCloudResourceState, self).__init__(depl, name, id)
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
        s = f"{super(FloatingIPState, self).show_type()}"
        if self.state == self.UP:
            s += f" [{self._state.get('location', None)}]"
        return s

    @property
    def full_name(self) -> str:
        address = self._state.get("address", None)
        return f"Hetzner Cloud Floating IP {self.resource_id} [{address}]"

    def prefix_definition(self, attr: Any) -> Dict[Sequence[str], Any]:
        return {("resources", "hetznerCloudFloatingIPs"): attr}

    def get_definition_prefix(self) -> str:
        return "resources.hetznerCloudFloatingIPs."

    def get_physical_spec(self) -> Dict[str, Any]:
        s = super(FloatingIPState, self).get_physical_spec()
        s["address"] = self._state.get("address", None)
        return s

    def cleanup_state(self) -> None:
        with self.depl._db:
            self.state = self.MISSING
            self.resource_id = None
            self._state["address"] = None
            self._state["description"] = None
            self._state["labels"] = None
            self._state["location"] = None
            self._state["type"] = None

    def _destroy(self) -> None:
        instance = self.get_instance()
        if instance is not None:
            self.logger.log(f"destroying {self.full_name}...")
            instance.delete()
        self.cleanup_state()

    def realise_create_floating_ip(self, allow_recreate: bool) -> None:
        defn: FloatingIPOptions = self.get_defn().config

        if self.state == self.UP:
            if self._state["location"] != defn.location:
                raise Exception("changing a floating IP's location isn't supported.")
            if not allow_recreate:
                raise Exception(
                    f"{self.full_name} definition changed and it needs to be "
                    "recreated use --allow-recreate if you want to create a new one"
                )
            self.warn("floating IP definition changed, recreating...")
            self._destroy()
            self._client = None

        location = self.get_client().locations.get_by_name(defn.location)

        self.logger.log(f"creating floating IP at {location.description}...")
        response = self.get_client().floating_ips.create(
            name=self.get_default_name(), type=defn.type, home_location=location,
        )
        if response.action:
            response.action.wait_until_finished()

        self.resource_id = response.floating_ip.id
        self.address = response.floating_ip.ip
        self.logger.log(f"IP address is {self.address}")

        with self.depl._db:
            self.state = self.STARTING
            self._state["location"] = defn.location
            self._state["type"] = defn.type

        self.wait_for_resource_available(self.resource_id)

    def realise_modify_description(self, allow_recreate: bool) -> None:
        defn: FloatingIPOptions = self.get_defn().config
        self.logger.log("updating floating IP description")
        self.get_instance().update(description=defn.description)
        with self.depl._db:
            self._state["description"] = defn.description

    def destroy(self, wipe: bool = False) -> bool:
        self._destroy()
        return True
