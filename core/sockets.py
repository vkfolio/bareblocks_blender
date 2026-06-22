# BareBlocks - 4.2/5.x-safe Geometry Nodes input access.
#
# Never address GN modifier inputs by the fragile "Socket_3" identifier directly;
# resolve the stable identifier from the human name every time (cheap, refactor-proof).

import bpy

from .ids import MOD_NAME


def socket_id(node_group, name, in_out="INPUT"):
    """Return the interface socket identifier for a named input/output socket."""
    for item in node_group.interface.items_tree:
        if item.item_type == "SOCKET" and item.in_out == in_out and item.name == name:
            return item.identifier
    raise KeyError(f"Socket {name!r} not found in node group {node_group.name!r}")


def get_modifier(obj):
    """Return the BareBlocks GN modifier on obj, or None."""
    if obj is None:
        return None
    return obj.modifiers.get(MOD_NAME)


def mod_value(obj, name):
    mod = get_modifier(obj)
    return mod[socket_id(mod.node_group, name)]


def set_mod(obj, name, value, tag=True):
    mod = get_modifier(obj)
    mod[socket_id(mod.node_group, name)] = value
    if tag:
        obj.update_tag()


def is_bareblocks(obj):
    return obj is not None and obj.get("bareblocks_type") is not None and get_modifier(obj) is not None
