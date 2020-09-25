# NixOps Hetzner Cloud Plugin

NixOps is a tool for deploying NixOS machines in a network or cloud. This repo contains the NixOps Hetzner Cloud Plugin.

## Disclaimer
This repo is pre-alpha! That means it's a work in progress, and many things may be unfinished or non-functional, therefore definitely NOT meant for production. If like me you're a nix-hobbyist and appreciate the super cheap rates Hetzner provides but have been aching for a way to automate deployments then you're in luck! While you can already provision resources with the [terraform provider](https://github.com/hetznercloud/terraform-provider-hcloud), this will do nothing for automating your NixOS deployment. The alternative, NixOps, is a more integrated solution which has just been waiting for someone to come and write a plugin. My goal is to automate the entire process of provisioning and deploying your NixOS box with one tool. At the moment I'm working on the other resources with an intent to complete all of them.

## Usage
Before you can use NixOps to manage Hetzner Cloud Resources you must have a Hetzner Cloud account. You'll need to manually create any project which you want to be managed with NixOps, and generate a project-specific API token which NixOps will use for authentication (security>api tokens>generate_api_token). The example code covers the basic use cases for Hetzner Cloud resource management with NixOps. The NixOps deployment options specific to Hetzer Cloud are declared in the nix files and documented here: TODO.

## Developing

To start developing on the NixOps Hetzner Cloud plugin, you can run:

```bash
  $ nix develop
  $ poetry install
  $ poetry shell
```

## Testing

## Building from source

The command to build NixOps depends on your platform.

See the main NixOps repo instructions for how to build NixOps
with this Hetzner Cloud plugin.

## TODO
-[]Tests
-[]Integrate server backend with network resources
-[]Validate options
-[]Documentation
-[]Autocreate volumes for server backend if specified
-[]Load Balancer Resource

---
Credit to the maintainers of the nixops-aws plugin which I have copied embarassing amounts of code from and elitak for the original nixos-infect script.
