# -*- coding: utf-8 -*-

import os
import os.path
import time
import sys

import nixops.util

from nixops.util import attr_property, create_key_pair
from nixops.backends import MachineOptions, MachineDefinition, MachineState
from nixops.resources import ResourceOptions#, ResourceDefinition, ResourceState

from nixops_hcloud.hcloud_common import ResourceDefinition, ResourceState

import nixops_hcloud.hcloud_utils
import nixops_hcloud.resources

import hcloud

from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Union
from typing_extensions import Literal


class HCloudOptions(ResourceOptions):
    name: str
    server_type: str
    volumes: Optional[Sequence[str]]
    networks: Optional[Sequence[str]]
    user_data: str
    labels: Optional[Mapping[str,str]]
    location: Union[Literal["Nuremberg"],Literal["Falkenstein"],Literal["Helsinki"]]    


class HCloudMachineOptions(MachineOptions):
    hcloud: HCloudOptions


class HCloudDefinition(MachineDefinition):
    """
    Definition of a Hetzner Cloud machine.
    """
    
    config: HCloudMachineOptions

    @classmethod
    def get_type(cls):
        return "hcloud"
    
    def __init__(self, name: str, config: nixops.resources.ResourceEval):
        super().__init__(name, config)

        if self.config.hcloud.accessKeyId is None:
            self.access_key_id = os.environ["HCLOUD_API_TOKEN"]
        else:
            self.access_key_id = self.config.hcloud.accessKeyId
            
        self.machine_name = self.config.hcloud.machineName

        self.location self.config.hcloud.location

        self.server_type = self.config.hcloud.server_type
        
        #self.volumes = self.config.hcloud.volumes

        #self.ipAddress = self.config.hcloud.ipAddress
        #self.network = self.config.hcloud.network
        #self.subnet = self.config.gce.subnet
        self.labels = dict(self.config.hcloud.labels)
        
            
        def show_type(self):
          return "{0} [{1}]".format(self.get_type(), self.location or "???")

    def 


class HCloudState(MachineState[HCloudDefinition], ResourceState):
    """ State of a Hetzner Cloud machine.  """

    @classmethod
    def get_type(cls):
        return "hcloud"
    
    def __init__(self, depl: nixops.deployment.Deployment, name: str, id):
        MachineState.__init__(self, depl, name, id)
        self.name = name
        self._conn = None

    #TODO
    def _reset_state(self):
        """
        Discard all state pertaining to an instance.
        TODO Also used in aws plugin.
        """

    #DONE
    def show_type(self):
        s = super(HCloudState, self).show_type()
        if self.datacenter or self.location:
            s = "{0} [{1}; {2}]".format(s, self.location, self.instance_type)
        return s

    #DONE
    @property
    def resource_id(self) -> Optional[str]:
        return self.vm_id

    #GROK
    def get_physical_spec(self):
        return (
            {
                (
                    "config",
                    "users",
                    "extraUsers",
                    "root",
                    "openssh",
                    "authorizedKeys",
                    "keys",
                ): [self._ssh_public_key]
            }
            if self._ssh_public_key
            else {}
        )

    
    #TODO
    def create(
        self,
        defn: NoneDefinition,
        check: bool,
        allow_reboot: bool,
        allow_recreate: bool,
    ):
        assert isinstance(defn, NoneDefinition)
        self.set_common_state(defn)
        self.target_host = defn._target_host
        self.public_ipv4 = defn._public_ipv4

        if not self.vm_id:
            if self.provision_ssh_key:
                self.log_start("generating new SSH key pair... ")
                key_name = "NixOps client key for {0}".format(self.name)
                self._ssh_private_key, self._ssh_public_key = create_key_pair(
                    key_name=key_name
                )

            self.log_end("done")
            self.vm_id = "nixops-{0}-{1}".format(self.depl.uuid, self.name)

    #TODO
    def switch_to_configuration(self, method, sync, command=None):
        res = super(NoneState, self).switch_to_configuration(method, sync, command)
        if res == 0:
            self._ssh_public_key_deployed = True
        return res

    #TODO
    def get_ssh_name(self):
        assert self.target_host
        return self.target_host

    #TODO
    def get_ssh_private_key_file(self) -> Optional[str]:
        if self._ssh_private_key_file:
            return self._ssh_private_key_file
        elif self._ssh_private_key:
            return self.write_ssh_private_key(self._ssh_private_key)
        return None

    #TODO
    def get_ssh_flags(self, *args, **kwargs):
        super_state_flags = super(NoneState, self).get_ssh_flags(*args, **kwargs)
        if self.vm_id and self.cur_toplevel and self._ssh_public_key_deployed:
            key_file = self.get_ssh_private_key_file()
            flags = super_state_flags + [
                "-o",
                "StrictHostKeyChecking=accept-new",
            ]
            if key_file:
                flags = flags + ["-i", key_file]
            return flags

        return super_state_flags


    #TODO
    def _check(self, res):
        if not self.vm_id:
            res.exists = False
            return
        
        res.exists = True
        res.is_up = self.ping()
        if res.is_up:
            super()._check(res)

    def destroy(self, wipe=False):
        # No-op; just forget about the machine.
        return True



    def reboot(self, hard=False):
        self.log("rebooting HCloud machine...")
        instance = self._get_instance()
        instance.reset() if hard else instance.reboot()
        
        self.state = self.STARTING













    

'''
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
'''



'''
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
'''



'''
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
'''



'''
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
'''


'''
# HCloud Method
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

'''
