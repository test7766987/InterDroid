import os
import json
import logging
import numpy as np
from difflib import SequenceMatcher
import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('exact_match')

def load_sequence(file_path):
    """Load test sequence"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        return []

def calculate_exact_match(test_sequence_path, benchmark_sequence_path):
    """Calculate exact match rate"""
    # Load test sequence and benchmark sequence
    test_sequence = load_sequence(test_sequence_path)
    benchmark_sequence = load_sequence(benchmark_sequence_path)
    
    if not test_sequence or not benchmark_sequence:
        logger.error("Test sequence or benchmark sequence is empty")
        return {
            "exact_matches": 0,
            "total_steps": 0,
            "match_percentage": 0.0,
            "details": {}
        }
    
    # Use longest common subsequence algorithm to calculate matches
    matcher = SequenceMatcher(None, test_sequence, benchmark_sequence)
    matches = matcher.get_matching_blocks()
    
    # Calculate number of exact matching steps
    exact_matches = sum(match.size for match in matches if match.size > 0)
    
    # Calculate match rate
    total_steps = len(benchmark_sequence)
    match_percentage = (exact_matches / total_steps) * 100 if total_steps > 0 else 0.0
    
    # Generate detailed information
    details = {
        "matching_blocks": [
            {
                "test_start": match.a,
                "benchmark_start": match.b,
                "size": match.size
            }
            for match in matches if match.size > 0
        ]
    }
    
    return {
        "exact_matches": exact_matches,
        "total_steps": total_steps,
        "match_percentage": match_percentage,
        "details": details
    }

def find_longest_matching_subsequence(test_sequence, benchmark_sequence):
    """Find longest matching subsequence"""
    # Dynamic programming algorithm to find longest common subsequence
    m = len(test_sequence)
    n = len(benchmark_sequence)
    
    # Create DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Fill DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if test_sequence[i-1] == benchmark_sequence[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    # Backtrack to find the longest common subsequence
    i, j = m, n
    lcs = []
    
    while i > 0 and j > 0:
        if test_sequence[i-1] == benchmark_sequence[j-1]:
            lcs.append({
                "test_index": i-1,
                "benchmark_index": j-1,
                "action": test_sequence[i-1]
            })
            i -= 1
            j -= 1
        elif dp[i-1][j] > dp[i][j-1]:
            i -= 1
        else:
            j -= 1
    
    # Reverse list to get correct order
    lcs.reverse()
    
    return lcs

def calculate_sequence_similarity(test_sequence, benchmark_sequence):
    """Calculate similarity between two sequences using various metrics"""
    if not test_sequence or not benchmark_sequence:
        return {
            "exact_match_percentage": 0.0,
            "jaccard_similarity": 0.0,
            "edit_distance": 0,
            "normalized_edit_distance": 0.0
        }
    
    # Calculate exact match using SequenceMatcher
    matcher = SequenceMatcher(None, test_sequence, benchmark_sequence)
    match_ratio = matcher.ratio()
    
    # Calculate Jaccard similarity (set-based)
    test_set = set(str(item) for item in test_sequence)
    benchmark_set = set(str(item) for item in benchmark_sequence)
    
    intersection = len(test_set.intersection(benchmark_set))
    union = len(test_set.union(benchmark_set))
    jaccard = intersection / union if union > 0 else 0.0
    
    # Calculate Levenshtein edit distance
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    # Convert sequences to strings for edit distance calculation
    test_str = [str(item) for item in test_sequence]
    benchmark_str = [str(item) for item in benchmark_sequence]
    
    edit_distance = levenshtein_distance(test_str, benchmark_str)
    max_len = max(len(test_sequence), len(benchmark_sequence))
    normalized_edit_distance = 1 - (edit_distance / max_len) if max_len > 0 else 0.0
    
    return {
        "exact_match_percentage": match_ratio * 100,
        "jaccard_similarity": jaccard * 100,
        "edit_distance": edit_distance,
        "normalized_edit_distance": normalized_edit_distance * 100
    }

def generate_match_report(test_sequence_path, benchmark_sequence_path, output_path):
    """Generate match report"""
    # Load sequences
    test_sequence = load_sequence(test_sequence_path)
    benchmark_sequence = load_sequence(benchmark_sequence_path)
    
    if not test_sequence or not benchmark_sequence:
        logger.error("Test sequence or benchmark sequence is empty")
        return False
    
    # Calculate match rate
    match_result = calculate_exact_match(test_sequence_path, benchmark_sequence_path)
    
    # Find longest matching subsequence
    lcs = find_longest_matching_subsequence(test_sequence, benchmark_sequence)
    
    # Calculate additional similarity metrics
    similarity_metrics = calculate_sequence_similarity(test_sequence, benchmark_sequence)
    
    # Generate report
    report = {
        "summary": match_result,
        "similarity_metrics": similarity_metrics,
        "longest_common_subsequence": lcs,
        "test_sequence_length": len(test_sequence),
        "benchmark_sequence_length": len(benchmark_sequence),
        "test_sequence_path": os.path.basename(test_sequence_path),
        "benchmark_sequence_path": os.path.basename(benchmark_sequence_path),
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # Save report
    try:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving report to {output_path}: {e}")
        return False

def visualize_sequence_match(test_sequence, benchmark_sequence, output_path=None):
    """Visualize the match between two sequences"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        
        # Find matching blocks
        matcher = SequenceMatcher(None, test_sequence, benchmark_sequence)
        matches = matcher.get_matching_blocks()
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Set up the plot
        ax.set_xlim(0, len(benchmark_sequence))
        ax.set_ylim(0, len(test_sequence))
        ax.set_xlabel('Benchmark Sequence')
        ax.set_ylabel('Test Sequence')
        ax.set_title('Sequence Match Visualization')
        
        # Plot matching blocks
        for match in matches:
            if match.size > 0:
                rect = patches.Rectangle(
                    (match.b, match.a),
                    match.size, match.size,
                    linewidth=1,
                    edgecolor='green',
                    facecolor='lightgreen',
                    alpha=0.5
                )
                ax.add_patch(rect)
        
        # Plot diagonal line for perfect match reference
        max_len = max(len(test_sequence), len(benchmark_sequence))
        ax.plot([0, max_len], [0, max_len], 'r--', alpha=0.3)
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add match percentage text
        match_percentage = sum(match.size for match in matches if match.size > 0) / len(benchmark_sequence) * 100
        ax.text(
            0.05, 0.95,
            f'Match: {match_percentage:.2f}%',
            transform=ax.transAxes,
            fontsize=12,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
        )
        
        # Save or show the plot
        if output_path:
            plt.savefig(output_path)
            logger.info(f"Visualization saved to {output_path}")
        else:
            plt.show()
        
        plt.close()
        return True
        
    except ImportError:
        logger.error("Matplotlib not installed. Cannot generate visualization.")
        return False
    except Exception as e:
        logger.error(f"Error generating visualization: {e}")
        return False

def compare_multiple_sequences(test_sequence_path, benchmark_dir, output_path=None):
    """Compare a test sequence against multiple benchmark sequences"""
    # Load test sequence
    test_sequence = load_sequence(test_sequence_path)
    if not test_sequence:
        logger.error(f"Test sequence {test_sequence_path} is empty or invalid")
        return None
    
    # Find all benchmark sequences in the directory
    benchmark_files = []
    if os.path.isdir(benchmark_dir):
        benchmark_files = [os.path.join(benchmark_dir, f) for f in os.listdir(benchmark_dir) 
                          if f.endswith('.json')]
    else:
        # Assume benchmark_dir is a single file
        if os.path.exists(benchmark_dir) and benchmark_dir.endswith('.json'):
            benchmark_files = [benchmark_dir]
    
    if not benchmark_files:
        logger.error(f"No benchmark sequences found in {benchmark_dir}")
        return None
    
    # Compare with each benchmark
    results = []
    for benchmark_file in benchmark_files:
        benchmark_sequence = load_sequence(benchmark_file)
        if not benchmark_sequence:
            logger.warning(f"Benchmark sequence {benchmark_file} is empty or invalid")
            continue
        
        # Calculate match and similarity
        match_result = calculate_exact_match(test_sequence_path, benchmark_file)
        similarity = calculate_sequence_similarity(test_sequence, benchmark_sequence)
        
        results.append({
            "benchmark_file": os.path.basename(benchmark_file),
            "match_result": match_result,
            "similarity": similarity
        })
    
    # Sort results by match percentage (descending)
    results.sort(key=lambda x: x["match_result"]["match_percentage"], reverse=True)
    
    # Generate report
    report = {
        "test_sequence": os.path.basename(test_sequence_path),
        "test_sequence_length": len(test_sequence),
        "benchmark_count": len(results),
        "results": results,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # Save report if output path is provided
    if output_path:
        try:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Comparison report saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving report to {output_path}: {e}")
    
    return report

if __name__ == "__main__":
    # Test code
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python exact_match.py <test_sequence_path> <benchmark_sequence_path> [output_report_path]")
        print("       python exact_match.py compare <test_sequence_path> <benchmark_dir> [output_report_path]")
        print("       python exact_match.py visualize <test_sequence_path> <benchmark_sequence_path> [output_image_path]")
        sys.exit(1)
    
    if sys.argv[1] == "compare":
        if len(sys.argv) < 4:
            print("Usage: python exact_match.py compare <test_sequence_path> <benchmark_dir> [output_report_path]")
            sys.exit(1)
        
        test_sequence_path = sys.argv[2]
        benchmark_dir = sys.argv[3]
        output_path = sys.argv[4] if len(sys.argv) > 4 else None
        
        report = compare_multiple_sequences(test_sequence_path, benchmark_dir, output_path)
        if report:
            print(f"Compared {report['test_sequence']} against {report['benchmark_count']} benchmark sequences")
            for i, result in enumerate(report['results'][:3]):  # Show top 3
                print(f"  {i+1}. {result['benchmark_file']}: {result['match_result']['match_percentage']:.2f}%")
    
    elif sys.argv[1] == "visualize":
        if len(sys.argv) < 4:
            print("Usage: python exact_match.py visualize <test_sequence_path> <benchmark_sequence_path> [output_image_path]")
            sys.exit(1)
        
        test_sequence_path = sys.argv[2]
        benchmark_sequence_path = sys.argv[3]
        output_path = sys.argv[4] if len(sys.argv) > 4 else None
        
        test_sequence = load_sequence(test_sequence_path)
        benchmark_sequence = load_sequence(benchmark_sequence_path)
        
        if test_sequence and benchmark_sequence:
            visualize_sequence_match(test_sequence, benchmark_sequence, output_path)
            print(f"Visualization {'saved to '+output_path if output_path else 'displayed'}")
        else:
            print("Error: Could not load sequences")
    
    else:
        test_sequence_path = sys.argv[1]
        benchmark_sequence_path = sys.argv[2]
        
        result = calculate_exact_match(test_sequence_path, benchmark_sequence_path)
        print(f"Exact match rate: {result['match_percentage']:.2f}% ({result['exact_matches']}/{result['total_steps']})")
        
        if len(sys.argv) > 3:
            output_path = sys.argv[3]
            if generate_match_report(test_sequence_path, benchmark_sequence_path, output_path):
                print(f"Match report saved to: {output_path}") 