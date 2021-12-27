# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Load Balancers.
#
from hcloud.servers.domain import Server
from hcloud.networks.domain import Network
from hcloud.load_balancers.domain import (
    CreateLoadBalancerResponse,
    LoadBalancer,
    LoadBalancerAlgorithm,
    # LoadBalancerService,
    # LoadBalancerServiceHttp,
    # LoadBalancerHealthCheck,
    # LoadBalancerHealtCheckHttp,
    LoadBalancerTarget,
)
from hcloud.load_balancer_types.client import BoundLoadBalancerType
from hcloud.locations.client import BoundLocation

from nixops.diff import Handler

from nixops.resources import ResourceDefinition
from nixops_hetznercloud.backends.hetznercloud import (
    HetznerCloudDefinition,
    HetznerCloudState,
)
from nixops_hetznercloud.resources.network import NetworkState
from nixops_hetznercloud.hetznercloud_common import HetznerCloudResourceState
from typing import Any, Dict, Sequence, Set, Type
from .types.load_balancer import (
    HealthCheckOptions,
    StickySessionOptions,
    ServiceOptions,
    TargetOptions,
    LoadBalancerOptions,
)


class LoadBalancerDefinition(ResourceDefinition):
    """
    Definition of a Hetzner Cloud load balancer.
    """

    config: LoadBalancerOptions

    @classmethod
    def get_type(cls):
        return "hetznercloud-load-balancer"

    @classmethod
    def get_resource_type(cls):
        return "hetznerCloudLoadBalancers"


class LoadBalancerState(HetznerCloudResourceState):
    """
    State of a Hetzner Cloud Load Balancer.
    """

    definition_type = LoadBalancerDefinition

    _resource_type = "load_balancers"
    _reserved_keys = HetznerCloudResourceState.COMMON_HCLOUD_RESERVED

    @classmethod
    def get_type(cls):
        return "hetznercloud-load-balancer"

    def __init__(self, depl, name, id):
        super(HetznerCloudResourceState, self).__init__(depl, name, id)
        self.handle_create_load_balancer = Handler(
            ["location", "loadBalancerType"], handle=self.realise_create_load_balancer,
        )
        self.handle_modify_algorithm = Handler(
            ["algorithm"],
            handle=self.realise_modify_algorithm,
            after=[self.handle_create_load_balancer],
        )
        self.handle_modify_labels = Handler(
            ["labels"],
            handle=self.realise_modify_labels,
            after=[self.handle_create_load_balancer],
        )
        self.handle_modify_network = Handler(
            ["network"],
            handle=self.realise_modify_network,
            after=[self.handle_create_load_balancer],
        )
        self.handle_modify_public_interface = Handler(
            ["enablePublicInterface"],
            handle=self.realise_modify_public_interface,
            after=[self.handle_modify_network],
        )
        self.handle_modify_targets = Handler(
            ["targets"],
            handle=self.realise_modify_targets,
            after=[self.handle_modify_network],
        )
        self.handle_modify_services = Handler(
            ["services"],
            handle=self.realise_modify_services,
            after=[self.handle_modify_targets],
        )

    def show_type(self):
        s = f"{super(LoadBalancerState, self).show_type()}"
        if self.state == self.UP:
            location = self._state.get("location", None)
            s += f" [{location}]"
        return s

    @property
    def full_name(self) -> str:
        location = self._state.get("location", None)
        return f"Hetzner Cloud Load Balancer {self.resource_id} [{location}]"

    def prefix_definition(self, attr: Any) -> Dict[Sequence[str], Any]:
        return {("resources", "hetznerCloudLoadBalancers"): attr}

    def get_definition_prefix(self) -> str:
        return "resources.hetznerCloudLoadBalancers."

    def get_physical_spec(self) -> Dict[str, Any]:
        s = super(LoadBalancerState, self).get_physical_spec()
        return s

    def create_after(self, resources, defn: HetznerCloudDefinition) -> Set[Any]:
        return {
            r
            for r in resources
            if isinstance(r, NetworkState) or isinstance(r, HetznerCloudState)
        }

    def cleanup_state(self) -> None:
        with self.depl._db:
            self.state = self.MISSING
            self.resource_id = None
            self._state["loadBalancerType"] = None
            self._state["name"] = None
            self._state["network"] = None
            self._state["targets"] = None
            self._state["services"] = None
            self._state["algorithm"] = None
            self._state["enablePublicInterface"] = None
            self._state["location"] = None
            self._state["labels"] = None

    def realise_create_load_balancer(self, allow_recreate: bool) -> None:
        defn: LoadBalancerOptions = self.get_defn().config

        if self.state == self.UP:
            if self._state["location"] != defn.location:
                raise Exception("changing a load balancers's location isn't supported.")
            if not allow_recreate:
                raise Exception(
                    f"{self.full_name} definition changed and it needs to be"
                    " recreated use --allow-recreate if you want to create a"
                    " new one"
                )
            self.warn("load balancer definition changed, recreating...")
            self._destroy()
            self._client = None

        location: BoundLocation = self.get_client().locations.get_by_name(defn.location)
        load_balancer_type: BoundLoadBalancerType = self.get_client().load_balancer_types.get_by_name(
            defn.loadBalancerType
        )

        self.logger.log(f"creating load balancer at {location.description}...")
        response: CreateLoadBalancerResponse = self.get_client().load_balancers.create(
            name=self.get_default_name(),
            load_balancer_type=load_balancer_type,
            algorithm=LoadBalancerAlgorithm(defn.algorithm),
            location=location,
        )

        response.action and response.action.wait_until_finished()

        self.resource_id = response.load_balancer.id
        with self.depl._db:
            self.state = self.STARTING
            self._state["location"] = defn.location
            self._state["loadBalancerType"] = defn.loadBalancerType
            self._state["algorithm"] = defn.algorithm

        self.wait_for_resource_available(self.resource_id)

    def realise_modify_algorithm(self, allow_recreate: bool) -> None:
        defn: LoadBalancerOptions = self.get_defn().config

        self.logger.log(f"changing algorithm to {defn.algorithm}...")
        self.get_client().load_balancers.change_algorithm(
            load_balancer=LoadBalancer(self.resource_id),
            algorithm=LoadBalancerAlgorithm(defn.algorithm),
        )

        with self.depl._db:
            self._state["algorithm"] = defn.algorithm

    def realise_modify_network(self, allow_recreate: bool) -> None:
        defn: LoadBalancerOptions = self.get_defn().config

        instance = self.get_instance()
        if instance.private_net:
            prev_network_id = instance.private_net[0].network.id
            self.logger.log(
                f"detaching {self.full_name} from network {prev_network_id}"
            )
            instance.detach_from_network(Network(prev_network_id))

        if defn.network is not None:
            res: NetworkState = self.get_hetznercloud_resource(
                defn.network, "hetznercloud-network", NetworkState
            )
            self.logger.log(f"attaching {self.full_name} to network {res.resource_id}")
            instance.attach_to_network(Network(res.resource_id))

        with self.depl._db:
            self._state["network"] = defn.network

    def realise_modify_public_interface(self, allow_recreate: bool) -> None:
        defn: LoadBalancerOptions = self.get_defn().config

        if defn.enablePublicInterface:
            self.logger.log("enabling public interface")
            self.get_client().load_balancers.enable_public_interface(
                LoadBalancer(self.resource_id)
            )
        else:
            self.logger.log("disabling public interface")
            self.get_client().load_balancers.disable_public_interface(
                LoadBalancer(self.resource_id)
            )

        with self.depl._db:
            self._state["enablePublicInterface"] = defn.enablePublicInterface

    def realise_modify_targets(self, allow_recreate: bool) -> None:
        defn: LoadBalancerOptions = self.get_defn().config

        prev_targets = {TargetOptions(**x) for x in self._state.get("targets", ())}
        final_targets = set(defn.targets)

        for target in prev_targets - final_targets:
            self.logger.log(f"removing target {target.machine}")
            res = self.depl.get_machine(
                name=target.machine.split("-")[6], type=Type[HetznerCloudState],
            )
            self.get_client().load_balancers.remove_target(
                load_balancer=LoadBalancer(self.resource_id),
                target=LoadBalancerTarget(
                    type="server",
                    server=Server(res.vm_id),
                    use_private_ip=target.usePrivateIp,
                ),
            )

        for target in final_targets - prev_targets:
            self.logger.log(f"adding target {target.machine}")
            res = self.depl.get_machine(
                name=target.machine.split("-")[6], type=Type[HetznerCloudState]
            )
            self.get_client().load_balancers.add_target(
                load_balancer=LoadBalancer(self.resource_id),
                target=LoadBalancerTarget(
                    type="server",
                    server=Server(res.vm_id),
                    use_private_ip=target.usePrivateIp,
                ),
            )

        with self.depl._db:
            self._state["targets"] = list(defn.targets)

    def realise_modify_services(self, allow_recreate: bool) -> None:
        defn: LoadBalancerOptions = self.get_defn().config

        self.logger.log("updating services")

        prev_services = set(
            map(self.parse_service_options, self._state.get("services", ()))
        )
        final_services = set(defn.services)

        # seems like lsiten post is the distinguishing service attribute.
        for service in prev_services - final_services:
            pass

        for service in final_services - prev_services:
            pass

        with self.depl._db:
            self._state["services"] = list(defn.services)

    def parse_service_options(self, service: Dict[str, Any]) -> ServiceOptions:
        result: Dict[str, Any] = {}
        for k, v in service.items():
            if k == "healthCheck":
                result[k] = HealthCheckOptions(**v)
            elif k == "stickySessions":
                result[k] = StickySessionOptions(**v)
            else:
                result[k] = v
        return ServiceOptions(**result)
