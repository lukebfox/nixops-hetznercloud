{ apiToken ? "qFYCZtzCGcWVdIaje8fQWSOg4RmTICCwcomcOJJtUJcFm3DjDJ9Nl0kkX2ZyrFnx"
}:
{
  network.description = "POC deployment";

  resources.hetznerCloudFloatingIPs.my-example-floating-ip = {
    inherit apiToken;
    location = "nbg1";
    type = "ipv4";
  };

}
