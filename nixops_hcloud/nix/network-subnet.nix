# Configuration specific to Hetzner Cloud Network Subnet Resource.
{ config, lib, pkgs, name, uuid, ... }:

with import ./lib.nix lib;
with lib;

{
  imports = [ ./common-hcloud-auth-options.nix ];

  ##### interface
  options = {
    
    networkId = mkOption {
      type = resource "network";
      description = "The ID of the Network where the subnet will be created.";
    };
    
    ipRange = mkOption {
      example = "10.0.1.0/24";
      type = types.listOf types.str;
      description = "Subnet range";
    };
    
  };
  
  ##### implementation
  config = {
  };
  
  config._type = "hcloud-network-subnet";
  
}
