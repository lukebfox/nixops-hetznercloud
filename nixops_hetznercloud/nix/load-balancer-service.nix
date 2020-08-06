# Configuration specific to Hetzner Cloud Load Balancer Service Resource.
{ config, lib, ... }:

with import ./lib.nix lib;
with lib;

{
  
  options = {
    
    protocol = mkOption {
      default = "http";
      type = types.enum [ "tcp" "http" "https" ];
      description = "Protocol of the underlying traffic for this service.";
    };

    listenPort = mkOption {
      default = 80;
      type = types.int;
      description = ''
        The port the service listens on, i.e. the port users can connect to. For
        HTTP or HTTPS services, the default values are 80 or 443, respectively.
     '';
    };

    destinationPort = mkOption {
      default = 80;
      type = types.int;
      description = ''
        The port traffic is forwarded to, i.e. the port the targets are
        listening and accepting connections on. For HTTP or HTTPS services, 
        the default values are 80 or 443, respectively.
      '';
    };

    healthCheck = mkOption {
      default = null;
      type = with types; nullOr (resource "hetzner-cloud-load-balancer-healthcheck");
      description = ''
        Configuration for health checks. 
        Checks the system status of target servers.
      '';
    };

    proxyProtocol = mkOption {
      default = false;
      type = types.bool;
      description = ''
        Enable the PROXY protocol. Please note that the software running on
        the targets and handling connections needs to support the PROXY
        protocol.
      '';
    };

    stickySessions = mkOption {
      default = null;
      description = ''
        Configuration for Sticky Sessions. Binds a session to a particular
        target server for a configurable time using a cookie. Valid only for
        HTTP/HTTPS services.
      '';
      type = with types; nullOr (submodule {
        options = {
          cookieName = mkOption {
            default = "HCLBSTICKY";
            type = types.str;
            description = ''
              Arbitrary name for the cookie which tracks the sticky session.
            '';
          };
          cookieLifetime = mkOption {
            default = 300;
            type = types.int;
            description = ''
              Time in seconds to bind the session to the target server.
              Limits are between 10 seconds and 86400 seconds (1 day).
            '';
          };
        };
      });
    };
    
    certificates = mkOption {
      type = types.listOf (resource "hetzner-cloud-certificate");
      description = ''
        TODO.
        Valid only for https services.
      '';
    };
    
    redirectHttp = mkOption {
      default = false;
      type = types.bool;
      description = ''
        Redirect all HTTP requests to this HTTPS service. Valid only for HTTPS
        services.
      '';
    };
    
  };
  
  config._type = "hetzner-cloud-load-balancer-service";
  
}
