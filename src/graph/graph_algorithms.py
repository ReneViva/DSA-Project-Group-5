# ======================= GRAPH ALGORITHMS =======================
# Basic algorithms on top of Graph:
#   - BFS traversal
#   - DFS traversal
#   - Shortest path (unweighted)
#   - Connected components

from collections import deque
from .graph_model import Graph


def bfs_traversal(graph: Graph, start_vertex):
    """
    Breadth-first traversal from start_vertex.

    Returns:
        order: list of vertices in discovery order.
    """
    visited = set()
    order = []
    queue = deque()

    visited.add(start_vertex)
    queue.append(start_vertex)

    while queue:
        u = queue.popleft()
        order.append(u)
        for edge in graph.incident_edges(u):
            v = graph.opposite(u, edge)
            if v not in visited:
                visited.add(v)
                queue.append(v)

    return order


def dfs_traversal(graph: Graph, start_vertex):
    """
    Depth-first traversal from start_vertex (recursive).
    """
    visited = set()
    order = []

    def _dfs(u):
        visited.add(u)
        order.append(u)
        for edge in graph.incident_edges(u):
            v = graph.opposite(u, edge)
            if v not in visited:
                _dfs(v)

    _dfs(start_vertex)
    return order


def shortest_path(graph: Graph, start_vertex, target_vertex):
    """
    Shortest path in an unweighted graph using BFS.

    Returns:
        list[Vertex] from start to target (inclusive),
        or None if no path.
    """
    if start_vertex is target_vertex:
        return [start_vertex]

    parent = {start_vertex: None}
    queue = deque([start_vertex])

    while queue:
        u = queue.popleft()
        for edge in graph.incident_edges(u):
            v = graph.opposite(u, edge)
            if v not in parent:
                parent[v] = u
                if v is target_vertex:
                    # reconstruct path
                    path = [v]
                    while u is not None:
                        path.append(u)
                        u = parent[u]
                    path.reverse()
                    return path
                queue.append(v)

    return None


def connected_components(graph: Graph):
    """
    Find all connected components of an (undirected) graph.

    Returns:
        list of components, each component is a list[Vertex].
    """
    visited = set()
    components = []

    for v in graph.vertices():
        if v in visited:
            continue

        comp = []
        stack = [v]
        visited.add(v)

        while stack:
            u = stack.pop()
            comp.append(u)
            for edge in graph.incident_edges(u):
                w = graph.opposite(u, edge)
                if w not in visited:
                    visited.add(w)
                    stack.append(w)

        components.append(comp)

    return components
