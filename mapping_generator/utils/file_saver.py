import os
import json
import re
import logging
import networkx as nx
from typing import Dict, Optional, Tuple, Any
from .visualizer import GraphVisualizer
from .path_manager import OutputPathManager

logger = logging.getLogger(__name__)



class FileSaver:
    """
    Handles saving generated graphs in various formats including DOT, JSON, and PNG.
    """
    
    def __init__(self, output_dir: str, no_images: bool = False):
        """
        Initializes the FileSaver instance.
        
        Args:
            output_dir (str): Base directory for saving files.
            no_images (bool): Flag to disable PNG image generation.
        """
        self.output_dir = output_dir
        self.no_images = no_images
        os.makedirs(output_dir, exist_ok=True)
    
    def save_graph(
        self,
        graph: nx.DiGraph,
        filename_base: str,
        metadata: Dict[str, Any],
        subdirs: str
    ) -> Dict[str, Optional[str]]:
        """
        Saves the generated graph to disk in the required formats.
        
        Args:
            graph (nx.DiGraph): The graph to save.
            filename_base (str): The base filename without extension.
            metadata (Dict[str, Any]): The metadata dictionary for the JSON file.
            subdirs (str): The relative subdirectory path to save the files into.
            
        Returns:
            Dict[str, Optional[str]]: A dictionary containing paths to the saved files.
        """
        full_dir = os.path.join(self.output_dir, subdirs)
        os.makedirs(full_dir, exist_ok=True)
        
        path_base = os.path.join(full_dir, filename_base)
        dot_path = f"{path_base}.dot"
        json_path = f"{path_base}.json"
        png_path = f"{path_base}.png" if not self.no_images else None
        
        paths = {}
        
        try:
            if self.no_images:
                GraphVisualizer.generate_dot_file_only(graph, dot_path)
            else:
                GraphVisualizer.generate_custom_dot_and_image(graph, dot_path, path_base)
            paths['dot'] = dot_path
            
            self._save_json(graph, json_path, metadata)
            paths['json'] = json_path
            paths['png'] = png_path
            
            logger.debug(f"Graph saved: {filename_base}")
            return paths
            
        except Exception as e:
            logger.error(f"Error saving graph {filename_base}: {e}", exc_info=True)
            raise
    
    def _save_json(self, graph: nx.DiGraph, json_path: str, metadata: Dict[str, Any]):
        """
        Saves the graph structure and metadata to a structured JSON file.
        
        Args:
            graph (nx.DiGraph): The graph instance.
            json_path (str): The complete file path where the JSON will be saved.
            metadata (Dict[str, Any]): The metadata to embed in the JSON.
        """
        placement = {}
        for node, data in graph.nodes(data=True):
            node_name = data.get('name', str(node))
            if isinstance(node, tuple) and len(node) >= 2:
                placement[node_name] = list(node)
            else:
                placement[node_name] = [0, 0]
        
        edges = []
        for src, dst in graph.edges():
            src_name = graph.nodes[src].get('name', str(src))
            dst_name = graph.nodes[dst].get('name', str(dst))
            edges.append([src_name, dst_name])
        
        json_data = {
            'graph_name': os.path.basename(json_path).replace('.json', ''),
            'metadata': metadata,
            'placement': placement,
            'edges': edges
        }
        
        if metadata.get('graph_properties'):
            json_data['graph_properties'] = metadata['graph_properties']
            
        if metadata.get('architecture_properties'):
            json_data['architecture_properties'] = metadata['architecture_properties']
            
        if 'generation_properties' in metadata:
            json_data['generation_properties'] = metadata['generation_properties']
        
        pretty_json = json.dumps(json_data, indent=2)
        compacted_json = self._compact_coordinates(pretty_json)
        
        with open(json_path, 'w') as f:
            f.write(compacted_json)
    
    @staticmethod
    def _compact_coordinates(json_string: str) -> str:
        """
        Compacts array representations in the JSON string for better readability.
        
        Args:
            json_string (str): The raw JSON string.
            
        Returns:
            str: The formatted JSON string with compacted coordinates.
        """
        return re.sub(
            r'\[\s*(-?\d+),\s*(-?\d+)(,\s*-?\d+)?\s*\]',
            lambda m: '[' + ', '.join(re.split(r',\s*', m.group(0)[1:-1])) + ']',
            json_string
        )

    def save_for_ml(self, placement_graph: nx.DiGraph, qca_architecture, filename_base: str, subdirs: str):
        full_dir = os.path.join(self.output_dir, subdirs)
        os.makedirs(full_dir, exist_ok=True)
        json_ml_path = os.path.join(full_dir, f"{filename_base}_ML.json")

        # Pega todas as coordenadas do grid QCA
        qca_grid_nodes = list(qca_architecture.get_graph().nodes())
        
        #Ordenacao topologica
        topological_order_coords = list(nx.topological_sort(placement_graph))

        coord_to_abstract_id = {}
        abstract_id_to_coord = {}  
        gate_nodes_features = []

        # Vamos mapear as ferramentas (inputs, outputs, operations, routing) para números 
        type_to_int = {'input': 0, 'operation': 1, 'routing': 2, 'output': 3, 'unknown': 4}

        for abstract_id, coord in enumerate(topological_order_coords):
            coord_to_abstract_id[coord] = abstract_id
            abstract_id_to_coord[abstract_id] = list(coord) 
            
            node_data = placement_graph.nodes[coord]
            node_type_str = node_data.get('type', 'unknown')
            
            gate_nodes_features.append({
                "id": abstract_id,
                "type_str": node_type_str,
                "type_int": type_to_int.get(node_type_str, 4)
            })
    
        #Pegas as arestas
        gate_edges = []
        for src, dst in placement_graph.edges():
            abstract_src = coord_to_abstract_id[src]
            abstract_dst = coord_to_abstract_id[dst]
            gate_edges.append([abstract_src, abstract_dst])

        #Repultado final
        ml_dataset = {
            "dataset_info": {
                "graph_name": filename_base,
                "num_logical_nodes": len(gate_nodes_features),
                "qca_grid_dimensions": qca_architecture.dim
            },
            "inputs": {
                "logical_nodes": gate_nodes_features, # O circuito em  ordem (Para Transformer)
                "logical_edges": gate_edges,          # As conexões 
                "qca_grid": [list(c) for c in qca_grid_nodes] # O grid
            },
            "targets": {
                "placement_labels": abstract_id_to_coord 
            }
        }
        
        with open(json_ml_path, 'w') as f:
            json.dump(ml_dataset, f, indent=2) 
            
        logger.debug(f"ML Dataset salvo: {filename_base}_ML.json")
        return json_ml_path
