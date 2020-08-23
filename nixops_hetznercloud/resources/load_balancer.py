# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Load Balancers.

# import hcloud
# import time

# from nixops.diff import Handler
from nixops.util import attr_property
from nixops.resources import ResourceDefinition, ResourceState, DiffEngineResourceState
from nixops_hetznercloud.resources.hetznercloud_common import HetznerCloudCommonState

from .types.load_balancer import HetznerCloudLoadBalancerOptions


class HetznerCloudLoadBalancerDefinition(ResourceDefinition):
    """
    Definition of a Hetzner Cloud load balancer.
    """

    config: HetznerCloudLoadBalancerOptions

    @classmethod
    def get_type(cls):
        return "hetznercloud-load-balancer"

    @classmethod
    def get_resource_type(cls):
        return "hetznerCloudLoadBalancers"

    def show_type(self):
        return "{0}".format(self.get_type())


class HetznerCloudLoadBalancerState(DiffEngineResourceState, HetznerCloudCommonState):
    """
    State of a Hetzner Cloud Network.
    """

    state = attr_property("state", ResourceState.MISSING, int)
    api_token = attr_property("apiToken", None)
    _reserved_keys = HetznerCloudCommonState.COMMON_HCLOUD_RESERVED + ["loadBalancerId"]
