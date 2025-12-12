# src/ui/graph_explorer.py

"""Streamlit component for exploring the developer–publisher graph.

This uses ONLY our own Graph implementation (src/graph/graph_model.py)
plus the algorithms in src/graph/graph_algorithms.py and Streamlit for UI.
No external graph/plotting libraries are used.
"""

from __future__ import annotations

from typing import Dict, Tuple, List, Set, Optional
from collections import defaultdict

import streamlit as st

from src.graph.graph_model import (
    build_dev_pub_graph,
    Graph,
    developer_with_most_publisher_collaborations,
    get_publisher_collaborations_for_developer,
)

from src.graph.graph_algorithms import (
    bfs_traversal,
    dfs_traversal,
    connected_components,
)


# -------------------------------------------------------------
# FULL DATASET (FAST) helpers: no graph build required
# -------------------------------------------------------------

def _build_id_name_maps(cleaned_data: Dict[str, list]) -> Tuple[Dict[int, str], Dict[int, str]]:
    dev_name_by_id: Dict[int, str] = {}
    for row in cleaned_data.get("developers", []):
        did = row.get("id")
        if did is not None:
            dev_name_by_id[int(did)] = row.get("name") or f"Developer #{did}"

    pub_name_by_id: Dict[int, str] = {}
    for row in cleaned_data.get("publishers", []):
        pid = row.get("id")
        if pid is not None:
            pub_name_by_id[int(pid)] = row.get("name") or f"Publisher #{pid}"

    return dev_name_by_id, pub_name_by_id


def _compute_top_developer_full_dataset(cleaned_data: Dict[str, list]) -> Tuple[Optional[int], int]:
    """
    Fast top developer: totals[dev_id] = sum over apps of (#publishers on that app),
    where dev_id is listed on that app.

    We de-duplicate devs and pubs per appid to avoid accidental double counts.
    """
    app_to_devs: Dict[int, Set[int]] = defaultdict(set)
    for row in cleaned_data.get("application_developers", []):
        appid = row.get("appid")
        did = row.get("developer_id")
        if appid is None or did is None:
            continue
        app_to_devs[int(appid)].add(int(did))

    app_to_pubs: Dict[int, Set[int]] = defaultdict(set)
    for row in cleaned_data.get("application_publishers", []):
        appid = row.get("appid")
        pid = row.get("publisher_id")
        if appid is None or pid is None:
            continue
        app_to_pubs[int(appid)].add(int(pid))

    totals: Dict[int, int] = defaultdict(int)

    for appid, devs in app_to_devs.items():
        pubs = app_to_pubs.get(appid)
        if not pubs:
            continue
        pub_count = len(pubs)
        for did in devs:
            totals[did] += pub_count

    if not totals:
        return None, 0

    top_did = max(totals.keys(), key=lambda d: totals[d])
    return top_did, int(totals[top_did])


def _compute_publisher_collabs_for_developer_full_dataset(
    cleaned_data: Dict[str, list],
    developer_id: int,
    sample_k_appids: int = 10,
) -> List[Tuple[int, int, List[int]]]:
    """
    Returns list of (publisher_id, weight, sample_appids) for ONE developer_id.
    weight counts unique apps shared with that publisher.

    Efficient 2-pass approach:
    - build app_to_pubs once
    - scan app_devs and when dev is present, update publisher stats
    """
    developer_id = int(developer_id)

    app_to_pubs: Dict[int, Set[int]] = defaultdict(set)
    for row in cleaned_data.get("application_publishers", []):
        appid = row.get("appid")
        pid = row.get("publisher_id")
        if appid is None or pid is None:
            continue
        app_to_pubs[int(appid)].add(int(pid))

    pub_weight: Dict[int, int] = defaultdict(int)
    pub_samples: Dict[int, List[int]] = defaultdict(list)

    # We must de-duplicate dev listings per appid
    # so we build app_to_devs only for apps where this dev appears.
    apps_with_dev: Set[int] = set()
    for row in cleaned_data.get("application_developers", []):
        appid = row.get("appid")
        did = row.get("developer_id")
        if appid is None or did is None:
            continue
        if int(did) == developer_id:
            apps_with_dev.add(int(appid))

    for appid in apps_with_dev:
        pubs = app_to_pubs.get(appid)
        if not pubs:
            continue
        for pid in pubs:
            pub_weight[pid] += 1
            if len(pub_samples[pid]) < sample_k_appids:
                pub_samples[pid].append(appid)

    results = [(pid, int(pub_weight[pid]), pub_samples.get(pid, [])) for pid in pub_weight.keys()]
    results.sort(key=lambda t: t[1], reverse=True)
    return results


# -------------------------------------------------------------
# Cached graph builder (SLICE MODE)
# -------------------------------------------------------------

@st.cache_resource
def _build_small_dev_pub_graph(
    cleaned_data: Dict[str, list],
    max_devs: int = 150,
    max_pubs: int = 150,
    max_links: int = 5000,
) -> Tuple[
    Graph,
    Dict[int, Graph.Vertex],
    Dict[int, Graph.Vertex],
    Dict[str, Graph.Vertex],
    Dict[str, Graph.Vertex],
]:
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

    return graph, dev_vertices, pub_vertices, dev_by_name, pub_by_name


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


def _render_collaborations_table(
    collabs: List[Tuple[Graph.Vertex, int, Set[int]]],
    title: str = "Collaborations",
) -> None:
    if not collabs:
        st.info("No collaborations found in the current graph slice.")
        return

    rows = []
    for pub_v, weight, games in collabs:
        pub_row = pub_v.element() or {}
        pub_name = pub_row.get("name") or f"Publisher #{pub_v.id()}"
        game_count = len(games) if isinstance(games, set) else int(weight)

        sample = ""
        if isinstance(games, set) and games:
            sample_ids = sorted(list(games))[:10]
            sample = ", ".join(map(str, sample_ids))

        rows.append({
            "Publisher": pub_name,
            "Weight (games together)": int(weight),
            "Unique games": int(game_count),
            "Sample appids": sample,
        })

    rows.sort(key=lambda r: r["Weight (games together)"], reverse=True)

    st.write(f"**{title}:** {len(rows)} publisher connections")
    st.table({
        "Publisher": [r["Publisher"] for r in rows[:25]],
        "Weight (games together)": [r["Weight (games together)"] for r in rows[:25]],
        "Unique games": [r["Unique games"] for r in rows[:25]],
        "Sample appids": [r["Sample appids"] for r in rows[:25]],
    })


def _render_full_dataset_table(
    pub_stats: List[Tuple[int, int, List[int]]],
    pub_name_by_id: Dict[int, str],
    title: str,
) -> None:
    if not pub_stats:
        st.info("No publisher collaborations found.")
        return

    rows = []
    for pid, weight, sample_appids in pub_stats[:25]:
        rows.append({
            "Publisher": pub_name_by_id.get(pid, f"Publisher #{pid}"),
            "Weight (games together)": int(weight),
            "Sample appids": ", ".join(map(str, sample_appids[:10])) if sample_appids else "",
        })

    st.write(f"**{title}:** {len(pub_stats)} publisher connections")
    st.table({
        "Publisher": [r["Publisher"] for r in rows],
        "Weight (games together)": [r["Weight (games together)"] for r in rows],
        "Sample appids": [r["Sample appids"] for r in rows],
    })


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

    dev_name_by_id, pub_name_by_id = _build_id_name_maps(cleaned_data)

    with st.spinner("Building a small developer–publisher graph from the dataset (slice mode)..."):
        graph, dev_vertices, pub_vertices, dev_by_name, pub_by_name = _build_small_dev_pub_graph(cleaned_data)

    if graph.vertex_count() == 0:
        st.warning("Graph is empty – check that graph-related tables are loaded.")
        return

    tab_dev, tab_pub, tab_top, tab_summary = st.tabs([
        "Developer view",
        "Publisher view",
        "Top collaborations",
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
            selected_dev_name = st.selectbox("Choose a developer:", dev_names, key="dev_select")
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
            selected_pub_name = st.selectbox("Choose a publisher:", pub_names, key="pub_select")
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
    # Top collaborations
    # ------------------------------------------------------------------
    with tab_top:
        st.subheader("Top developer by publisher collaborations")

        st.write(
            """
            **Two modes:**
            - **Slice mode:** uses the small graph built above (fast, supports BFS/DFS).
            - **FULL dataset (fast):** computes using link tables directly (no graph build).
            """
        )

        mode = st.radio(
            "Choose computation mode:",
            ["Slice graph mode", "FULL dataset (fast)"],
            horizontal=True,
            key="top_mode",
        )

        if mode == "Slice graph mode":
            st.caption("Uses the graph slice shown in the other tabs.")

            if st.button("Find top developer in this graph slice", key="top_dev_btn"):
                top_dev, total = developer_with_most_publisher_collaborations(graph, dev_vertices)
                st.session_state["top_dev_vertex"] = top_dev
                st.session_state["top_dev_total"] = total
                st.session_state["top_dev_collabs"] = (
                    get_publisher_collaborations_for_developer(graph, top_dev) if top_dev else []
                )

            top_dev = st.session_state.get("top_dev_vertex")
            if top_dev is not None:
                st.success(f"Top developer: **{_vertex_label(top_dev)}**")
                st.write(f"Total collaborations (sum of weights): **{st.session_state.get('top_dev_total', 0)}**")

                collabs = st.session_state.get("top_dev_collabs", [])
                _render_collaborations_table(collabs, title="Publishers collaborating with the top developer")

            st.markdown("---")
            st.subheader("Inspect collaborations for a chosen developer (slice mode)")

            dev_names = sorted(dev_by_name.keys())
            if not dev_names:
                st.info("No developers available in this slice.")
            else:
                chosen_name = st.selectbox("Pick a developer:", dev_names, key="dev_collab_pick")
                chosen_dev = dev_by_name[chosen_name]

                if st.button("Show collaborations for this developer", key="dev_collab_btn"):
                    st.session_state["manual_dev_vertex"] = chosen_dev
                    st.session_state["manual_collabs"] = get_publisher_collaborations_for_developer(graph, chosen_dev)

                manual_dev = st.session_state.get("manual_dev_vertex")
                if manual_dev is not None:
                    st.info(f"Developer: **{_vertex_label(manual_dev)}**")
                    manual_collabs = st.session_state.get("manual_collabs", [])
                    _render_collaborations_table(manual_collabs, title="Publishers collaborating with this developer")

        else:
            st.caption("Computes on the FULL dataset (fast) without creating a huge graph.")

            if st.button("Find top developer in FULL dataset", key="top_full_btn"):
                top_did, total = _compute_top_developer_full_dataset(cleaned_data)
                st.session_state["full_top_did"] = top_did
                st.session_state["full_top_total"] = total
                st.session_state["full_top_pub_stats"] = (
                    _compute_publisher_collabs_for_developer_full_dataset(cleaned_data, top_did)
                    if top_did is not None else []
                )

            top_did = st.session_state.get("full_top_did")
            if top_did is not None:
                st.success(f"Top developer: **{dev_name_by_id.get(top_did, f'Developer #{top_did}')}**")
                st.write(f"Total collaborations (sum of weights): **{st.session_state.get('full_top_total', 0)}**")

                pub_stats = st.session_state.get("full_top_pub_stats", [])
                _render_full_dataset_table(
                    pub_stats,
                    pub_name_by_id,
                    title="Publishers collaborating with the top developer (FULL dataset)",
                )
            else:
                st.info("Click the button above to compute the full-dataset top developer.")

            st.markdown("---")
            st.subheader("Inspect collaborations for a developer by ID (FULL dataset)")

            dev_id_input = st.number_input("Developer ID:", min_value=0, value=0, step=1, key="full_dev_id")
            sample_k = st.slider("Sample appids per publisher", 0, 20, 10, key="sample_k_full")

            if st.button("Show FULL dataset collaborations for this developer", key="full_dev_btn"):
                stats = _compute_publisher_collabs_for_developer_full_dataset(
                    cleaned_data, int(dev_id_input), sample_k_appids=int(sample_k)
                )
                st.session_state["full_manual_stats"] = stats
                st.session_state["full_manual_did"] = int(dev_id_input)

            manual_stats = st.session_state.get("full_manual_stats")
            manual_did = st.session_state.get("full_manual_did")
            if manual_stats is not None and manual_did is not None:
                st.info(f"Developer: **{dev_name_by_id.get(manual_did, f'Developer #{manual_did}')}**")
                _render_full_dataset_table(
                    manual_stats,
                    pub_name_by_id,
                    title="Publishers collaborating with this developer (FULL dataset)",
                )

    # ------------------------------------------------------------------
    # Graph summary
    # ------------------------------------------------------------------
    with tab_summary:
        st.subheader("Global graph statistics (slice graph)")

        v_count = graph.vertex_count()
        e_count = graph.edge_count()
        st.write(f"**Vertices:** {v_count}  |  **Edges:** {e_count}")

        comps = connected_components(graph)
        comp_sizes = sorted((len(c) for c in comps), reverse=True)
        st.write(f"**Connected components:** {len(comp_sizes)}")

        if comp_sizes:
            st.write(f"Largest component size: **{max(comp_sizes)}** vertices")
            top_sizes = comp_sizes[:10]
            st.table({
                "Component #": list(range(1, len(top_sizes) + 1)),
                "Size": top_sizes,
            })

        st.markdown("---")
        st.subheader("Most connected developers/publishers in this slice")

        rows = [{"label": _vertex_label(v), "degree": graph.degree(v)} for v in graph.vertices()]
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
    neighbors = []
    for edge in graph.incident_edges(v):
        u, w = edge.endpoints()
        other = w if v is u else u

        row = other.element() or {}
        name = row.get("name") or f"{other.kind()} #{other.id()}"

        data = edge.element() or {}
        games = data.get("games")
        weight = data.get("weight", 0)
        n_games = len(games) if isinstance(games, set) else int(weight)

        neighbors.append({
            "Neighbor": name,
            "Role": other.kind(),
            "Games together": n_games,
        })

    if not neighbors:
        st.info("This vertex has no neighbors in the current graph slice.")
        return

    neighbors.sort(key=lambda r: r["Games together"], reverse=True)
    top = neighbors[:25]

    st.write(f"Found **{len(neighbors)}** neighbors for this {role}.")
    st.table({
        "Neighbor": [r["Neighbor"] for r in top],
        "Role": [r["Role"] for r in top],
        "Games together": [r["Games together"] for r in top],
    })


def _render_traversal(graph: Graph, start: Graph.Vertex, mode: str = "bfs") -> None:
    if mode == "bfs":
        order = bfs_traversal(graph, start)
        title = "BFS traversal order"
    else:
        order = dfs_traversal(graph, start)
        title = "DFS traversal order"

    if not order:
        st.info("Traversal returned no vertices.")
        return

    labels = [_vertex_label(v) for v in order[:40]]
    st.write(f"{title} (first {len(labels)} vertices shown):")
    st.code(" -> ".join(labels))
