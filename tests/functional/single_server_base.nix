{
  network.description = "NixOps HetznerCloud Test";
  resources.sshKeyPairs.ssh-key = {};

  machine = {
    deployment.targetEnv = "hetznercloud";
    deployment.hetznercloud = {
      region = "nbg1";
      serverType = "cx11";
    };
  };
}
