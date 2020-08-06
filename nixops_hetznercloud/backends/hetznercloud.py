# -*- coding: utf-8 -*-

# import os
# import time
# import sys
# import hcloud

from nixops.util import attr_property
from nixops.backends import MachineDefinition, MachineState
# from nixops.resources import ResourceDefinition, ResourceState
import nixops.deployment
from nixops.backends import DiffEngineMachineState

from nixops_hetznercloud.resources.hetznercloud_common import HetznerCloudCommonState
# import nixops_hetznercloud.hetznercloud_utils
# import nixops_hetznercloud.resources

from typing import Optional

from .options import HetznerCloudMachineOptions


class HetznerCloudDefinition(MachineDefinition):
    """
    Definition of a Hetzner Cloud machine.
    """

    config: HetznerCloudMachineOptions

    @classmethod
    def get_type(cls):
        return "hetznerCloud"

    def __init__(self, name: str, config: nixops.resources.ResourceEval):
        super().__init__(name, config)
        self.api_token = self.config.hetznerCloud.apiToken
        self.location = self.config.hetznerCloud.location
        self.server_name = self.config.hetznerCloud.serverName
        self.server_type = self.config.hetznerCloud.serverType
        self.labels = dict(self.config.hetznerCloud.labels)

    def show_type(self):
        return "{0} [{1}]".format(self.get_type(), self.location or "???")


class HetznerCloudState(DiffEngineMachineState[HetznerCloudDefinition], HetznerCloudCommonState):
    """
    State of a Hetzner Cloud machine.
    """

    @classmethod
    def get_type(cls):
        return "hetznerCloud"

    state = attr_property("state", DiffEngineMachineState.MISSING, int)  # override

    def __init__(self, depl: nixops.deployment.Deployment, name: str, id):
        MachineState.__init__(self, depl, name, id)

    # TODO
    def _reset_state(self):
        """
        Discard all state pertaining to an instance.
        TODO Also used in aws plugin.
        """

    # DONE
    def show_type(self):
        s = super(HetznerCloudState, self).show_type()
        if self.datacenter or self.location:
            s = "{0} [{1}; {2}]".format(s, self.location, self.instance_type)
        return s

    # DONE
    @property
    def resource_id(self) -> Optional[str]:
        return self.vm_id


"""
# AWS methods
_connect
_reset_state
show_type
resource_id
get_ssh_name
get_console_output
get_backups
get_keys
get_physical_spec
get_physical_backup_spec
get_ssh_private
get_ssh_flags
update_block_device_mapping
create
create_after
restore
destroy
start
stop
reboot
backup
_check

_connect_boto3
_connect_vpc
_connect_route53
_get_spot_instance
_get_instance
_get_snapshot_by_id
_wait_for_ip
_ip_for_ssh_key
_delete_volume
_assign_elastic_ip
_wait_for_spot_request_fulfillment
_cancel_spot_request
_retry_route53
_update_route53
after_activation
attach_volume
create_instance
check_stopped
next_charge_time
security_groups_to_ids
remove_backup
wait_for_snapshot_to_become_completed
"""


"""
# GCE methods
resourceId
show_type
get_backups
get_console_output
get_keys
get_ssh_name
get_ssh_private_key_file
get_ssh_flags
update_block_device_mapping
create
create_after
restore
destroy
start
stop
reboot
backup
_check

full_name
node
address_to
full_metadata
gen_metadata
_delete_volume
_node_deleted
is_deployed
create_node
after_activation
wait_for_snapshot_initiated
remove_backup
get_physical_spec
get_physical_backup_spec
"""


"""
# Packet Method
connect
resource_id
get_keys
get_ssh_name
get_ssh_private_key_file
get_ssh_flags
create
create_after
destroy
get_physical_spec

get_sos_ssh_name
get_physical_spec_from_plan
op_sos_console
op_reinstall
get_common_tags
op_update_provSystem
update_provSystem
update_metadata
packetstate2state
findKeypairResource
create_device
wait_for_state
"""


"""
# Hetzner Methods
connect
resource_id
get_physical_spec
get_ssh_name
get_ssh_password
get_ssh_flags
public_ipv4
create
destroy
start
stop
reboot
reboot_rescue
_check

_get_robot_user_and_pass
get_server_from_main_robot
_get_server_by_ip
_wait_for_rescue
_bootstrap_rescue_for_existing_system
_bootstrap_rescue
calculate_ipv4_subnet
_install_base_system
_detect_hardware
_switch_to_configuration
_get_ethernet_interfaces
_get_udev_rule_for
_get_ipv4_addr_and_prefix_for
_get_default_gw
_get_nameservers
_indent
_gen_network_spec
_wait_stop
_destroy
"""


"""
# HetznerCloud Method
connect
resource_id
get_keys
get_ssh_name
get_ssh_private_key_file
get_ssh_flags
create
create_after
destroy
get_physical_spec
"""
