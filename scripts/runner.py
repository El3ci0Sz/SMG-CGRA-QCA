import os
import sys
import argparse
import logging
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from mapping_generator.cli import create_parser
from mapping_generator.generation.controller import GenerationTask
from mapping_generator.utils.logger_setup import setup_logger

def run_single_generation(args: argparse.Namespace) -> None:
    """
    Executes a single generation task based on the provided command-line arguments.

    Args:
        args (argparse.Namespace): The parsed command-line arguments containing the configuration for the generation.

    Returns:
        None
    """
    task_params = _build_task_params_from_args(args)
    
    try:
        task = GenerationTask(**task_params)
        success = task.run()
        
        print("-" * 55)
        if success:
            print("\nGeração concluída com sucesso!")
            if task.generator and task.file_saver:
                print(f"📁 Resultados em: {os.path.abspath(task.file_saver.output_dir)}")
        else:
            print("\nGeração falhou.")
            
    except Exception as e:
        print(f"\nErro durante geração: {e}")
        logging.error(f"Erro na execução single: {e}", exc_info=True)


def _build_task_params_from_args(args: argparse.Namespace) -> dict:
    """
    Extracts and formats generation parameters from the parsed command-line arguments.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.

    Returns:
        dict: A dictionary containing the structured parameters required to initialize a GenerationTask.
    """
    params = {
        'tec': args.tec,
        'gen_mode': args.gen_mode if hasattr(args, 'gen_mode') else 'grammar',
        'k': args.k_graphs,
        'output_dir': args.output_dir,
        'no_images': args.no_images,
        'retries_multiplier': args.retries_multiplier,
        'visualize': args.visualize,
        'export_ml': getattr(args, 'export_ml', False) 
    }
    
    if args.tec == 'cgra':
        params['arch_sizes'] = [tuple(args.arch_size)]
        params['cgra_params'] = {'bits': args.bits}
        params['graph_range'] = tuple(args.graph_range)
        params['k_range'] = tuple(args.k_range)
        params['no_extend_io'] = args.no_extend_io
        params['max_path_length'] = args.max_path_length
        params['ii'] = args.ii
        params['alpha'] = args.alpha
        params['strategy'] = args.strategy
        if args.strategy == 'systematic':
            params['difficulty'] = args.difficulty
        elif args.strategy == 'random':
            if not args.difficulty_range:
                raise ValueError("--difficulty-range obrigatório para --strategy random")
            params['difficulty_range'] = args.difficulty_range
            params['adaptive'] = True
    
    elif args.tec == 'qca':
        params['arch_sizes'] = [tuple(args.arch_size)]
        params['qca_arch'] = args.qca_arch
        
        params['num_gates'] = args.num_gates
        params['num_outputs'] = args.num_outputs
        params['detailed_stats'] = not getattr(args, 'no_detailed_stats', False)
        params['qca_strategy'] = 'backwards' if getattr(args, 'backwards', False) else 'backwards'
        
        if hasattr(args, 'backwards') and args.backwards:
            params['qca_strategy'] = 'backwards'
    
    return params

def main() -> None:
    """
    The main entry point of the script. Parses arguments, configures logging,
    and delegates execution to the appropriate command handler.

    Returns:
        None
    """
    parser = create_parser()
    args = parser.parse_args()
    
    setup_logger(verbose=args.verbose)
    
    run_single_generation(args)


if __name__ == "__main__":
    main()
