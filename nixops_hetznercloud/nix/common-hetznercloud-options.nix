{ lib }:

with lib;

{
    
  labels = mkOption {
    default = { };
    example = { environment = "foobar"; "example.com/my" = "label"; };
      type = types.attrsOf types.str;
      description = ''
        A set of key/value label pairs to assign to the instance.
        Valid label keys have two segments: an optional prefix and name, separated by a slash (/). The name segment is required and must be a string of 63 characters or less, beginning and ending with an alphanumeric character ([a-z0-9A-Z]) with dashes (-), underscores (_), dots (.), and alphanumerics between. The prefix is optional. If specified, the prefix must be a DNS subdomain: a series of DNS labels separated by dots (.), not longer than 253 characters in total, followed by a slash (/).
        Valid label values must be a string of 63 characters or less and must be empty or begin and end with an alphanumeric character ([a-z0-9A-Z]) with dashes (-), underscores (_), dots (.), and alphanumerics between.      '';
  };
  
}
