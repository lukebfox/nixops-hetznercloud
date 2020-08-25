{
  config_exporters = { optionalAttrs, ... }: [
    (config: {
      hetznerCloud = optionalAttrs (config.deployment.targetEnv == "hetznercloud") config.deployment.hetznerCloud;
    })
  ];
  options = [
    ./hetznercloud.nix
  ];
  resources = { evalResources, zipAttrs, resourcesByType, ... }: {
    hetznerCloudCertificates = evalResources ./certificate.nix (zipAttrs resourcesByType.hetznerCloudCertificates or []);
    hetznerCloudFloatingIPs = evalResources ./floating-ip.nix (zipAttrs resourcesByType.hetznerCloudFloatingIPs or []);
    hetznerCloudLoadBalancers = evalResources ./load-balancer.nix (zipAttrs resourcesByType.hetznerCloudLoadBalancers or []);
    hetznerCloudNetworks = evalResources ./network.nix (zipAttrs resourcesByType.hetznerCloudNetworks or []);
    hetznerCloudVolumes = evalResources ./volume.nix (zipAttrs resourcesByType.hetznerCloudVolumes or []);
  };
}
