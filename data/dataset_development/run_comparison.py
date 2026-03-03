#!/usr/bin/env python3
"""
CLI interface for running multi-model Elo comparisons.

Usage:
    python run_comparison.py --dataset emojis --models haiku-3.5 gpt-4.1-mini --passes 3
    python run_comparison.py --dataset common_words --models all --passes 2 --name word_comparison
    python run_comparison.py --list-datasets
    python run_comparison.py --list-models
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from multi_model_elo import run_multi_model_comparison, MODEL_MAPPINGS
from datasets import get_dataset, list_datasets
from comparison_report import generate_comparison_report

# Default models for convenience
DEFAULT_MODELS = ["haiku-3.5", "gpt-4.1-mini", "kimi-k2", "deepseek-v3"]

def list_available_models():
    """Print available model shortcuts and their full names."""
    print("\nAvailable Models:")
    print("-" * 60)
    print(f"{'Shortcut':<15} {'Full Model Name':<45}")
    print("-" * 60)
    
    # Get unique models (some have duplicate entries)
    seen = set()
    for short, full in MODEL_MAPPINGS.items():
        if full not in seen and "/" not in short:  # Only show shortcuts
            print(f"{short:<15} {full:<45}")
            seen.add(full)
    
    print("\nYou can use either the shortcut or full model name.")
    print("Use 'all' to run all default models.")

def list_available_datasets():
    """Print available datasets with sample items."""
    print("\nAvailable Datasets:")
    print("-" * 60)
    
    for dataset_name in list_datasets():
        dataset = get_dataset(dataset_name)
        sample = dataset[:3] if len(dataset) >= 3 else dataset
        sample_str = ", ".join(str(item) for item in sample)
        if len(dataset) > 3:
            sample_str += ", ..."
        print(f"{dataset_name:<20} ({len(dataset)} items)")
        print(f"  Sample: {sample_str}")
    
    print("\nUse any dataset name with --dataset option.")

def parse_models(models_arg):
    """Parse model argument which can be a list or 'all'."""
    if len(models_arg) == 1 and models_arg[0].lower() == "all":
        return DEFAULT_MODELS
    return models_arg

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run multi-model Elo comparisons on various datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run comparison on emojis with two models
  python run_comparison.py --dataset emojis --models haiku-3.5 gpt-4.1-mini --passes 3
  
  # Run on common words with all default models
  python run_comparison.py --dataset common_words --models all --passes 2
  
  # Custom output name
  python run_comparison.py --dataset abstract_concepts --models kimi-k2 deepseek-v3 --name philosophy_test
  
  # List available options
  python run_comparison.py --list-datasets
  python run_comparison.py --list-models
        """
    )
    
    # Action arguments
    parser.add_argument("--list-datasets", action="store_true",
                       help="List available datasets and exit")
    parser.add_argument("--list-models", action="store_true",
                       help="List available model shortcuts and exit")
    
    # Comparison arguments
    parser.add_argument("--dataset", type=str,
                       help="Name of dataset to use (see --list-datasets)")
    parser.add_argument("--models", nargs="+",
                       help="Model(s) to compare (use 'all' for all defaults)")
    parser.add_argument("--passes", type=int, default=3,
                       help="Number of passes per model (default: 3)")
    parser.add_argument("--name", type=str,
                       help="Custom name for output files (default: auto-generated)")
    parser.add_argument("--verbose", action="store_true",
                       help="Show detailed progress during execution")
    
    args = parser.parse_args()
    
    # Handle list actions
    if args.list_datasets:
        list_available_datasets()
        return
    
    if args.list_models:
        list_available_models()
        return
    
    # Validate required arguments for comparison
    if not args.dataset or not args.models:
        parser.error("--dataset and --models are required for comparison")
    
    # Load dataset
    try:
        dataset = get_dataset(args.dataset)
        print(f"\nLoaded dataset '{args.dataset}' with {len(dataset)} items")
    except ValueError as e:
        print(f"Error: {e}")
        print("Use --list-datasets to see available options")
        return 1
    
    # Parse models
    models = parse_models(args.models)
    
    # Generate output name if not provided
    if args.name:
        output_name = args.name
    else:
        # Auto-generate name from dataset and timestamp
        output_name = f"{args.dataset}_{datetime.now().strftime('%Y%m%d_%H%M')}"
    
    print(f"Output name: {output_name}")
    print(f"Models to compare: {', '.join(models)}")
    print(f"Passes per model: {args.passes}")
    
    # Confirm before starting
    print("\nPress Enter to start comparison (Ctrl+C to cancel)...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    
    # Run comparison
    try:
        results = run_multi_model_comparison(
            dataset=dataset,
            models=models,
            dataset_name=args.dataset,
            passes_per_model=args.passes,
            output_name=output_name,
            verbose=args.verbose
        )
        
        # Generate report
        output_dir = Path(__file__).parent / "comparisons"
        latest_dir = max(output_dir.glob(f"*_{output_name}"))
        report_path = latest_dir / "comparison_report.md"
        
        print("\nGenerating markdown report...")
        generate_comparison_report(results, report_path)
        
        print(f"\n{'='*70}")
        print("✅ Comparison complete!")
        print(f"📁 Results directory: {latest_dir}")
        print(f"📄 Report: {report_path}")
        print(f"📊 Raw data: {latest_dir / 'raw_results.json'}")
        
        # Show summary of top items
        print(f"\n🏆 Top 5 items by weighted average Elo:")
        sorted_items = sorted(
            results["weighted_average_elos"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for i, (item, elo) in enumerate(sorted_items[:5], 1):
            print(f"  {i}. {item}: {elo:.0f}")
        
    except Exception as e:
        print(f"\n❌ Error during comparison: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())