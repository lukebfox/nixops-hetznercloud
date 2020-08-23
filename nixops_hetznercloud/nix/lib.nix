lib:

with lib;

{

  machine = mkOptionType {
    name = "Hetzner Cloud machine";
    check = x: x ? hetznerCloud;
    merge = mergeOneOption;
  };

  resource = type: mkOptionType {
    name = "resource of type ‘${type}’";
    check = x: x._type or "" == type;
    merge = mergeOneOption;
  };

  shorten_uuid = uuid: replaceChars ["-"] [""] uuid;

}
