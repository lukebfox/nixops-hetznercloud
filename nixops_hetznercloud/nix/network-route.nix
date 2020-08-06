# Configuration specific to Hetzner Cloud Network Route Resource.
{ config, lib, pkgs, name, uuid, ... }:

with import ./lib.nix lib;
with lib;

{
  
  imports = [ ./common-hetznercloud-auth-options.nix ];

  options = {

    networkId = mkOption {
      example = "resources.hetznerCloudNetworks.myPrivateNet";
      type = resource "hetzner-cloud-network";
      description = "The ID of the Network where the route will be created.";
    };
    
    destination = mkOption {
      example = "10.0.1.0/24";
      type = types.str;
      description = ''
        The destination IP range that this route applies to. If the
        destination IP of a packet falls in this range, it matches
        this route.
      '';
    };
    
    gateway = mkOption {
      example = "10.0.1.2";
      type = types.str;
      description = ''
        The gateway resource to which routed packets are forwarded.
        Must be a hetzner cloud Server instance.
      '';
    };
    
    labels = (import ./common-hetznercloud-options.nix { inherit lib; }).labels;
    
  };
    
  config._type = "hetzner-cloud-network-route";
  
}
