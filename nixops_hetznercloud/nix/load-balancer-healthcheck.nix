# Configuration specific to Hetzner Cloud Load Balancer Healthcheck Resource.
{ config, lib, ... }:

with import ./lib.nix lib;
with lib;

{
  
  options = {
    
    protocol = mkOption {
      default = "http";
      type = types.enum ["tcp" "http" ];
      description = ''
        Protocol used by the health check. Choices are 'http' or 'tcp'.
      '';
    };

    port = mkOption {
      default = 80;
      type = types.int;
      description = ''
        The port the health check request is forwarded to.
      '';
    };

    interval = mkOption {
      default = 15;
      type = types.int;
      description = ''
        Health check interval in seconds. Limits are from 3 seconds to 60
        seconds.
      '';
    };

    timeout = mkOption {
      default = 10;
      type = types.int;
      description = ''
        Health check timeout in seconds. Limits are from 1 second to the health
        check interval.
      '';
    };

    retries = mkOption {
      default = 3;
      type = types.enum [ 1 2 3 4 5 ];
      description = "Health check retries. Valid values are from 1 to 5.";
    };

    http = mkOption {
      default = null;
      description = "Options for health checks using HTTP.";
      type = with types; nullOr (submodule {
        options = {
          
          domain = mkOption {
            example = "example.com";
            type = types.str;
            description = "Domain to query for the health check.";
          };

          path = mkOption {
            default = "/";
            type = types.str;
            description = "Path to query for the health check.";
          };

          response = mkOption {
            default = "{ \\\"status\\\": \\\"ok\\\" }";
            type = types.str;
            description = ''
              Custom string that must be contained as substring in HTTP response
              in order to pass the health check.
            '';
          };

          statusCodes = mkOption {
            default = [ "2??" "3??" ];
            type = types.listOf types.str;
            description = ''
              Returned HTTP Status codes in order to pass the health check.
              Supports the wildcards '?' for exactly one character and '*' for
              multiple ones.
            '';
          };

          tls = mkOption {
            default = false;
            type = types.bool;
            description = "Use HTTPS for health check.";
          };

        };
      });
    };
    
  };

  config._type = "hetzner-cloud-load-balancer-healthcheck";
  
}
