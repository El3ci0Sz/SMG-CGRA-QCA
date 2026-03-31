# utils/graph_topology.py

import networkx as nx
import logging
from typing import Dict

logger = logging.getLogger(__name__)

def calculate_topological_levels(graph: nx.DiGraph, attribute_name: str = 'level') -> Dict[any, int]:
    levels = {}
    try:
        for node in nx.topological_sort(graph):
            preds = list(graph.predecessors(node))
            if not preds:
                level = 0
            else:
                level = max(levels[p] for p in preds) + 1
            
            levels[node] = level
            graph.nodes[node][attribute_name] = level
            
        return levels
    except nx.NetworkXUnfeasible:
        logger.warning("O grafo contém ciclos; não é possível calcular os níveis topológicos.")
        return {}
