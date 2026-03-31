import random
import networkx as nx
import logging
from typing import Optional, List, Tuple, Set, Dict
from collections import defaultdict

try:
    from ...architectures.qca import QCA
except ImportError:
    pass

logger = logging.getLogger(__name__)


class QcaBackwardsGenerator:
    """
    Reverse QCA Mapping Generator
    """

    _VALID_OUTPUT_BORDERS = {
        'U': {'top', 'bottom', 'left', 'right'},
        'R': {'right', 'bottom'},
        'T': {'right', 'bottom'},
    }

    def __init__(self, qca_architecture, target_gates: int, num_outputs: int = 1):
        """
        Initializes the QcaBackwardsGenerator with the given QCA architecture and generation parameters.

        Sets up internal data structures including the placement graph, used nodes, border nodes,
        density map, frontier-by-quadrant index, and architecture-specific behavioural flags
        (density bias, quadrant-front expansion, inertia probability).

        :param qca_architecture: QCA architecture object providing graph topology, dimensions,
                                 and border nodes.
        :param target_gates: Minimum number of logic gates the generated circuit must contain.
        :param num_outputs: Number of output nodes to place in the circuit (default: 1).
        """
        self.qca_architecture = qca_architecture
        self.target_gates = target_gates
        self.num_outputs = num_outputs
        self.arch_type = getattr(qca_architecture, 'arch_type', 'U')

        if target_gates >= 20:
            self.internal_generation_target = int(target_gates * 1.5)
        else:
            self.internal_generation_target = int(target_gates * 2.5)

        self.placement_graph = nx.DiGraph()
        self.used_nodes: Set[Tuple[int, int]] = set()
        self.border_nodes = self.qca_architecture.get_border_nodes()
        self.arch_graph = None
        self.node_depth = {}

        rows, cols = self.qca_architecture.dim
        self.dim = (rows, cols)
        self.mid_row = rows // 2
        self.mid_col = cols // 2

        self._use_density_bias   = (self.arch_type == 'U')
        self._use_quadrant_front = (self.arch_type == 'U') 
        self._density_weight     = 0.1 if self._use_density_bias else 0.0
        self._inertia_prob       = 0.80 if self.arch_type == 'U' else 0.30

        logger.debug(
            f"BackwardsGenerator arch={self.arch_type} | "
            f"density={self._use_density_bias} | "
            f"quad_front={self._use_quadrant_front} | "
            f"inertia={self._inertia_prob}"
        )

        self.frontier_by_quad: Dict[Tuple[int, int], List] = defaultdict(list)
        self._density_cell_size = max(3, min(rows, cols) // 10)
        self._density_map: Dict[Tuple[int, int], int] = defaultdict(int)

    def generate(self) -> Optional[nx.DiGraph]:
        """
        Executes the backwards circuit generation algorithm and returns the resulting placement graph.

        Seeds output nodes on valid border positions, then iteratively expands the circuit
        backwards by attempting gate insertion, wire routing, predecessor sharing, and crossover
        placement. After expansion, rescues dangling branches, prunes dead paths, and validates
        the graph for acyclicity, weak connectivity, and gate-count requirements.

        :return: A directed acyclic placement graph (nx.DiGraph) containing input, output,
                 operation, routing, and crossover nodes if all constraints are satisfied;
                 ``None`` otherwise.
        """
        self.placement_graph.clear()
        self.used_nodes.clear()
        self.node_depth.clear()
        self.frontier_by_quad.clear()
        self._density_map.clear()
        self.arch_graph = self.qca_architecture.get_graph()

        frontier = self._seed_outputs()
        if len(frontier) != self.num_outputs:
            return None

        current_gates = 0
        max_iter = self.internal_generation_target * 60
        iter_count = 0

        while iter_count < max_iter and self._frontier_nonempty(frontier):
            iter_count += 1

            current_node = self._pick_node(frontier)
            self._remove_node(frontier, current_node)

            is_border = current_node in self.border_nodes
            wants_more_gates = current_gates < self.internal_generation_target

            if is_border and self.placement_graph.nodes[current_node].get('type') != 'output':
                if not wants_more_gates or random.random() < 0.05:
                    self._finalize_as_input(current_node)
                    continue

            success = False

            if random.random() < 0.6:
                if self._try_share_predecessor(current_node):
                    success = True

            if not success and wants_more_gates and random.random() < 0.35:
                preds = self._add_gate_logic(current_node)
                if preds:
                    for p in preds:
                        self._add_to_frontier(frontier, p)
                    current_gates += 1
                    success = True

            if not success:
                cross = self._try_crossover(current_node)
                if cross:
                    self._add_to_frontier(frontier, cross)
                    success = True

            if not success:
                pred = self._add_wire_logic(current_node)
                if pred:
                    self._add_to_frontier(frontier, pred)
                else:
                    if is_border and self.placement_graph.nodes[current_node].get('type') != 'output':
                        self._finalize_as_input(current_node)
                    else:
                        self.placement_graph.nodes[current_node]['stuck'] = True

        leaves = [
            n for n in self.placement_graph.nodes()
            if self.placement_graph.in_degree(n) == 0
            and self.placement_graph.nodes[n].get('type') != 'input'
        ]
        for node in leaves:
            self._rescue_route_to_border(node)

        self._prune_dead_branches()

        if not nx.is_directed_acyclic_graph(self.placement_graph):
            return None
        if not nx.is_weakly_connected(self.placement_graph):
            return None

        final_outputs = [n for n, d in self.placement_graph.nodes(data=True) if d.get('type') == 'output']
        final_inputs  = [n for n, d in self.placement_graph.nodes(data=True) if d.get('type') == 'input']
        final_gates   = len([n for n, d in self.placement_graph.nodes(data=True) if d.get('type') == 'operation'])

        if len(final_outputs) != self.num_outputs:
            return None
        if len(final_inputs) == 0:
            return None
        if final_gates < self.target_gates:
            return None

        return self.placement_graph

    def _fast_path_exists(self, start: Tuple[int, int], target: Tuple[int, int]) -> bool:
        """
        Checks whether a directed path exists from ``start`` to ``target`` in the placement graph.

        Uses an iterative depth-first search to avoid the overhead of ``nx.has_path`` on large graphs.

        :param start: Source node coordinates (row, col).
        :param target: Destination node coordinates (row, col).
        :return: ``True`` if a directed path from ``start`` to ``target`` exists; ``False`` otherwise.
        """
        if start == target:
            return True
        stack = [start]
        visited = {start}
        while stack:
            curr = stack.pop()
            for succ in self.placement_graph.successors(curr):
                if succ == target:
                    return True
                if succ not in visited:
                    visited.add(succ)
                    stack.append(succ)
        return False


    def _classify_border_side(self, node: Tuple[int, int]) -> str:
        """
        Returns the border side label for a given node based on its grid position.

        Compares the node's row and column indices against the architecture dimensions
        to determine which edge of the grid it belongs to.

        :param node: Node coordinates (row, col).
        :return: One of ``'top'``, ``'bottom'``, ``'left'``, or ``'right'``.
        """
        rows, cols = self.dim
        r, c = node
        if r == 0:        return 'top'
        if r == rows - 1: return 'bottom'
        if c == 0:        return 'left'
        return 'right'

    def _seed_outputs(self) -> List[Tuple[int, int]]:
        """
        Places output nodes on valid border positions and returns the initial frontier.

        Filters border nodes by the sides allowed for the current architecture type,
        shuffles candidates per side, and assigns output labels in a round-robin fashion
        across sides until ``num_outputs`` outputs are placed.

        :return: List of output node coordinates that form the initial expansion frontier.
        """
        valid_sides = self._VALID_OUTPUT_BORDERS.get(self.arch_type, {'right', 'bottom'})

        sides: Dict[str, List] = defaultdict(list)
        for n in self.border_nodes:
            side = self._classify_border_side(n)
            if side in valid_sides and list(self.arch_graph.predecessors(n)):
                sides[side].append(n)

        for side in sides:
            random.shuffle(sides[side])

        side_order = [s for s in ['right', 'bottom', 'top', 'left'] if sides.get(s)]
        frontier = []
        placed = 0
        side_idx = 0

        while placed < self.num_outputs and any(sides.values()):
            if not side_order:
                break
            side = side_order[side_idx % len(side_order)]
            side_idx += 1
            if not sides.get(side):
                continue
            node = sides[side].pop()
            self.placement_graph.add_node(node, type='output', name=f"OUT_{node}")
            self.used_nodes.add(node)
            self._register_used(node)
            self.node_depth[node] = 0
            self._add_to_frontier(frontier, node)
            placed += 1

        return frontier

    def _get_quad(self, node: Tuple[int, int]) -> Tuple[int, int]:
        """
        Returns the quadrant index of a node relative to the grid centre.

        Divides the grid into four quadrants using the midpoint of rows and columns.

        :param node: Node coordinates (row, col).
        :return: Tuple ``(row_half, col_half)`` where each component is ``0`` (upper/left)
                 or ``1`` (lower/right).
        """
        r, c = node
        return (0 if r < self.mid_row else 1, 0 if c < self.mid_col else 1)

    def _add_to_frontier(self, frontier: list, node):
        """
        Appends a node to the main frontier list and, when quadrant tracking is active,
        also registers it in the per-quadrant index.

        :param frontier: The main frontier list to append the node to.
        :param node: Node coordinates (row, col) to be added.
        """
        frontier.append(node)
        if self._use_quadrant_front:
            self.frontier_by_quad[self._get_quad(node)].append(node)

    def _remove_node(self, frontier: list, node):
        """
        Removes a node from the main frontier list and, if quadrant tracking is enabled,
        from the corresponding quadrant sub-list. Silent if the node is not present.

        :param frontier: The main frontier list to remove the node from.
        :param node: Node coordinates (row, col) to be removed.
        """
        try:
            frontier.remove(node)
        except ValueError:
            pass
        if self._use_quadrant_front:
            try:
                self.frontier_by_quad[self._get_quad(node)].remove(node)
            except ValueError:
                pass

    def _frontier_nonempty(self, frontier: list) -> bool:
        """
        Checks whether the frontier still contains nodes to process.

        :param frontier: The current frontier list.
        :return: ``True`` if the frontier is non-empty; ``False`` otherwise.
        """
        return bool(frontier)

    def _pick_node(self, frontier: list) -> Tuple[int, int]:
        """
        Selects the next node to expand from the frontier using architecture-aware heuristics.

        For architectures with quadrant tracking, preferentially picks from the least-dense
        quadrant to encourage uniform spread. Falls back to random selection otherwise,
        with a bias towards non-border nodes.

        :param frontier: The current frontier list (must be non-empty).
        :return: Selected node coordinates (row, col).
        :raises RuntimeError: If the frontier is empty.
        """
        if not frontier:
            raise RuntimeError("Empty frontier")

        if not self._use_quadrant_front:
            non_border = [n for n in frontier if n not in self.border_nodes]
            if non_border and random.random() < 0.7:
                return random.choice(non_border)
            return random.choice(frontier)

        if random.random() < 0.70:
            quad_density = {
                q: sum(1 for n in self.used_nodes if self._get_quad(n) == q)
                for q in [(0,0),(0,1),(1,0),(1,1)]
                if self.frontier_by_quad[q]
            }
            if quad_density:
                for q in sorted(quad_density, key=lambda x: quad_density[x]):
                    lst = self.frontier_by_quad[q]
                    if lst:
                        non_border = [n for n in lst if n not in self.border_nodes]
                        return random.choice(non_border) if non_border else random.choice(lst)

        return random.choice(frontier)


    def _register_used(self, node: Tuple[int, int]):
        """
        Increments the density counter for the grid cell that contains the given node.

        Only active when density-bias mode is enabled (``_use_density_bias`` is ``True``).
        The density map is keyed by coarse cell indices computed from ``_density_cell_size``.

        :param node: Node coordinates (row, col) whose cell counter should be incremented.
        """
        if not self._use_density_bias:
            return
        r, c = node
        self._density_map[(r // self._density_cell_size, c // self._density_cell_size)] += 1

    def _density_score(self, node: Tuple[int, int]) -> float:
        """
        Computes a local density score for a node based on how crowded its surrounding cells are.

        Aggregates the density counters of the 3×3 neighbourhood of coarse cells around
        the node's cell. Returns ``0.0`` when density-bias mode is disabled.

        :param node: Node coordinates (row, col).
        :return: Sum of density counts in the 3×3 neighbourhood as a float.
        """
        if not self._use_density_bias:
            return 0.0
        r, c = node
        cr, cc = r // self._density_cell_size, c // self._density_cell_size
        return float(sum(
            self._density_map.get((cr+dr, cc+dc), 0)
            for dr in (-1, 0, 1) for dc in (-1, 0, 1)
        ))


    def _get_valid_predecessors(self, node: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Returns the architecture-graph predecessors of a node that have not yet been placed.

        :param node: Node coordinates (row, col) whose predecessors are queried.
        :return: List of unoccupied predecessor node coordinates, or an empty list if
                 the node is not present in the architecture graph.
        """
        if node not in self.arch_graph:
            return []
        return [p for p in self.arch_graph.predecessors(node) if p not in self.used_nodes]

    def _get_valid_predecessors_sorted(self, node: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Returns valid predecessors of a node sorted by ascending local density score.

        When density-bias mode is active and there are at least two candidates, predecessors
        are ranked by their density score plus a small random jitter to break ties.
        Returns the unsorted list when density-bias is disabled or fewer than two candidates exist.

        :param node: Node coordinates (row, col).
        :return: List of valid predecessor coordinates ordered from sparsest to densest.
        """
        preds = self._get_valid_predecessors(node)
        if not self._use_density_bias or len(preds) <= 1:
            return preds
        return sorted(preds, key=lambda p: self._density_score(p) + random.uniform(0, 0.5))

    def _try_share_predecessor(self, node: Tuple[int, int]) -> bool:
        """
        Attempts to reuse an already-placed predecessor as the input of the given node.

        Iterates over shuffled architecture predecessors and connects the first eligible
        already-placed node, verifying depth consistency and absence of a cycle before
        adding the edge.

        :param node: Node coordinates (row, col) that needs an incoming connection.
        :return: ``True`` if a shared predecessor was successfully connected; ``False`` otherwise.
        """
        if node not in self.arch_graph:
            return False
        preds = list(self.arch_graph.predecessors(node))
        random.shuffle(preds)
        for p in preds:
            if p in self.used_nodes and self.placement_graph.has_node(p):
                if self.node_depth.get(p) != self.node_depth.get(node, 0) + 1:
                    continue
                if self._fast_path_exists(node, p):
                    continue
                self.placement_graph.add_edge(p, node)
                return True
        return False

    def _add_gate_logic(self, node: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """
        Promotes a node to a logic gate (operation) and wires two predecessor routing nodes to it.

        Requires at least two valid predecessors. Selects two candidates based on the density
        heuristic or at random, labels them as routing nodes, connects them to the gate, and
        updates used-nodes tracking and depth information.

        :param node: Node coordinates (row, col) to be promoted to an operation node.
        :return: List of the two newly placed predecessor coordinates, or ``None`` if fewer
                 than two valid predecessors are available.
        """
        preds = self._get_valid_predecessors_sorted(node)
        if len(preds) < 2:
            return None

        selected = preds[:2] if self._use_density_bias else random.sample(preds, 2)

        self.placement_graph.nodes[node]['type'] = 'operation'
        self.placement_graph.nodes[node]['name'] = f"op_{node}"

        depth = self.node_depth.get(node, 0)
        for p in selected:
            self.placement_graph.add_node(p, type='routing', name=f"rout_{p}")
            self.placement_graph.add_edge(p, node)
            self.used_nodes.add(p)
            self._register_used(p)
            self.node_depth[p] = depth + 1

        return selected

    def _try_crossover(self, node: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Attempts to insert a crossover by repurposing an existing routing predecessor.

        Looks for a placed routing neighbour whose own predecessor slot is free. When found,
        upgrades it to a crossover node, adds the necessary edges, and returns the newly
        placed upstream node.

        :param node: Node coordinates (row, col) for which a crossover path is sought.
        :return: Coordinates of the newly placed upstream node if a crossover was created;
                 ``None`` otherwise.
        """
        if node not in self.arch_graph:
            return None
        preds = list(self.arch_graph.predecessors(node))
        random.shuffle(preds)
        for p in preds:
            if p in self.used_nodes and self.placement_graph.has_node(p):
                if self.placement_graph.nodes[p].get('type') == 'routing':
                    if self._fast_path_exists(node, p):
                        continue
                    dr, dc = p[0] - node[0], p[1] - node[1]
                    p_prev = (p[0] + dr, p[1] + dc)
                    if p_prev in self.arch_graph.predecessors(p) and p_prev not in self.used_nodes:
                        self.placement_graph.nodes[p]['type'] = 'crossover'
                        self.placement_graph.nodes[p]['name'] = f"cross_{p}"
                        self.placement_graph.add_edge(p, node)
                        self.placement_graph.add_node(p_prev, type='routing', name=f"rout_{p_prev}")
                        self.placement_graph.add_edge(p_prev, p)
                        self.used_nodes.add(p_prev)
                        self._register_used(p_prev)
                        self.node_depth[p_prev] = self.node_depth.get(node, 0) + 2
                        return p_prev
        return None

    def _add_wire_logic(self, node: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Extends the circuit by placing a single routing wire predecessor for the given node.

        Selects the best predecessor using an inertia-based heuristic that favours continuing
        in the same direction as the current signal flow, optionally penalised by local density.
        Falls back to a density-sorted or random choice when inertia is not applicable.

        :param node: Node coordinates (row, col) to be extended with a wire predecessor.
        :return: Coordinates of the newly placed routing predecessor, or ``None`` if no
                 valid predecessors are available.
        """
        preds = self._get_valid_predecessors_sorted(node)
        if not preds:
            return None

        if len(preds) > 1 and random.random() < self._inertia_prob:
            children = list(self.placement_graph.successors(node))
            if children:
                child = children[0]
                dr, dc = node[0] - child[0], node[1] - child[1]
                best_p, best_score = None, -9999
                for p in preds:
                    inertia  = (dr * (p[0] - node[0])) + (dc * (p[1] - node[1]))
                    sparsity = -self._density_score(p) * self._density_weight
                    score = inertia + sparsity + random.uniform(-0.1, 0.1)
                    if score > best_score:
                        best_score, best_p = score, p
                selected = best_p
            else:
                selected = preds[0] if self._use_density_bias else random.choice(preds)
        else:
            selected = preds[0] if self._use_density_bias else random.choice(preds)

        self.placement_graph.add_node(selected, type='routing', name=f"rout_{selected}")
        self.placement_graph.add_edge(selected, node)
        self.used_nodes.add(selected)
        self._register_used(selected)
        self.node_depth[selected] = self.node_depth.get(node, 0) + 1
        return selected

    def _finalize_as_input(self, node: Tuple[int, int]) -> bool:
        """
        Marks a border node as a circuit input and assigns it an input label.

        Only border nodes are eligible to become inputs. Updates the node's ``type``
        and ``name`` attributes in the placement graph.

        :param node: Node coordinates (row, col) to be designated as an input.
        :return: ``True`` if the node was successfully labelled as an input;
                 ``False`` if the node is not on the architecture border.
        """
        if node in self.border_nodes:
            self.placement_graph.nodes[node]['type'] = 'input'
            self.placement_graph.nodes[node]['name'] = f"in_{node}"
            return True
        return False

    def _rescue_route_to_border(self, start_node: Tuple[int, int]) -> bool:
        """
        Attempts to connect a dangling node to a free border node via a routed path.

        Performs a breadth-first search backwards through the architecture graph from
        ``start_node``, seeking a reachable unoccupied border node within a path-length
        limit. When a valid border is found, all intermediate nodes are inserted into
        the placement graph as routing or crossover nodes and labelled accordingly.

        :param start_node: Node coordinates (row, col) of the unconnected leaf node
                           that needs to be rescued.
        :return: ``True`` if a route to a border node was successfully established;
                 ``False`` if no viable path was found within the search limit.
        """
        queue = [(start_node, [start_node])]
        visited = {start_node}
        limit = max(self.dim) * 4

        while queue:
            curr, path = queue.pop(0)
            if len(path) > limit:
                continue

            if curr in self.border_nodes and curr not in self.used_nodes:
                for i in range(len(path) - 1):
                    u, v = path[i + 1], path[i]
                    if u in self.used_nodes:
                        self.placement_graph.nodes[u]['type'] = 'crossover'
                        self.placement_graph.nodes[u]['name'] = f"cross_{u}"
                        self.placement_graph.add_edge(u, v)
                    else:
                        ntype = 'input' if u == path[-1] else 'routing'
                        self.placement_graph.add_node(
                            u, type=ntype,
                            name=f"{'in' if ntype == 'input' else 'rout'}_{u}"
                        )
                        self.placement_graph.add_edge(u, v)
                        self.used_nodes.add(u)
                        self._register_used(u)
                    self.node_depth[u] = self.node_depth.get(v, 0) + 1
                return True

            preds = list(self.arch_graph.predecessors(curr))
            random.shuffle(preds)
            for p in preds:
                if p not in visited:
                    if p not in self.used_nodes:
                        if not self._fast_path_exists(start_node, p):
                            visited.add(p)
                            queue.append((p, path + [p]))
                    elif self.placement_graph.nodes.get(p, {}).get('type') == 'routing':
                        dr, dc = p[0] - curr[0], p[1] - curr[1]
                        pp = (p[0] + dr, p[1] + dc)
                        if (pp in self.arch_graph.predecessors(p)
                                and pp not in self.used_nodes
                                and pp not in visited):
                            if not self._fast_path_exists(start_node, p):
                                visited.add(pp)
                                queue.append((pp, path + [p, pp]))
        return False

    def _prune_dead_branches(self) -> None:
        """
        Removes all nodes not reachable from any input and downgrades malformed gate types.

        Performs a forward reachability traversal from all input nodes to identify the
        live portion of the graph, then removes every unreachable node. Afterwards,
        any operation node with fewer than two predecessors is downgraded to a routing
        node, and any crossover node that lacks the required two predecessors or two
        successors is likewise downgraded.
        """
        valid_inputs = {n for n, d in self.placement_graph.nodes(data=True)
                        if d.get('type') == 'input'}
        alive = set(valid_inputs)
        queue = list(valid_inputs)
        while queue:
            curr = queue.pop()
            for s in self.placement_graph.successors(curr):
                if s not in alive:
                    alive.add(s)
                    queue.append(s)

        self.placement_graph.remove_nodes_from(
            [n for n in self.placement_graph.nodes() if n not in alive]
        )

        for n, data in list(self.placement_graph.nodes(data=True)):
            if data.get('type') == 'operation':
                if len(list(self.placement_graph.predecessors(n))) < 2:
                    self.placement_graph.nodes[n]['type'] = 'routing'
            elif data.get('type') == 'crossover':
                if (len(list(self.placement_graph.predecessors(n))) < 2 or
                        len(list(self.placement_graph.successors(n))) < 2):
                    self.placement_graph.nodes[n]['type'] = 'routing'
