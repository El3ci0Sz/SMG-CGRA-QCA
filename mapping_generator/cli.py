import argparse

def create_parser() -> argparse.ArgumentParser:
    """
    Creates and configures the command-line argument parser for the mapping generator.
    """
    parser = argparse.ArgumentParser(
        description="Mapping Generator for CGRA and QCA.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # --- Configurações Gerais ---
    group_general = parser.add_argument_group('General Configurations')
    group_general.add_argument('--tec', type=str, default='cgra', choices=['cgra', 'qca'], help='Target technology.')
    group_general.add_argument('--k-graphs', type=int, default=10, help='Number of graphs to generate.')
    group_general.add_argument('--output-dir', type=str, default='results', help='Base directory to save outputs.')
    group_general.add_argument('--no-images', action='store_true', help='Disable PNG image generation.')
    group_general.add_argument('--visualize', action='store_true', help='Enable generation of physical grid visual files.')
    group_general.add_argument('--export-ml', action='store_true', help='Export decoupled graphs as JSON for ML training.')
    group_general.add_argument('-v', '--verbose', action='store_true', help='Show detailed logs from the generation.')

    # --- Configurações CGRA ---
    group_cgra = parser.add_argument_group('CGRA Specific Configurations')
    group_cgra.add_argument('--gen-mode', type=str, default='grammar', choices=['grammar', 'random'], help='Generation mode (CGRA only).')
    group_cgra.add_argument('--arch-size', type=int, nargs=2, default=[4, 4], help='Architecture dimensions (rows cols).')
    group_cgra.add_argument('--bits', type=str, default='1000', help='CGRA interconnection bits (mdht).')
    group_cgra.add_argument('--graph-range', type=int, nargs=2, default=[8, 10], help='Min and max nodes for the DFG.')
    group_cgra.add_argument('--k-range', type=int, nargs=2, default=[2, 3], help='K-range for grammar rules.')
    group_cgra.add_argument('--max-path-length', type=int, default=15, help='Max path length for routing.')
    group_cgra.add_argument('--ii', type=int, default=None, help='Specify a fixed Initiation Interval (II).')
    group_cgra.add_argument('--no-extend-io', action='store_true', help='Disable I/O extension to border.')
    group_cgra.add_argument('--retries-multiplier', type=int, default=150, help='Multiplier for max attempts (grammar).')
    group_cgra.add_argument('--alpha', type=float, default=0.3, help='Probability of adding extra edges (random mode).')
    
    # Estratégias de Dificuldade (CGRA)
    group_cgra.add_argument('--strategy', type=str, default='systematic', choices=['systematic', 'random'], help='Difficulty strategy (grammar mode).')
    group_cgra.add_argument('--difficulty', type=int, default=1, help='Difficulty level for systematic strategy (1-20).')
    group_cgra.add_argument('--difficulty-range', type=int, nargs=2, metavar=('MIN', 'MAX'), help='Difficulty range for random strategy (e.g., 1 10).')
    group_cgra.add_argument('--flexible-recipe', action='store_true', help='Accept partial recipe fulfillment.')

    # --- Configurações QCA ---
    group_qca = parser.add_argument_group('QCA Specific Configurations')
    group_qca.add_argument('--qca-arch', type=str, default='U', choices=['U', 'R', 'T'], help='QCA architecture type.')
    group_qca.add_argument('--backwards', action='store_true', help='Force Backwards generation strategy (Complex QCA).')
    group_qca.add_argument('--num-gates', type=int, default=10, help='Target number of logic gates (Backwards).')
    group_qca.add_argument('--num-outputs', type=int, default=1, help='Number of output nodes to seed (Backwards).')
    group_qca.add_argument('--no-detailed-stats', action='store_true', help='Disable exact node type counts in JSON.')

    return parser
