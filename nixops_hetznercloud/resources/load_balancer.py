# -*- coding: utf-8 -*-

# Automatic provisioning of Hetzner Cloud Load Balancers.

import hcloud

from nixops.diff import Handler
from nixops.resources import ResourceDefinition
from nixops_hetznercloud.hetznercloud_common import HetznerCloudResourceState

from .types.load_balancer import LoadBalancerOptions


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

    def show_type(self):
        return "{0}".format(self.get_type())


class LoadBalancerState(HetznerCloudResourceState):
    """
    State of a Hetzner Cloud Load Balancer.
    """

    definition_type = LoadBalancerDefinition

    _resource_type = "load_balancers"
    _reserved_keys = HetznerCloudResourceState.COMMON_HCLOUD_RESERVED
