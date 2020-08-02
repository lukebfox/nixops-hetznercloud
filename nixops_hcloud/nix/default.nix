{
  config_exporters = { optionalAttrs, ... }: [
    (config: {
      hcloud = optionalAttrs (config.deployment.targetEnv == "hetznercloud") config.deployment.hcloud;
    })
  ];
  options = [
    ./hcloud.nix
  ];
  resources = { evalResources, zipAttrs, resourcesByType, ... }: {
    hcloudCertificates = evalResources ./certificate.nix (zipAttrs resourcesByType.hcloudCertificate or []);
    hcloudFloatingIPs = evalResources ./floating-ip.nix (zipAttrs resourcesByType.hcloudFloatingIPs or []);
    hcloudLoadBalancers = evalResources ./load-balancer.nix (zipAttrs resourcesByType.hcloudLoadBalancers or []);
    hcloudNetworks = evalResources ./network.nix (zipAttrs resourcesByType.hcloudNetworks or []);
    hcloudNetworkSubnets = evalResources ./network-subnet.nix (zipAttrs resourcesByType.hcloudNetworkSubnets or []);
    hcloudNetworkRoutes = evalResources ./network-route.nix (zipAttrs resourcesByType.hcloudNetworkRoutes or []);
  };
}
