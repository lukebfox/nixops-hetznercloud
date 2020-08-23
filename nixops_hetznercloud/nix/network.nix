# Configuration specific to Hetzner Cloud Network Resource.
{ config, lib, name, uuid, ... }:

with import ./lib.nix lib;
with lib;

{
  
  imports = [ ./common-hetznercloud-auth-options.nix ];

  options = {

    ipRange = mkOption {
      example = "10.0.0.0/16";
      type = types.str;
      description = ''
        The range of internal addresses that are legal on this network.
        This range is a <link xlink:href="http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing">CIDR</link> specification.
      '';
    };

    subnets = mkOption {
      default = [];
      example = ["10.0.1.0/24" "10.0.2.0/24" "10.0.3.0/24"];
      type = types.listOf types.str;
      description = "List of ip ranges defining the subnets for this Network.";
    };

    routes = mkOption {
      default = [];
      type = types.listOf (types.submodule {
        options = {
          destination = mkOption {
            example = "10.0.100.0/24";
            type = types.str;
            description = ''
              The destination IP range that this route applies to. If the
              destination IP of a packet falls in this range, it matches
              this route.
            '';
          };
          gateway = mkOption {
            example = "10.0.1.100";
            type = types.str;
            description = ''
              The gateway resource to which routed packets are forwarded.
              Must be a hetzner cloud Server instance.
            '';
          };
        };
      });
    };

    networkId = mkOption {
      default = "";
      type = types.str;
      description = ''
        The Network ID generated from Hetzner Cloud. This is set by NixOps
      '';
    };
    
  } // import ./common-hetznercloud-options.nix { inherit lib; };
    
  config._type = "hetznercloud-network";
  
}
