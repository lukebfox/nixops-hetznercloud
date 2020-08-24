{ apiToken ? "qFYCZtzCGcWVdIaje8fQWSOg4RmTICCwcomcOJJtUJcFm3DjDJ9Nl0kkX2ZyrFnx"
}:
{
  network.description = "POC deployment";

  machine1 =
    { config, resources, ... }:
    {
      deployment.targetEnv = "hetznercloud";
      deployment.hetznerCloud = {
        inherit apiToken;
        location = "nbg1";
        #serverName = "trivial-server";
        serverType = "cx11";
        #sshKeys = with resources.hetznerCloudSSHKeys; [ yubikey ];
      };
    };

  #resources.hetznerCloudSSHKeys.yubikey = {
  #  inherit apiToken;
#    publicKey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCmmGKguILui9U7qPvPivhfIVH0OgGZL1aSgNiQiPSbp5x/qmgbOvsP/DTfjzLQTGsNE9ipFPNObUjM/EQwp/UvJQ8/ZpmemW56KntUr2cXURuGGCmJV1ihg0zI12sl0JzLvt2oGu83feGhg268lUDY5ind5iHheUqGQsemlIJH7z1CTGqfWG1yg8QbbrIwbsvhH0nwX5U8AAyBFAOn6/rmyjJzPyfSotuOdzna+aFqZ+6yYkboADnMoyr8n1ZMqaYy0CZhINOl0BHQX1GtHrItQIz3al7jA6NgC2VH1C8hhIe4TSMthwo0VL7WnyRg3cSkIfYeI9b06Ll0F4BWX8qlJ1IzkuMElTA+M3+EffbWBFYS0aThNIMYs+y6JC0yA0xVs4dDsWq5YV1WO8oNfWszyqfmM4DPYRw8Y/uzpOUD67b2UZYrupSiZerYFQidAPGjGy0AqXLK4Hso2oCOK4HOX2yqXIqQTkzUC4T8PSdCZbughcvCzTAwwIU/NlBdnKZjbCuGwvZtx0KushE3PzCds0ocK093hezvQR8YOzA3lXCfiPsQDIrOCj36BhzPUekJa/+Qn1W3PujOlTriwE6LJAFzRyqMaUGzpBC8ELrml3GYAsrJeVW82Y5SOq11OgMK550wjDhjehRp5KEENR5MHZJXbJe667+qOjRPZ6Kvgw== openpgp:0xA747ED85";
    #publicKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDgFoF1gx50bc273ZtaxisKq/GO8Y+awYhZenlwB6YzF robot@lukebentleyfox.net";
  #};
  
}
