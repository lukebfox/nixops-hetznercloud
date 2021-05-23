{ apiToken ? "changeme"
, location ? "nbg1" }:
let
  backend =
    { pkgs, ... }:
    {
      deployment.targetEnv = "hetznercloud";
      deployment.hetznerCloud = {
        inherit apiToken location;
        serverType = "cx11";
      };
      services.nginx.enable = true;
      networking.firewall.allowedTCPPorts = [ 80 443 ];
    };
in
{
  network.description = "Hetzner Cloud load balancer example deployment";

  machine1 = backend;
  machine2 = backend;

  resources.hetznerCloudLoadBalancers.lb1 =
    { nodes, ... }:
    {
      inherit apiToken location;
      loadBalancerType = "lb11";
      targets = [ nodes.machine1 nodes.machine2 ];
      services = [];
      algorithm = "round_robin";
    };
}
