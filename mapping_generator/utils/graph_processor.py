# mapping_generator/utils/graph_processor.py

import networkx as nx
from .mapping import Mapping
from .graph_topology import calculate_topological_levels

class GraphProcessor:
    """Provides utility functions for processing and validating mappings."""

    def __init__(self, mapping: Mapping):
        """Initializes the processor with a mapping object."""
        self.mapping = mapping
        self.dfg = self._build_dfg_from_mapping()

    def _build_dfg_from_mapping(self) -> nx.DiGraph:
        """Constructs a NetworkX DiGraph from the mapping's routing information."""
        dfg = nx.DiGraph()
        nodes = set(self.mapping.placement.keys())
        dfg.add_nodes_from(nodes)
        
        for (source_id, dest_id) in self.mapping.routing.keys():
            if source_id in nodes and dest_id in nodes:
                dfg.add_edge(source_id, dest_id)
        return dfg

    def _calculate_levels(self):
        """Calculates the topological level of each node in the DFG.

        The level of a node is the length of the longest path from an input
        node to it. This is stored as a 'level' attribute on each node.
        """
        calculate_topological_levels(self.dfg)

    def _is_balanced(self) -> bool:
        """Checks if the DFG is balanced.

        A DFG is considered balanced if all predecessors of any given node
        reside at the same topological level.

        Returns:
            bool: True if the graph is balanced, False otherwise.
        """
        for node in self.dfg.nodes():
            predecessors = list(self.dfg.predecessors(node))
            if len(predecessors) > 1:
                first_level = self.dfg.nodes[predecessors[0]].get('level')
                if first_level is None: return False 
                
                for p in predecessors[1:]:
                    if self.dfg.nodes[p].get('level') != first_level:
                        return False
        return True

    def is_valid(self) -> bool:
        """Performs a full validation of the DFG.

        A valid DFG must be:
        1. Weakly connected.
        2. A Directed Acyclic Graph (DAG).
        3. Balanced (all predecessors of a node are at the same level).

        Returns:
            bool: True if all validation checks pass, False otherwise.
        """
        if self.dfg.number_of_nodes() < 2:
            return False

        if not nx.is_weakly_connected(self.dfg):
            return False
        if not nx.is_directed_acyclic_graph(self.dfg):
            return False
        
        self._calculate_levels()
        if not self._is_balanced():
            return False
            
        return True
