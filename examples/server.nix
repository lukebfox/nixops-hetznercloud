{ apiToken ? "qFYCZtzCGcWVdIaje8fQWSOg4RmTICCwcomcOJJtUJcFm3DjDJ9Nl0kkX2ZyrFnx"
}:
{
  network.description = "POC deployment";

  machine1 = {
     deployment.targetEnv = "hetznercloud";
     deployment.hetznerCloud = {
       inherit apiToken;
       location = "nbg1";
       serverName = "machine1name";
       serverType = "cx11";
     };
   };
  
}
