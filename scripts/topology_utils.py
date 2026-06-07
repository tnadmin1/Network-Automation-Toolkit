"""
topology_utils.py
-----------------
Build a network topology from CDP (or LLDP) neighbor data.

Two real-world problems this module solves, both pure-function and unit-tested:

  1. Name reconciliation. CDP reports a neighbor by its configured HOSTNAME
     (e.g. "SFFX_RTR"), but your inventory uses a different name
     (e.g. "c5915-rtr"). We build a map from hostname -> inventory name so the
     diagram uses consistent, recognizable labels.

  2. Link deduplication. A link between A and B is reported twice — once by A
     (it sees B) and once by B (it sees A). We collapse those into one link.

Output is Mermaid, which GitHub renders as a live diagram inside Markdown.
"""


def _clean_hostname(name):
    """Strip any domain suffix and whitespace, uppercase for matching."""
    if not name:
        return ""
    return name.split(".")[0].strip().upper()


def _first(data, *keys, default=""):
    """Return the first present, non-empty value among the given keys.

    TextFSM field names vary across template versions (e.g. 'local_port' vs
    'local_interface'), so we check several candidates defensively.
    """
    for key in keys:
        value = data.get(key)
        if value:
            return value
    return default


def build_hostname_map(device_hostnames):
    """Map each device's reported hostname to its inventory name.

    device_hostnames : {inventory_name: reported_hostname}
    returns          : {CLEAN_HOSTNAME: inventory_name}
    """
    mapping = {}
    for inv_name, hostname in device_hostnames.items():
        key = _clean_hostname(hostname)
        if key:
            mapping[key] = inv_name
    return mapping


def canonicalize(cdp_name, hostname_map):
    """Translate a CDP-reported neighbor name to an inventory name if known."""
    key = _clean_hostname(cdp_name)
    return hostname_map.get(key, key or "unknown")


def build_links(cdp_per_device, hostname_map=None):
    """Build a deduplicated list of links from CDP neighbor data.

    cdp_per_device : {inventory_name: [neighbor_dict, ...]}
        each neighbor_dict has local_port, remote_port, destination_host
    returns        : sorted list of (node_a, port_a, node_b, port_b) tuples,
                     each undirected link represented exactly once.
    """
    hostname_map = hostname_map or {}
    seen = set()
    links = []

    for device, neighbors in cdp_per_device.items():
        for neighbor in neighbors:
            local_port = _first(neighbor, "local_port", "local_interface", default="?")
            remote_port = _first(neighbor, "remote_port", "neighbor_interface", default="?")
            remote_name = _first(neighbor, "destination_host", "neighbor_name", default="")
            remote = canonicalize(remote_name, hostname_map)

            endpoint_a = (device, local_port)
            endpoint_b = (remote, remote_port)

            # A frozenset of the two endpoints is identical no matter which
            # device reported the link, so duplicates collapse automatically.
            key = frozenset({endpoint_a, endpoint_b})
            if key in seen:
                continue
            seen.add(key)
            links.append((device, local_port, remote, remote_port))

    return sorted(links)


def _node_id(name):
    """Make a Mermaid-safe node id (letters, digits, underscores only)."""
    return "n_" + "".join(c if c.isalnum() else "_" for c in name)


def render_mermaid(links):
    """Render links as a Mermaid 'graph' diagram (renders natively on GitHub)."""
    lines = ["graph LR"]
    if not links:
        lines.append("  empty[No neighbors discovered]")
        return "\n".join(lines)

    for node_a, port_a, node_b, port_b in links:
        a_id = _node_id(node_a)
        b_id = _node_id(node_b)
        # Edge label shows the ports on each end of the link.
        lines.append(f'  {a_id}["{node_a}"] ---|"{port_a} - {port_b}"| {b_id}["{node_b}"]')

    return "\n".join(lines)
