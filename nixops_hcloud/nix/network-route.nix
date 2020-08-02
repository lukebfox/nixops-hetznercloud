# Configuration specific to Hetzner Cloud Network Route Resource.
{ config, lib, pkgs, name, uuid, ... }:

with import ./lib.nix lib;
with lib;

{
  
  imports = [ ./common-hcloud-auth-options.nix ];

  ##### interface
  options = {

    networkId = mkOption {
      type = resource "hcloud-network";
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
      example = "10.0.1.1";
      type = types.str;
      description = ''
        The gateway resource to which routed packets are forwarded.
        Must be a hetzner cloud server instance.
      '';
    };
    
    labels = (import ./common-hcloud-options.nix { inherit lib; }).labels;
    
  };
  
  ##### implementation
  config = {
  };
  
  config._type = "hcloud-network-route";
  
}
