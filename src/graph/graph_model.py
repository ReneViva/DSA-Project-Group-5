# ======================= GRAPH MODEL =======================
# This file builds a graph structure representing relationships in the dataset.
# Steps:
# 1. Create nodes (e.g., developers, publishers)
# 2. Add edges for collaborations or relationships
# 3. Use NetworkX Graph for implementation
# 4. Provide methods to build and access the graph
# Purpose: Prepare the graph layer for running algorithms like BFS/DFS later.
# ======================= GRAPH MODEL =======================
# Adjacency-map graph implementation (no external libraries).
# Supports undirected graphs by default.

from collections import defaultdict


class Graph:
    """Adjacency-map based graph (undirected by default)."""

    class Vertex:
        __slots__ = ("_element", "_kind", "_id")

        def __init__(self, element, kind=None, id_=None):
            # element: usually a dict row from dataset
            self._element = element
            self._kind = kind          # e.g. "developer" or "publisher"
            self._id = id_             # integer id from CSV

        def element(self):
            return self._element

        def kind(self):
            return self._kind

        def id(self):
            return self._id

        def __hash__(self):
            # Allows Vertex to be used as dict key / in sets
            return id(self)

        def __repr__(self):
            base = self._element
            name = None
            if isinstance(base, dict):
                name = base.get("name")
            if name:
                return f"Vertex({self._kind}:{name})"
            return f"Vertex(kind={self._kind}, id={self._id})"

    class Edge:
        __slots__ = ("_origin", "_destination", "_element")

        def __init__(self, u, v, element=None):
            self._origin = u
            self._destination = v
            self._element = element    # e.g. {"games": set(), "weight": int}

        def endpoints(self):
            return (self._origin, self._destination)

        def element(self):
            return self._element

        def __repr__(self):
            return f"Edge({self._origin} <-> {self._destination}, data={self._element})"

    # -----------------------------------------------------
    # CORE GRAPH STRUCTURE
    # -----------------------------------------------------

    def __init__(self, directed=False):
        """Create an empty graph (undirected by default)."""
        self._outgoing = {}
        # For undirected graphs, incoming == outgoing
        self._incoming = {} if directed else self._outgoing
        self._directed = directed

    def is_directed(self):
        return self._directed

    # ---------- vertex helpers ----------

    def vertex_count(self):
        return len(self._outgoing)

    def vertices(self):
        """Iterate over vertices."""
        return self._outgoing.keys()

    # ---------- edge helpers ----------

    def edge_count(self):
        total = sum(len(adj) for adj in self._outgoing.values())
        return total if self._directed else total // 2

    def edges(self):
        """Iterate over edges (unique in undirected case)."""
        result = set()
        for adj in self._outgoing.values():
            result.update(adj.values())
        return result

    def get_edge(self, u, v):
        """Return edge from u to v, or None."""
        return self._outgoing.get(u, {}).get(v)

    def degree(self, v, outgoing=True):
        adj = self._outgoing if outgoing else self._incoming
        return len(adj.get(v, {}))

    def incident_edges(self, v, outgoing=True):
        """Iterate over edges incident to v."""
        adj = self._outgoing if outgoing else self._incoming
        for e in adj.get(v, {}).values():
            yield e

    # ---------- mutators ----------

    def insert_vertex(self, element=None, kind=None, id_=None):
        v = Graph.Vertex(element, kind=kind, id_=id_)
        self._outgoing[v] = {}
        if self._directed:
            self._incoming[v] = {}
        return v

    def insert_edge(self, u, v, element=None):
        """Insert an edge between u and v, if it does not already exist."""
        existing = self.get_edge(u, v)
        if existing is not None:
            return existing

        e = Graph.Edge(u, v, element)
        self._outgoing[u][v] = e
        self._incoming[v][u] = e
        return e

    # ---------- static helper ----------

    @staticmethod
    def opposite(v, e):
        """Return the vertex on the other end of edge e from v."""
        u, w = e.endpoints()
        if v is u:
            return w
        if v is w:
            return u
        raise ValueError("v is not incident to edge e")


# =========================================================
# Developer–Publisher graph builder
# =========================================================

def build_dev_pub_graph(cleaned_data):
    """
    Build an undirected bipartite graph between developers and publishers.

    cleaned_data: dict[str, list[dict]] from DataLoader.load_all()

    Returns:
        graph: Graph
        dev_vertices: dict[developer_id -> Vertex]
        pub_vertices: dict[publisher_id -> Vertex]
    """
    g = Graph(directed=False)

    developers = cleaned_data.get("developers", [])
    publishers = cleaned_data.get("publishers", [])
    app_devs = cleaned_data.get("application_developers", [])
    app_pubs = cleaned_data.get("application_publishers", [])

    # --- create vertices ---

    dev_vertices = {}
    for row in developers:
        dev_id = row.get("id")
        v = g.insert_vertex(element=row, kind="developer", id_=dev_id)
        dev_vertices[dev_id] = v

    pub_vertices = {}
    for row in publishers:
        pub_id = row.get("id")
        v = g.insert_vertex(element=row, kind="publisher", id_=pub_id)
        pub_vertices[pub_id] = v

    # --- group app → devs / pubs ---

    from collections import defaultdict

    app_to_devs = defaultdict(list)
    for row in app_devs:
        appid = row.get("appid")
        did = row.get("developer_id")
        if appid is None or did is None:
            continue
        app_to_devs[appid].append(did)

    app_to_pubs = defaultdict(list)
    for row in app_pubs:
        appid = row.get("appid")
        pid = row.get("publisher_id")
        if appid is None or pid is None:
            continue
        app_to_pubs[appid].append(pid)

    # --- insert edges for collaborations ---

    edge_lookup = {}   # (dev_id, pub_id) -> Edge

    for appid, dev_ids in app_to_devs.items():
        pub_ids = app_to_pubs.get(appid, [])
        if not pub_ids:
            continue

        for did in dev_ids:
            if did not in dev_vertices:
                continue
            for pid in pub_ids:
                if pid not in pub_vertices:
                    continue

                key = (did, pid) if did <= pid else (pid, did)
                if key not in edge_lookup:
                    u = dev_vertices[did]
                    v = pub_vertices[pid]
                    edge_data = {"games": {appid}, "weight": 1}
                    e = g.insert_edge(u, v, element=edge_data)
                    edge_lookup[key] = e
                else:
                    e = edge_lookup[key]
                    data = e.element()
                    data["games"].add(appid)
                    data["weight"] += 1

    return g, dev_vertices, pub_vertices
