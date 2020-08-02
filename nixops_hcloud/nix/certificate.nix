# Configuration specific to Hetzner Cloud Certificate Resource.
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
      description = "Hetzner Cloud Certificate <literal>Name</literal>.";
    };
    
    certificate = mkOption {
      example = ''
        -----BEGIN CERTIFICATE-----
        MIIDMDCCAhigAwIBAgIIJgROscP8RRUwDQYJKoZIhvcNAQELBQAwIDEeMBwGA1UE
        ...
        TKS8gQ==
        -----END CERTIFICATE-----
      '';
      type = types.str;
      description = ''
        Certificate and chain in PEM format, in order so that each record
        directly certifies the one preceding.
      '';
    };

    privateKey = mkOption {
      example = ''
        -----BEGIN RSA PRIVATE KEY-----
        MIIEpQIBAAKCAQEAorPccsHibgGLJIub5Sb1yvDvARifoKzg7MIhyAYLnJkGn9B1
        ...
        AHcjLFCNvobInLHTTmCoAxYBmEv2eakas0+n4g/LM2Ukaw1Bz+3VrVo=
        -----END RSA PRIVATE KEY-----
      '';
      type = types.str;
      description = "Certificate key in PEM format";
    };
    
    labels = (import ./common-hcloud-options.nix { inherit lib; }).labels;
    
  };
  
  ##### implementation
  config = {
  };
  
  config._type = "hcloud-certificate";
  
}
