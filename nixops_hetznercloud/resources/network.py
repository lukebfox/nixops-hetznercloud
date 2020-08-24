# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Networks.

import hcloud
from hcloud.networks.domain import NetworkSubnet, NetworkRoute

from nixops.diff import Handler
from nixops.resources import ResourceDefinition
from nixops_hetznercloud.hetznercloud_common import HetznerCloudResourceState


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

    def show_type(self):
        return "{0}".format(self.get_type())


class NetworkState(HetznerCloudResourceState):
    """
    State of a Hetzner Cloud Network.
    """

    _reserved_keys = HetznerCloudResourceState.COMMON_HCLOUD_RESERVED + ["networkId"]

    @classmethod
    def get_type(cls):
        return "hetznercloud-network"

    def __init__(self, depl, name, id):
        super(HetznerCloudResourceState, self).__init__(depl, name, id)
        self.network_id = self.resource_id
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
            handle=self.realise_modify_labels,
        )

    def show_type(self):
        s = super(NetworkState, self).show_type()
        return "{0}".format(s)

    @property
    def resource_id(self):
        return self._state.get("networkId", None)

    def network(self):
        return self.get_client().networks.get_by_id(self.resource_id)

    @property
    def full_name(self):
        return "Hetzner Cloud Network {0} [{1}]".format(
            self.resource_id, self._state.get("name", None)
        )

    def prefix_definition(self, attr):
        return {("resources", "hetznerCloudNetworks"): attr}

    def get_definition_prefix(self):
        return "resources.hetznerCloudNetworks."

    def get_physical_spec(self):
        return {
            "networkId": self.resource_id,
            "ipRange": self._state.get("ipRange", None),
        }

    def cleanup_state(self):
        with self.depl._db:
            self.state = self.MISSING
            self._state["networkId"] = None
            self._state["ipRange"] = None
            self._state["subnets"] = None
            self._state["routes"] = None
            self._state["labels"] = None

    def _check(self):
        if self.resource_id is None:
            return
        try:
            self.get_client().networks.get_by_id(self.resource_id)
        except hcloud.APIException as e:
            if e.code == "not_found":
                self.warn(
                    "{0} was deleted from outside nixops,"
                    " it needs to be recreated...".format(self.full_name)
                )
                self.cleanup_state()
                return
        if self.state == self.STARTING:
            self.wait_for_resource_available(
                self.get_client().networks, self.resource_id
            )

    def _destroy(self):
        self.logger.log("destroying {0}...".format(self.full_name))
        try:
            self.get_client().networks.get_by_id(self.resource_id).delete()
        except hcloud.APIException as e:
            if e.code == "not_found":
                self.warn("{0} was already deleted".format(self.full_name))
            else:
                raise e
        self.cleanup_state()

    def realise_create_network(self, allow_recreate):
        config = self.get_defn()
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

        self.log("creating virtual network '{0}'...".format(name))
        try:
            self.network_id = (
                self.get_client().networks.create(name=name, ip_range=config.ipRange).id
            )
        except hcloud.APIException as e:
            if e.code == "invalid_input":
                raise Exception(
                    "couldn't create Network Resource due to {0}".format(e.message)
                )
            else:
                raise e

        with self.depl._db:
            self.state = self.STARTING
            self._state["networkId"] = self.network_id
            self._state["ipRange"] = config.ipRange

        self.wait_for_resource_available(self.get_client().networks, self.network_id)

    def realise_modify_subnets(self, allow_recreate):
        config = self.get_defn()
        self.logger.log("updating subnets for {0}...".format(self.full_name))

        prev_subnets = set(self._state.get("subnets", []))
        final_subnets = set(config.subnets)

        def delete(ip_range: str):
            subnet = NetworkSubnet(ip_range, "cloud", "eu-central")
            action = self.network().delete_subnet(subnet)
            self.wait_with_progress(action, "deleting subnet {0}".format(ip_range))

        subnets_to_delete = list(prev_subnets - final_subnets)
        if subnets_to_delete:
            self.logger.log_start("deleting subnets...")
            list(map(delete, subnets_to_delete))
            self.logger.log_end("")

        def add(ip_range: str):
            subnet = NetworkSubnet(ip_range, "cloud", "eu-central")
            action = self.network().add_subnet(subnet)
            self.wait_with_progress(action, "adding subnet {0}".format(ip_range))

        subnets_to_add = list(final_subnets - prev_subnets)
        if subnets_to_add:
            self.logger.log_start("adding subnets...")
            list(map(add, subnets_to_add))
            self.logger.log_end("")

        with self.depl._db:
            self._state["subnets"] = list(final_subnets)

    def realise_modify_routes(self, allow_recreate):
        config = self.get_defn()
        self.logger.log("updating routes for {0}...".format(self.full_name))

        prev_routes = set(self._state.get("routes", []))
        final_routes = set(config.routes)

        def delete(route: RouteOptions):
            r = NetworkRoute.from_dict(dict(route))
            action = self.network().delete_route(r)
            self.wait_with_progress(
                action, "deleting route for {0}".format(route.destination)
            )

        routes_to_delete = list(prev_routes - final_routes)
        if routes_to_delete:
            self.logger.log_start("deleting routes...")
            list(map(delete, routes_to_delete))
            self.logger.log_end("")

        def add(route: RouteOptions):
            r = NetworkRoute.from_dict(dict(route))
            action = self.network().add_route(r)
            self.wait_with_progress(
                action, "adding route for {0}".format(route.destination)
            )

        routes_to_add = list(final_routes - prev_routes)
        if routes_to_add:
            self.logger.log_start("adding routes...")
            list(map(add, routes_to_add))
            self.logger.log_end("")

        with self.depl._db:
            self._state["routes"] = list(final_routes)

    def realise_modify_labels(self, allow_recreate):
        config = self.get_defn()
        self.logger.log("updating labels for {0}".format(self.full_name))

        self.get_client().networks.get_by_id(self.resource_id).update(
            labels={**self.get_common_labels(), **dict(config.labels)}
        )
        with self.depl._db:
            self._state["labels"] = dict(config.labels)

    def destroy(self, wipe=False):
        self._destroy()
        return True
