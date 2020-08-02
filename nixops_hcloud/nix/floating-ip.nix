# Configuration specific to Hetzner Cloud Floating IP Resource.
{ config, lib, name, uuid ... }:

with import ./lib.nix lib;
with lib;

{

  imports = [ ./common-hcloud-auth-options.nix ];

  ##### interface
  options = {
    
    name = mkOption {
      default = "nixops-${uuid}-${name}";
      type = types.str;
      description = "Hetzner Cloud Floating IP <literal>Name</literal>.";
    };

    location = (import ./common-hcloud-options.nix { inherit lib; }).location;

    protocol = mkOption {
      default = "ipv4";
      type = types.enum [ "ipv4" "ipv6" ];
      description = "Floating IP protocol type. Choices are 'ipv4' or 'ipv6'.";
    };
    
    serverId = mkOption {
      default = null;
      type = types.nullOr machine;
      description = ''
        TODO
      '';
    };

    labels = (import ./common-hcloud-options.nix { inherit lib; }).labels;
    
  };
  
  ##### implementation
  config = {
  };
  
  config._type = "hcloud-floating-ip";
  
}
