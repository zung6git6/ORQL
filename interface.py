import streamlit as st

import re
import json
from collections import defaultdict

import networkx as nx
from pyvis.network import Network

import tempfile
import os

import matplotlib.colors as mcolors
import community as community_louvain

from utils import OneRingDB, ORQueryExecutor

import time

def greedy_coloring(graph):
    color_assignment = {}

    for node in graph:
        neighbour_colors = {color_assignment[neighbour] for neighbour in graph[node] if neighbour in color_assignment}

        color = 0
        while color in neighbour_colors:
            color += 1

        color_assignment[node] = color

    return color_assignment

def draw_graph(base: OneRingDB):
    G = nx.Graph()

    for node in base.get_all_nodes():
        G.add_node(node.Name, label=node.Name, title=f"Class: {node.Node_class}\nProps: {node.Properties}")

    for edge in base.EdgeDictionary.values():
        G.add_edge(
            base.get_node_by_id(edge.Source_id).Name,
            base.get_node_by_id(edge.Target_id).Name,
            label=edge.Edge_class,
            title=str(edge.Properties),
        )

    if 'CLUSTER' in st.session_state and st.session_state.CLUSTER:
        # détection des communautés avec Louvain
        partition = community_louvain.best_partition(G)

        # trouver les hubs dans chaque communauté
        community_nodes = defaultdict(list)
        for node, comm in partition.items():
            community_nodes[comm].append(node)

        hubs = []
        for comm_id, nodes in community_nodes.items():
            subgraph = G.subgraph(nodes)
            # trouver les noeuds avec le plus haut degré
            max_deg = max(dict(subgraph.degree()).values())
            for node in subgraph.nodes:
                node_in_base = base.get_node_by_name(node)
                if subgraph.degree(node) == max_deg:
                    hubs.append(node)
                    node_in_base.HUB = True
                    base.NodeDictionary[node_in_base.Id].HUB = True
                else:
                    node_in_base.HUB = False
                    base.NodeDictionary[node_in_base.Id].HUB = False

        # appliquer les attributs dans le graphe final
        for node in G.nodes():
            is_hub = node in hubs
            if is_hub:
                G.nodes[node]["title"] += "\n HUB"
                G.nodes[node]["size"] = 30
                G.nodes[node]["shape"] = "star"
            else:
                G.nodes[node]["title"] += ""
                G.nodes[node]["size"] = 20
                G.nodes[node]["shape"] = "dot"

    # coloriage
    if 'COLOR' in st.session_state and st.session_state.COLOR:
        coloring = greedy_coloring(dict(G.adjacency()))
        color_palette = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())

        for node, color_id in coloring.items():
            color_hex = color_palette[color_id % len(color_palette)]  # éviter dépassement
            G.nodes[node]['color'] = color_hex

    # visualisation
    if not ignore_direction:
        net = Network(height="600px", width="100%", notebook=False, directed=True)
    else:
        net = Network(height="600px", width="100%", notebook=False, directed=False)
    net.from_nx(G)
    net.repulsion(node_distance=200, central_gravity=0.3)

    tmp_dir = tempfile.mkdtemp()
    path = os.path.join(tmp_dir, "graph.html")
    net.save_graph(path)
    return path, G

st.set_page_config(page_title="OneRingDB Explorer", layout="wide")
st.title("OneRingDB Explorer")
if 'COLOR' not in st.session_state:
    st.session_state.COLOR = False
if 'LINEARISE' not in st.session_state:
    st.session_state.LINEARISE = False

# sidebar
st.sidebar.header("Interroger la base")
uploaded_file = st.sidebar.file_uploader("Charger un fichier JSON", type="json")

query_input = st.sidebar.text_area("Entrez une requête ORQL", height=200)
ignore_direction = st.sidebar.checkbox("Ignore Direction", value=False)
run_query = st.sidebar.button("Exécuter")


# load JSON file
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = ""

if uploaded_file and st.session_state.uploaded_file != uploaded_file:
    st.session_state.uploaded_file = uploaded_file
    content = json.load(uploaded_file)
    nodes = content.get("nodes", {})
    relationships = content.get("relationships", [])

    st.session_state.base = OneRingDB()
    st.session_state.CLUSTER = False
    st.session_state.COLOR = False
    st.session_state.LINEARISE = False
    for node_name, class_name in nodes.items():
        st.session_state.base.create_node(node_name, class_name)

    for source_name, target_name, edge_class, edge_properties in relationships:
        st.session_state.base.create_edge(
            st.session_state.base.get_node_by_name(source_name).Id,
            st.session_state.base.get_node_by_name(target_name).Id,
            edge_class,
            edge_properties
        )
    st.success("✅ Base de données chargée !")

if 'base' in st.session_state:
    # run ORQL query
    if run_query and query_input.strip():
        start_time = time.time()
        ORQueryExecutor(query_input, st.session_state.base, ignore_direction=ignore_direction)
        end_time = time.time()
        elapsed_time = end_time - start_time

        st.success(f"✅ Requête exécutée en {elapsed_time:.3f} secondes.")

    base = st.session_state.base
    st.subheader("Statistiques")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Nombre de noeuds", len(base.NodeDictionary))
    with col2:
        st.metric("Nombre d'arêtes", len(base.EdgeDictionary))

    # traçer le graphe
    st.subheader("Graphe Interactif")

    if len(base.NodeDictionary) > 0:
        start_time = time.time()

        html_path, Graph = draw_graph(base)
        st.session_state.html_path = html_path
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=600, scrolling=True)

        end_time = time.time()
        elapsed = end_time - start_time
        st.success(f"Graphe affiché en {elapsed:.3f} secondes.")
        
        # linéarisation des triplets
        if st.session_state.LINEARISE:
            st.subheader("Triplets Linéarisés")

            triplets_text = []
            for edge in base.EdgeDictionary.values():
                source_name = base.get_node_by_id(edge.Source_id).Name
                target_name = base.get_node_by_id(edge.Target_id).Name
                predicate = edge.Edge_class
                triplet = f"{source_name} --{predicate}--> {target_name}"
                triplets_text.append(triplet)

            st.code("\n".join(triplets_text), language='text')
    else:
        st.info("Charge un fichier JSON pour voir le graphe.")