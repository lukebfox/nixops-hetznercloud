# Configuration specific to Hetzner Cloud SSH Key Resource.
{ config, lib, name, uuid, ... }:

with import ./lib.nix lib;
with lib;

{

  imports = [ ./common-hetznercloud-auth-options.nix ];

  options = {
    
    publicKey = mkOption {
      example = ''
        ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK0wmN/Cr3JXqmLW7u+g9pTh+wyqDHpSQEIQczXkVx9q me@example.net
      '';
      type = types.str;
      description = "SSH public key";
    };
    
    sshKeyId = mkOption {
      default = "";
      type = types.str;
      description = ''
        The SSH Key id generated from Hetzner Cloud. This is set by NixOps.
      '';
    };
    
  } // import ./common-hetznercloud-options.nix { inherit lib; };
  
  config._type = "hetznercloud-ssh-key";
  
}
