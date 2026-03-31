import os
from typing import Dict, Optional, Tuple, Any

class OutputPathManager:
    """
    Manages file naming conventions and directory structures.
    Centralizes naming rules to ensure consistency across the project.
    """
    
    BIT_TO_NAME = {
        '1000': 'mesh',
        '1001': 'mesh-toroidal',
        '1111': 'all',
        '1010': 'mesh-onehop'
    }
    
    @staticmethod
    def build_subdirs(
        tec_name: str,
        gen_mode: str,
        difficulty: Optional[int | str] = None,
        interconnect: Optional[str] = None,
        arch_size: Optional[Tuple[int, int]] = None,
        num_nodes: Optional[int] = None,
        qca_arch_type: Optional[str] = None
    ) -> str:
        """
        Constructs the subdirectory path based on generation parameters.
        
        Args:
            tec_name (str): The technology name (e.g., 'QCA' or 'CGRA').
            gen_mode (str): The generation strategy used.
            difficulty (Optional[int | str]): The difficulty level of the generation.
            interconnect (Optional[str]): The interconnection architecture type.
            arch_size (Optional[Tuple[int, int]]): The grid dimensions (rows, cols).
            num_nodes (Optional[int]): The total number of nodes in the graph.
            qca_arch_type (Optional[str]): The QCA clock zone architecture type.
            
        Returns:
            str: The relative path for the output directory.
        """
        subdirs = []
        
        if tec_name == "QCA":
            base_folder = f"mappings_qca_{gen_mode}"
            subdirs.append(base_folder)
            
            if qca_arch_type:
                subdirs.append(qca_arch_type)
            if arch_size:
                subdirs.append(f"{arch_size[0]}x{arch_size[1]}")
            if num_nodes:
                subdirs.append(f"{num_nodes}_nodes")
        
        elif tec_name == "CGRA":
            if gen_mode == 'grammar':
                if difficulty == 'random':
                    base_folder = "grammar_random_difficulty"
                elif difficulty == 'smart_random':
                    base_folder = "grammar_smart_random"
                elif isinstance(difficulty, int):
                    base_folder = "grammar_systematic_difficulty"
                else:
                    base_folder = f"mappings_cgra_{gen_mode}"
            else:
                base_folder = f"mappings_cgra_{gen_mode}"
            
            subdirs.append(base_folder)
            
            if interconnect:
                subdirs.append(interconnect)
            if arch_size:
                subdirs.append(f"{arch_size[0]}x{arch_size[1]}")
            if num_nodes:
                subdirs.append(f"{num_nodes}_nodes")
        
        return os.path.join(*subdirs)
    
    @staticmethod
    def build_filename(
        tec_name: str,
        arch_size: Tuple[int, int],
        num_nodes: int,
        num_edges: int,
        difficulty: int | str,
        index: int,
        is_fallback: bool = False
    ) -> str:
        """
        Generates a standardized filename for the output files.
        
        Args:
            tec_name (str): The technology name.
            arch_size (Tuple[int, int]): The grid dimensions (rows, cols).
            num_nodes (int): The total number of nodes in the graph.
            num_edges (int): The total number of edges in the graph.
            difficulty (int | str): The difficulty level or constraint identifier.
            index (int): The unique index of the generated graph.
            is_fallback (bool): Indicates if the file was generated using a fallback strategy.
            
        Returns:
            str: The formatted filename without extension.
        """
        arch_str = f"{arch_size[0]}x{arch_size[1]}"
        
        if is_fallback and isinstance(difficulty, int):
            diff_str = f"{difficulty}fb"
        else:
            diff_str = str(difficulty)
        
        return (
            f"{tec_name.lower()}_map_"
            f"diff{diff_str}_{arch_str}_"
            f"N{num_nodes}_E{num_edges}_{index}"
        )
    
    @staticmethod
    def get_interconnect_name(bits: str) -> str:
        """
        Returns the interconnection name based on the provided bitmask.
        
        Args:
            bits (str): The bitmask representing the interconnection type.
            
        Returns:
            str: The mapped interconnection name or 'custom'.
        """
        return OutputPathManager.BIT_TO_NAME.get(bits, "custom")
    
    @staticmethod
    def build_metadata(
        tec_name: str,
        num_nodes: int,
        num_edges: int,
        arch_size: Tuple[int, int],
        gen_mode: str,
        difficulty: Optional[int | str] = None,
        recipe: Optional[Dict] = None,
        alpha: Optional[float] = None,
        ii: Optional[int] = None,
        bits: Optional[str] = None,
        interconnect_name: Optional[str] = None,
        qca_arch_type: Optional[str] = None,
        metrics: Optional[Dict] = None,
        **extra_fields
    ) -> Dict[str, Any]:
        """
        Constructs a comprehensive metadata dictionary for the JSON output.
        
        Args:
            tec_name (str): The technology name.
            num_nodes (int): The total number of nodes.
            num_edges (int): The total number of edges.
            arch_size (Tuple[int, int]): The grid dimensions.
            gen_mode (str): The generation strategy.
            difficulty (Optional[int | str]): The difficulty level.
            recipe (Optional[Dict]): The generation recipe constraints.
            alpha (Optional[float]): The alpha probability for random edges.
            ii (Optional[int]): The initiation interval.
            bits (Optional[str]): The CGRA interconnection bitmask.
            interconnect_name (Optional[str]): The mapped interconnection name.
            qca_arch_type (Optional[str]): The QCA architecture type.
            metrics (Optional[Dict]): Collected graph metrics and statistics.
            **extra_fields: Additional fields to append to the metadata.
            
        Returns:
            Dict[str, Any]: The structured metadata dictionary.
        """
        metadata = {
            'tec_name': tec_name,
            'tec': tec_name.lower(),
            'technology': tec_name,
            'gen_mode': gen_mode,
            'mode': gen_mode,
            'num_nodes': num_nodes,
            'num_edges': num_edges,
            'arch_size': list(arch_size),
            'architecture_dimensions': f"{arch_size[0]}x{arch_size[1]}"
        }
        
        graph_properties = {
            "node_count": num_nodes,
            "edge_count": num_edges
        }
        if tec_name == "CGRA" and ii is not None:
            graph_properties["II"] = ii
            metadata['ii'] = ii
        metadata['graph_properties'] = graph_properties
        
        generation_properties = {}
        if difficulty is not None:
            generation_properties["difficulty"] = difficulty
            metadata['difficulty'] = difficulty
            if isinstance(difficulty, int) and recipe:
                generation_properties["recipe"] = recipe
                metadata['recipe'] = recipe
        
        if alpha is not None:
            generation_properties["alpha"] = alpha
            metadata['alpha'] = alpha
        
        if generation_properties:
            metadata['generation_properties'] = generation_properties
        
        arch_props = {
            "type": tec_name,
            "dimensions": list(arch_size)
        }
        
        if tec_name == "CGRA":
            if bits:
                arch_props["interconnections"] = {
                    "mesh": bool(int(bits[0])),
                    "diagonal": bool(int(bits[1])),
                    "one_hop": bool(int(bits[2])),
                    "toroidal": bool(int(bits[3]))
                }
                metadata['bits'] = bits
            if interconnect_name:
                arch_props["interconnection_name"] = interconnect_name
                metadata['interconnect_name'] = interconnect_name
        
        if tec_name == "QCA" and qca_arch_type:
            arch_props["qca_arch_type"] = qca_arch_type
            metadata['qca_arch_type'] = qca_arch_type
        
        metadata['architecture_properties'] = arch_props
        
        if metrics:
            metadata['metrics'] = metrics
        
        metadata.update(extra_fields)
        return metadata

