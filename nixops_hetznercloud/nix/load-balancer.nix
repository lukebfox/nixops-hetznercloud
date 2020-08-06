# Configuration specific to Hetzner Cloud Load Balancer Resource.
{ config, lib, uuid, name, resources, ... }:

with import ./lib.nix lib;
with lib;

{

  imports = [ ./common-hetzner-cloud-auth-options.nix ];

  options = {

    name = mkOption {
      default = "nixops-${uuid}-${name}";
      example = "my-load-balancer";
      type = types.str;
      description = "Hetzner Cloud Load Balancer <literal>Name</literal>.";
    };

    location = mkOption {
      example = "nbg1";
      type = type.enum ["nbg1", "fsn1", "hel1" ];
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
      type = types.nullOr (resource "hetzner-cloud-network");
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
      type = types.listOf (resource "hetzner-cloud-load-balancer-service");
      example = [ "resources.hetznerCloudLoadBalancerServices.myHttpRedirect" ];
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

    labels = (import ./common-hetzner-cloud-options.nix { inherit lib; }).labels;
    
  };
    
  config._type = "hetzner-cloud-load-balancer";
  
}
