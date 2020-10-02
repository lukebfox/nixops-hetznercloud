# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Networks.

from hcloud import APIException
from hcloud.networks.domain import NetworkSubnet, NetworkRoute

from nixops.diff import Handler
from nixops.resources import ResourceDefinition
from nixops_hetznercloud.hetznercloud_common import HetznerCloudResourceState

from typing import Any, Dict, Sequence, Tuple

from .types.network import NetworkOptions, RouteOptions


def hashable(x: RouteOptions) -> Tuple[str, str]:
    return x.destination, x.gateway


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

    def show_type(self):
        return "{0}".format(self.get_type())


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
        s = super(NetworkState, self).show_type()
        return "{0}".format(s)

    @property
    def full_name(self) -> str:
        return "Hetzner Cloud Network {0}".format(self.resource_id)

    def prefix_definition(self, attr: Any) -> Dict[Sequence[str], Any]:
        return {("resources", "hetznerCloudNetworks"): attr}

    def get_definition_prefix(self) -> str:
        return "resources.hetznerCloudNetworks."

    def get_physical_spec(self) -> Dict[Sequence[str], Any]:
        return {"networkId": self.resource_id}

    def cleanup_state(self) -> None:
        with self.depl._db:
            self.state = self.MISSING
            self.resource_id = None
            self._state["ipRange"] = None
            self._state["subnets"] = None
            self._state["routes"] = None
            self._state["labels"] = None

    def _destroy(self) -> None:
        instance = self.get_instance()
        if instance is not None:
            self.logger.log("destroying {0}...".format(self.full_name))
            instance.delete()
        self.cleanup_state()

    def realise_create_network(self, allow_recreate: bool) -> None:
        defn: NetworkOptions = self.get_defn().config
        name = self.get_default_name()

        if self.state == self.UP:
            if not allow_recreate:
                raise Exception(
                    "{0} definition changed and it needs to be recreated "
                    "use --allow-recreate if you want to create a new one".format(
                        self.full_name
                    )
                )
            self.warn("virtual network definition changed, recreating...")
            self._destroy()
            self._client = None

        self.log_start("creating virtual network '{0}'...".format(name))
        self.resource_id = (
            self.get_client().networks.create(name=name, ip_range=defn.ipRange).id
        )

        with self.depl._db:
            self.state = self.STARTING
            self._state["ipRange"] = defn.ipRange

        self.wait_for_resource_available(self.resource_id)

    def realise_modify_subnets(self, allow_recreate: bool) -> None:
        defn: NetworkOptions = self.get_defn().config

        prev_subnets = set(self._state.get("subnets", []))
        final_subnets = set(defn.subnets)

        for ip_range in prev_subnets - final_subnets:
            subnet = NetworkSubnet(ip_range, "cloud", "eu-central")
            self.logger.log("deleting subnet {0}".format(ip_range))
            self.wait_on_action(self.get_instance().delete_subnet(subnet))

        for ip_range in final_subnets - prev_subnets:
            subnet = NetworkSubnet(ip_range, "cloud", "eu-central")
            self.logger.log("adding subnet {0}".format(ip_range))
            self.wait_on_action(self.get_instance().add_subnet(subnet))

        with self.depl._db:
            self._state["subnets"] = list(final_subnets)

    def realise_modify_routes(self, allow_recreate: bool) -> None:
        defn: NetworkOptions = self.get_defn().config

        instance = self.get_instance()
        prev_routes = set(map(tuple, self._state.get("routes", [])))
        final_routes = set(map(hashable, defn.routes))

        for d1, g1 in prev_routes - final_routes:
            self.logger.log("deleting route for {0}".format(g1))
            self.wait_on_action(instance.delete_route(NetworkRoute(d1, g1)))

        for d2, g2 in final_routes - prev_routes:
            self.logger.log("adding route to {0}".format(g2))
            self.wait_on_action(instance.add_route(NetworkRoute(d2, g2)))

        with self.depl._db:
            self._state["routes"] = list(final_routes)

    def destroy(self, wipe: bool = False) -> bool:
        self._destroy()
        return True
