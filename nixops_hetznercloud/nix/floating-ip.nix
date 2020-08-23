# Configuration specific to Hetzner Cloud Floating IP Resource.
{ config, lib, name, uuid, ... }:

with import ./lib.nix lib;
with lib;

{

  imports = [ ./common-hetznercloud-auth-options.nix ];

  options = {

    description = mkOption {
      default = "";
      type = types.str;
      description = "Hetzner Cloud Floating IP <literal>Description</literal>.";
    };

    type = mkOption {
      default = "ipv4";
      type = types.enum [ "ipv4" "ipv6" ];
      description = "Floating IP protocol type. Choices are 'ipv4' or 'ipv6'.";
    };

    location = mkOption {
      default = null;
      example = "nbg1";
      type = with types; nullOr (enum ["nbg1" "fsn1" "hel1"]);
      description = ''
        The ID of the home location (routing is optimized for that location).
        Choices are 'nbg1', 'fsn1' or 'hel1'.
      '';
    };

    floatingIpId = mkOption {
      default = "";
      type = types.str;
      description = "The Floating IP ID generated from Hetzner Cloud. This is set by NixOps";
    };
    
    address = mkOption {
      default = "";
      type = types.str;
      description = "The Floating IP address generated from Hetzner Cloud. This is set by NixOps";      
    };

  } // import ./common-hetznercloud-options.nix { inherit lib; };

  config._type = "hetznercloud-floating-ip";

}
