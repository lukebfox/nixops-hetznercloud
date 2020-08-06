# Configuration specific to Hetzner Cloud Network Resource.
{ config, lib, pkgs, name, uuid, ... }:

with import ./lib.nix lib;
with lib;

{
  imports = [ ./common-hetznercloud-auth-options.nix ];

  options = {
    
    name = {
      default = "nixops-${uuid}-${name}";
      example = "myPrivateNet";
      type = types.str;
      description = "Hetzner Cloud Network <literal>Name</literal>.";
    };

    cidrBlock = {
      example = "10.0.0.0/16";
      type = types.str;
      description = ''
        The range of internal addresses that are legal on this network.
        This range is a <link xlink:href="http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing">CIDR</link> specification.
      '';
    };

    labels = (import ./common-hetznercloud-options.nix { inherit lib; }).labels;
    
  };
    
  config._type = "hetzner-cloud-network";
  
}
