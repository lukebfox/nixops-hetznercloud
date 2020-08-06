# Configuration specific to Hetzner Cloud Network Subnet Resource.
{ config, lib, ... }:

with import ./lib.nix lib;
with lib;

{
  imports = [ ./common-hetzner-cloud-auth-options.nix ];

  options = {
    
    networkId = mkOption {
      example = "resources.hetznerCloudNetworks.myPrivateNet";
      type = resource "network";
      description = "The ID of the Network which this subnet belongs to.";
    };
    
    ipRange = mkOption {
      example = "10.0.1.0/24";
      type = types.str;
      description = "The IP range that this subnet defines.";
    };
    
  };
    
  config._type = "hetzner-cloud-network-subnet";
  
}
