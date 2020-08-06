{
  config_exporters = { optionalAttrs, ... }: [
    (config: {
      hetznerCloud = optionalAttrs (config.deployment.targetEnv == "hetznerCloud") config.deployment.hetznerCloud;
    })
  ];
  options = [
    ./hetznercloud.nix
  ];
  resources = { evalResources, zipAttrs, resourcesByType, ... }: {
    hetznerCloudCertificates = evalResources ./certificate.nix (zipAttrs resourcesByType.hetznerCloudCertificates or []);
#    hetznerCloudFloatingIPs = evalResources ./floating-ip.nix (zipAttrs resourcesByType.hetznerCloudFloatingIPs or []);
#    hetznerCloudLoadBalancers = evalResources ./load-balancer.nix (zipAttrs resourcesByType.hetznerCloudLoadBalancers or []);
#    hetznerCloudLoadBalancerServices = evalResources ./load-balancer-service.nix (zipAttrs resourcesByType.hetznerCloudLoadBalancerServices or []);
#    hetznerCloudLoadBalancerHealthchecks = evalResources ./load-balancer-healthcheck.nix (zipAttrs resourcesByType.hetznerCloudLoadBalancerHealthchecks or []); 
#    hetznerCloudNetworks = evalResources ./network.nix (zipAttrs resourcesByType.hetznerCloudNetworks or []);
#    hetznerCloudNetworkSubnets = evalResources ./network-subnet.nix (zipAttrs resourcesByType.hetznerCloudNetworkSubnets or []);
#    hetznerCloudNetworkRoutes = evalResources ./network-route.nix (zipAttrs resourcesByType.hetznerCloudNetworkRoutes or []);   
#    hetznerCloudVolumes = evalResources ./volume.nix (zipAttrs resourcesByType.hetznerCloudVolumes or []);
  };
}
