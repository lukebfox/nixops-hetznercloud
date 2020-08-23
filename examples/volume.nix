{ apiToken ? "qFYCZtzCGcWVdIaje8fQWSOg4RmTICCwcomcOJJtUJcFm3DjDJ9Nl0kkX2ZyrFnx"
}:
{
  network.description = "POC deployment";

  resources.hetznerCloudVolumes.my-example-volume = {
    inherit apiToken;
    location = "nbg1";
    name = "volume-1";
    size = 10;
    format = "ext4";
    labels = { hi = "hi"; } ;
  };

}
