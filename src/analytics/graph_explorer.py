# src/ui/graph_explorer.py

"""Streamlit component for exploring the developer–publisher graph.

This uses ONLY our own Graph implementation (src/graph/graph_model.py)
plus the algorithms in src/graph/graph_algorithms.py and Streamlit for UI.
No external graph/plotting libraries are used.
"""

from __future__ import annotations

from typing import Dict, Tuple

import streamlit as st

from src.graph.graph_model import build_dev_pub_graph, Graph
from src.graph.graph_algorithms import (
    bfs_traversal,
    dfs_traversal,
    connected_components,
)


# -------------------------------------------------------------
# Cached graph builder
# -------------------------------------------------------------

@st.cache_resource
def _build_small_dev_pub_graph(
    cleaned_data: Dict[str, list],
    max_devs: int = 150,
    max_pubs: int = 150,
    max_links: int = 5000,
) -> Tuple[Graph, Dict[str, Graph.Vertex], Dict[str, Graph.Vertex]]:
    """Build a *small* bipartite developer–publisher graph.

    We limit how many rows we use so that the UI stays fast. You can
    safely increase these numbers later if performance is still OK.
    """

    developers = cleaned_data.get("developers", [])[:max_devs]
    publishers = cleaned_data.get("publishers", [])[:max_pubs]
    app_devs = cleaned_data.get("application_developers", [])[:max_links]
    app_pubs = cleaned_data.get("application_publishers", [])[:max_links]

    slim = {
        "developers": developers,
        "publishers": publishers,
        "application_developers": app_devs,
        "application_publishers": app_pubs,
    }

    graph, dev_vertices, pub_vertices = build_dev_pub_graph(slim)

    # Build name -> vertex maps for easy selection in the UI
    dev_by_name: Dict[str, Graph.Vertex] = {}
    for v in dev_vertices.values():
        row = v.element() or {}
        name = row.get("name")
        if name:
            dev_by_name[name] = v

    pub_by_name: Dict[str, Graph.Vertex] = {}
    for v in pub_vertices.values():
        row = v.element() or {}
        name = row.get("name")
        if name:
            pub_by_name[name] = v

    return graph, dev_by_name, pub_by_name


# -------------------------------------------------------------
# Helper for pretty vertex labels
# -------------------------------------------------------------

def _vertex_label(v: Graph.Vertex) -> str:
    row = v.element() or {}
    name = row.get("name")
    if name:
        return f"{v.kind().title()} – {name}"
    if v.id() is not None:
        return f"{v.kind().title()} #{v.id()}"
    return f"Vertex(kind={v.kind()})"


# -------------------------------------------------------------
# Main render function
# -------------------------------------------------------------


def render_graph_explorer(cleaned_data: Dict[str, list]) -> None:
    """Render the 'Graph explorer' section inside Streamlit app.

    Call this once from app.py, after `cleaned_data` has been loaded.
    """

    st.divider()
    st.header("7. Developer–publisher graph explorer (no external libraries)")

    st.write(
        """
        This component uses our own adjacency-map `Graph` implementation to build a
        **bipartite graph** between developers and publishers:

        * Vertices = developers + publishers
        * Edge between dev and pub = they have at least one game together
        * Edge weight = how many games they share

        The visualization is text-based: we show neighborhoods, traversal orders,
        and degree tables instead of using plotting libraries.
        """
    )

    with st.spinner("Building a small developer–publisher graph from the dataset..."):
        graph, dev_by_name, pub_by_name = _build_small_dev_pub_graph(cleaned_data)

    if graph.vertex_count() == 0:
        st.warning("Graph is empty – check that graph-related tables are loaded.")
        return

    tab_dev, tab_pub, tab_summary = st.tabs([
        "Developer view",
        "Publisher view",
        "Graph summary",
    ])

    # ------------------------------------------------------------------
    # Developer view
    # ------------------------------------------------------------------
    with tab_dev:
        st.subheader("Developer neighborhood & traversals")

        dev_names = sorted(dev_by_name.keys())
        if not dev_names:
            st.warning("No developers found in the current graph slice.")
        else:
            selected_dev_name = st.selectbox(
                "Choose a developer:",
                dev_names,
                key="dev_select",
            )

            selected_dev = dev_by_name[selected_dev_name]
            st.caption(_vertex_label(selected_dev))

            cols = st.columns(3)
            with cols[0]:
                show_neighbors = st.button("Show neighbors", key="dev_neighbors")
            with cols[1]:
                show_bfs = st.button("BFS traversal", key="dev_bfs")
            with cols[2]:
                show_dfs = st.button("DFS traversal", key="dev_dfs")

            if show_neighbors:
                _render_neighbors_table(graph, selected_dev, role="publisher")

            if show_bfs:
                _render_traversal(graph, selected_dev, mode="bfs")

            if show_dfs:
                _render_traversal(graph, selected_dev, mode="dfs")

    # ------------------------------------------------------------------
    # Publisher view
    # ------------------------------------------------------------------
    with tab_pub:
        st.subheader("Publisher neighborhood & traversals")

        pub_names = sorted(pub_by_name.keys())
        if not pub_names:
            st.warning("No publishers found in the current graph slice.")
        else:
            selected_pub_name = st.selectbox(
                "Choose a publisher:",
                pub_names,
                key="pub_select",
            )

            selected_pub = pub_by_name[selected_pub_name]
            st.caption(_vertex_label(selected_pub))

            cols = st.columns(3)
            with cols[0]:
                show_neighbors = st.button("Show neighbors", key="pub_neighbors")
            with cols[1]:
                show_bfs = st.button("BFS traversal", key="pub_bfs")
            with cols[2]:
                show_dfs = st.button("DFS traversal", key="pub_dfs")

            if show_neighbors:
                _render_neighbors_table(graph, selected_pub, role="developer")

            if show_bfs:
                _render_traversal(graph, selected_pub, mode="bfs")

            if show_dfs:
                _render_traversal(graph, selected_pub, mode="dfs")

    # ------------------------------------------------------------------
    # Graph summary
    # ------------------------------------------------------------------
    with tab_summary:
        st.subheader("Global graph statistics")

        v_count = graph.vertex_count()
        e_count = graph.edge_count()

        st.write(f"**Vertices:** {v_count}  |  **Edges:** {e_count}")

        # Connected components
        comps = connected_components(graph)
        comp_sizes = sorted((len(c) for c in comps), reverse=True)

        st.write(f"**Connected components:** {len(comp_sizes)}")

        if comp_sizes:
            max_size = max(comp_sizes)
            st.write(f"Largest component size: **{max_size}** vertices")

            st.write("Component size distribution (top 10):")
            top_sizes = comp_sizes[:10]
            st.table({
                "Component #": list(range(1, len(top_sizes) + 1)),
                "Size": top_sizes,
            })

        # Top-degree vertices
        st.markdown("---")
        st.subheader("Most connected developers/publishers in this slice")

        rows = []
        for v in graph.vertices():
            rows.append({
                "label": _vertex_label(v),
                "degree": graph.degree(v),
            })

        rows.sort(key=lambda r: r["degree"], reverse=True)
        top_rows = rows[:15]

        st.table({
            "Vertex": [r["label"] for r in top_rows],
            "Degree": [r["degree"] for r in top_rows],
        })


# -------------------------------------------------------------
# Internal helpers used by the tabs
# -------------------------------------------------------------


def _render_neighbors_table(graph: Graph, v: Graph.Vertex, role: str) -> None:
    """Show a small table of neighbors for vertex v.

    `role` is just a string we display ("developer" / "publisher").
    """

    neighbors = []
    for edge in graph.incident_edges(v):
        u, w = edge.endpoints()
        other = w if v is u else u

        row = other.element() or {}
        name = row.get("name") or f"{other.kind()} #{other.id()}"

        data = edge.element() or {}
        weight = data.get("weight")
        games = data.get("games")
        n_games = len(games) if isinstance(games, set) else weight

        neighbors.append({
            "Neighbor": name,
            "Role": other.kind(),
            "Games together": n_games,
        })

    if not neighbors:
        st.info("This vertex has no neighbors in the current graph slice.")
        return

    st.write(f"Found **{len(neighbors)}** neighbors for this {role}.")

    neighbors.sort(key=lambda r: r["Games together"], reverse=True)
    top = neighbors[:25]

    st.table({
        "Neighbor": [r["Neighbor"] for r in top],
        "Role": [r["Role"] for r in top],
        "Games together": [r["Games together"] for r in top],
    })


def _render_traversal(graph: Graph, start: Graph.Vertex, mode: str = "bfs") -> None:
    """Show BFS/DFS traversal order starting from `start`.

    `mode` is either "bfs" or "dfs".
    """

    if mode == "bfs":
        order = bfs_traversal(graph, start)
        title = "BFS traversal order"
    else:
        order = dfs_traversal(graph, start)
        title = "DFS traversal order"

    if not order:
        st.info("Traversal returned no vertices.")
        return

    labels = [_vertex_label(v) for v in order[:40]]  # limit for readability
    st.write(f"{title} (first {len(labels)} vertices shown):")
    st.code(" -> ".join(labels))
