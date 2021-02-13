# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Networks.

from hcloud.networks.domain import Network, NetworkSubnet, NetworkRoute
from nixops.diff import Handler
from nixops.resources import ResourceDefinition
from nixops_hetznercloud.hetznercloud_common import HetznerCloudResourceState

from typing import Any, Dict, Sequence

from .types.network import NetworkOptions, RouteOptions


class NetworkDefinition(ResourceDefinition):
    """
    Definition of a Hetzner Cloud virtual network.
    """

    config: NetworkOptions

    @classmethod
    def get_type(cls):
        return "hetznercloud-network"

    @classmethod
    def get_resource_type(cls):
        return "hetznerCloudNetworks"


class NetworkState(HetznerCloudResourceState):
    """
    State of a Hetzner Cloud Network.
    """

    definition_type = NetworkDefinition

    _resource_type = "networks"
    _reserved_keys = HetznerCloudResourceState.COMMON_HCLOUD_RESERVED

    @classmethod
    def get_type(cls):
        return "hetznercloud-network"

    def __init__(self, depl, name, id):
        super(HetznerCloudResourceState, self).__init__(depl, name, id)
        self.handle_create_network = Handler(
            ["ipRange"], handle=self.realise_create_network,
        )
        self.handle_modify_subnets = Handler(
            ["subnets"],
            after=[self.handle_create_network],
            handle=self.realise_modify_subnets,
        )
        self.handle_modify_routes = Handler(
            ["routes"],
            after=[self.handle_modify_subnets],
            handle=self.realise_modify_routes,
        )
        self.handle_modify_labels = Handler(
            ["labels"],
            after=[self.handle_modify_subnets, self.handle_modify_routes],
            handle=super().realise_modify_labels,
        )

    def show_type(self):
        return f"{super(NetworkState, self).show_type()}"

    @property
    def full_name(self) -> str:
        return f"Hetzner Cloud Network {self.resource_id}"

    def prefix_definition(self, attr: Any) -> Dict[Sequence[str], Any]:
        return {("resources", "hetznerCloudNetworks"): attr}

    def get_definition_prefix(self) -> str:
        return "resources.hetznerCloudNetworks."

    def cleanup_state(self) -> None:
        with self.depl._db:
            self.state = self.MISSING
            self.resource_id = None
            self._state["ipRange"] = None
            self._state["subnets"] = None
            self._state["routes"] = None
            self._state["labels"] = None

    def realise_create_network(self, allow_recreate: bool) -> None:
        defn: NetworkOptions = self.get_defn().config
        name = self.get_default_name()

        if self.state == self.UP:
            if not allow_recreate:
                raise Exception(
                    f"{self.full_name} definition changed and it needs to be "
                    "recreated use --allow-recreate if you want to create a new one"
                )
            self.warn("virtual network definition changed, recreating...")
            self._destroy()
            self._client = None

        self.log_start(f"creating virtual network '{name}'...")
        self.resource_id = (
            self.get_client().networks.create(name=name, ip_range=defn.ipRange).id
        )

        with self.depl._db:
            self.state = self.STARTING
            self._state["ipRange"] = defn.ipRange

        self.wait_for_resource_available(self.resource_id)

    def realise_modify_subnets(self, allow_recreate: bool) -> None:
        defn: NetworkOptions = self.get_defn().config

        prev_subnets = set(self._state.get("subnets", ()))
        final_subnets = set(defn.subnets)

        for ip_range in prev_subnets - final_subnets:
            self.logger.log(f"deleting subnet {ip_range}")
            self.wait_on_action(
                self.get_client().networks.delete_subnet(
                    network=Network(self.resource_id),
                    subnet=NetworkSubnet(ip_range, "cloud", "eu-central")
                )
            )

        for ip_range in final_subnets - prev_subnets:
            self.logger.log(f"adding subnet {ip_range}")
            self.wait_on_action(
                self.get_client().networks.add_subnet(
                    network=Network(self.resource_id),
                    subnet=NetworkSubnet(ip_range, "cloud", "eu-central")
                )
            )

        with self.depl._db:
            self._state["subnets"] = list(defn.subnets)

    def realise_modify_routes(self, allow_recreate: bool) -> None:
        defn: NetworkOptions = self.get_defn().config

        # workaround to get hashable types
        # TODO patch nixops StateDict getter for dicts (if appropriate)
        prev_routes = {RouteOptions(**x) for x in self._state.get("routes", ())}
        final_routes = set(defn.routes)

        for route in prev_routes - final_routes:
            self.logger.log(f"deleting route for {route.gateway}")
            self.wait_on_action(
                self.get_client().networks.delete_route(
                    network=Network(self.resource_id),
                    route=NetworkRoute(route.destination, route.gateway)
                )
            )

        for route in final_routes - prev_routes:
            self.logger.log(f"adding route to {route.gateway}")
            self.wait_on_action(
                self.get_client().networks.add_route(
                    network=Network(self.resource_id),
                    route=NetworkRoute(route.destination, route.gateway)
                )
            )

        # Why must we insert as a list when the original type (tuple) is json encodable?
        # StateDict setter accepts inserting lists and dicts for legacy reasons.
        # TODO patch nixops to encode tuples (in addition, for backwards compat)
        with self.depl._db:
            self._state["routes"] = list(defn.routes)
