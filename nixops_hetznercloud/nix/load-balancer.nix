# Configuration specific to Hetzner Cloud Load Balancer Resource.
{ config, lib, uuid, name, resources, ... }:

with import ./lib.nix lib;
with lib;

let
  loadBalancerHealthcheckOptions =
    { config, ... }:
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
                type = with types; listOf str;
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
    };
      
  loadBalancerServiceOptions =
    { config, ... }:
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
          type = with types; nullOr (submodule loadBalancerHealthcheckOptions);
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
          type = types.listOf (resource "hetznercloud-certificate");
          description = ''
            TODO Valid only for https services.
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
    };

in

{

  options = {

    location = mkOption {
      example = "nbg1";
      type = type.enum ["nbg1" "fsn1" "hel1"];
      description = ''
        The Hetzner Cloud location where the load balancer should be created.
        Options are 'nbg1', 'fsn1', or 'hel1'.
      '';
    };

    balancerType = mkOption {
      default = "lb11";
      example = "lb11";
      type = types.str;
      description = ''
        Hetner Cloud load balancer type.
        See TODO for a list of valid load balancer types.
      '';
    };

    network = mkOption {
      default = null;
      example = "resources.hetznerCloudNetwork.myPrivateNet";
      type = types.nullOr (resource "hetznercloud-network");
      description = ''
        The Network Resource to attach this Load Balancer to.
        Targets must be a part of the same network as the Load Balancer.
      '';
    };

    targets = mkOption {
      default = [];
      example = [ "machines.httpserver1" "machines.httpserver2" ];
      type = types.listOf machine;
      description = ''
        The list of machine resources to use as targets for this Load Balancer.
      '';
    };

    services = mkOption {
      default = [];
      type = with types; listOf (submodule loadBalancerServiceOptions);
      description = ''
        Services allow you to decide how traffic will be routed from the Load
        Balancer to the targets. Each service will have a health check included.
      '';
    };

    algorithm = mkOption {
      default = "round_robin";
      example = "least_connections";
      type = types.str;
      description = "Algorithm used to direct incoming requests.";
    };

    loadBalancerId = mkOption {
      default = "";
      type = types.str;
      description = ''
        The Load Balancer ID generated from Hetzner Cloud. This is set by NixOps
      '';
    };

  } // import ./common-hetznercloud-options.nix { inherit lib; };

  config._type = "hetznercloud-load-balancer";

}
