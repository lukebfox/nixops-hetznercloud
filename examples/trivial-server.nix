{ apiToken ? "changeme"
, location ? "nbg1" }:
{
  network.description = "Hetzner Cloud trivial server deployment";

  machine1 =
    { config, ... }:
    {
      deployment.targetEnv = "hetznercloud";
      deployment.hetznerCloud = {
        inherit apiToken location;
        serverType = "cx11";
      };
    };

}
