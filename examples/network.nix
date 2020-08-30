{ apiToken ? "qFYCZtzCGcWVdIaje8fQWSOg4RmTICCwcomcOJJtUJcFm3DjDJ9Nl0kkX2ZyrFnx"
}:
{
  network.description = "POC deployment";

  resources.hetznerCloudNetworks.my-example-network = {
    inherit apiToken;
    name = "privNet";
    ipRange = "10.0.0.0/16";
    subnets = [
      "10.0.1.0/24"
      "10.0.2.0/24"
      "10.0.3.0/24"
    ];
    routes = [
      { destination = "10.0.4.0/24";
        gateway = "10.0.1.1";
      }
      { destination = "10.0.5.0/24";
        gateway = "10.0.1.2";
      }

    ];
  };

}
