{
  network.description = "NixOps HetznerCloud Test";

  machine = {
    deployment.targetEnv = "hetznercloud";
    deployment.hetznerCloud = {
      location = "nbg1";
      serverType = "cx11";
    };
  };
}
