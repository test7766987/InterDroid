import os
import json
import logging
import re
import datetime
from collections import defaultdict
from PIL import Image
import cv2
import numpy as np
import imagehash

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('action_coverage')

class ActionSequence:
    """Action sequence class, used to represent and compare action sequences"""
    
    def __init__(self):
        """Initialize action sequence"""
        self.actions = []
    
    def add_action(self, action_type, next_page=None, params=None):
        """Add an action"""
        self.actions.append({
            "type": action_type,
            "next_page": next_page,
            "params": params or {}
        })
    
    def load_from_file(self, file_path):
        """Load action sequence from file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                self.actions = data
            else:
                logger.error(f"File {file_path} has incorrect format, should be a JSON array")
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
    
    def save_to_file(self, file_path):
        """Save action sequence to file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.actions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving to file {file_path}: {e}")
    
    def get_action_types(self):
        """Get all action types"""
        return [action["type"] for action in self.actions]
    
    def get_action_transitions(self):
        """Get all action transitions (action type + next page)"""
        return [(action["type"], action["next_page"]) for action in self.actions]
    
    def filter_by_action_type(self, action_type):
        """Filter actions by type"""
        filtered = ActionSequence()
        filtered.actions = [action for action in self.actions if action["type"] == action_type]
        return filtered
    
    def get_unique_pages(self):
        """Get all unique pages in the sequence"""
        pages = set()
        for action in self.actions:
            if action["next_page"]:
                pages.add(action["next_page"])
        return pages

def calculate_action_coverage(test_sequence_path, benchmark_sequence_path):
    """Calculate action coverage"""
    # Load test sequence and benchmark sequence
    test_sequence = ActionSequence()
    test_sequence.load_from_file(test_sequence_path)
    
    benchmark_sequence = ActionSequence()
    benchmark_sequence.load_from_file(benchmark_sequence_path)
    
    if not test_sequence.actions or not benchmark_sequence.actions:
        logger.error("Test sequence or benchmark sequence is empty")
        return {
            "covered_actions": 0,
            "total_actions": 0,
            "coverage_percentage": 0.0,
            "details": {}
        }
    
    # Get all action transitions in the benchmark sequence
    benchmark_transitions = benchmark_sequence.get_action_transitions()
    unique_benchmark_transitions = set(benchmark_transitions)
    
    # Get all action transitions in the test sequence
    test_transitions = test_sequence.get_action_transitions()
    
    # Calculate covered action transitions
    covered_transitions = set()
    transition_counts = defaultdict(int)
    
    for transition in test_transitions:
        if transition in unique_benchmark_transitions:
            covered_transitions.add(transition)
            transition_counts[transition] += 1
    
    # Calculate coverage
    total_transitions = len(unique_benchmark_transitions)
    covered_count = len(covered_transitions)
    coverage_percentage = (covered_count / total_transitions) * 100 if total_transitions > 0 else 0.0
    
    # Generate detailed information
    details = {
        "covered_transitions": [{"type": t[0], "next_page": t[1], "count": transition_counts[t]} for t in covered_transitions],
        "uncovered_transitions": [{"type": t[0], "next_page": t[1]} for t in unique_benchmark_transitions if t not in covered_transitions]
    }
    
    return {
        "covered_actions": covered_count,
        "total_actions": total_transitions,
        "coverage_percentage": coverage_percentage,
        "details": details
    }

def extract_timestamp_from_filename(filename):
    """Extract timestamp from filename using regex"""
    # Common timestamp patterns in filenames
    patterns = [
        r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})',  # YYYY-MM-DD_HH-MM-SS
        r'(\d{4}\d{2}\d{2}_\d{2}\d{2}\d{2})',      # YYYYMMDD_HHMMSS
        r'(\d{10,13})'                             # Unix timestamp (seconds or milliseconds)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            timestamp_str = match.group(1)
            # Convert to datetime or timestamp based on format
            try:
                if '-' in timestamp_str:
                    dt = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
                    return dt.timestamp()
                elif '_' in timestamp_str and len(timestamp_str) == 15:
                    dt = datetime.datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    return dt.timestamp()
                else:
                    return float(timestamp_str) / (1000 if len(timestamp_str) > 10 else 1)
            except ValueError:
                continue
    
    try:
        return os.path.getctime(filename)
    except:
        return 0

def find_closest_screenshot(screenshots_dir, timestamp, max_time_diff=5):
    """Find the screenshot closest to the given timestamp"""
    if not os.path.exists(screenshots_dir):
        return None
    
    screenshot_files = [f for f in os.listdir(screenshots_dir) 
                       if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not screenshot_files:
        return None
    
    # Convert timestamp to float if it's a string
    if isinstance(timestamp, str):
        try:
            timestamp = float(timestamp)
        except ValueError:
            try:
                dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt.timestamp()
            except ValueError:
                logger.error(f"Could not parse timestamp: {timestamp}")
                return None
    
    closest_file = None
    min_diff = float('inf')
    
    for file in screenshot_files:
        file_path = os.path.join(screenshots_dir, file)
        file_timestamp = extract_timestamp_from_filename(file)
        
        time_diff = abs(file_timestamp - timestamp)
        if time_diff < min_diff and time_diff <= max_time_diff:
            min_diff = time_diff
            closest_file = file_path
    
    return closest_file

def detect_page_from_screenshot(screenshot_path, reference_screenshots=None):
    """Detect page type from screenshot using image comparison or ML techniques"""
    if not os.path.exists(screenshot_path):
        return None
    
    if reference_screenshots and os.path.exists(reference_screenshots):
        target_img = Image.open(screenshot_path)
        target_hash = imagehash.phash(target_img)
        
        # Find the most similar reference screenshot
        best_match = None
        min_diff = float('inf')
        
        ref_files = [f for f in os.listdir(reference_screenshots) 
                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        for ref_file in ref_files:
            ref_path = os.path.join(reference_screenshots, ref_file)
            try:
                ref_img = Image.open(ref_path)
                ref_hash = imagehash.phash(ref_img)
                
                diff = target_hash - ref_hash
                if diff < min_diff:
                    min_diff = diff
                    page_name = os.path.splitext(ref_file)[0]
                    best_match = page_name
            except Exception as e:
                logger.error(f"Error processing reference image {ref_path}: {e}")
        
        # If the difference is small enough, return the matched page
        if min_diff < 10:  # Threshold can be adjusted
            return best_match
    
    try:
        img = cv2.imread(screenshot_path)
        if img is None:
            return None
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        white_pixel_count = np.sum(edges > 0)
        
        if white_pixel_count > 10000:
            return "complex_page"
        else:
            return "simple_page"
    except Exception as e:
        logger.error(f"Error analyzing screenshot {screenshot_path}: {e}")
        return None

def generate_action_sequence(screenshots_dir, actions_log_path, output_path=None, reference_screenshots=None):
    """Generate action sequence based on screenshots and action logs"""
    sequence = ActionSequence()
    
    try:
        with open(actions_log_path, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) < 2:
                    continue
                
                timestamp = parts[0]
                action_type = parts[1]
                
                params = {}
                for param_part in parts[2:]:
                    if '=' in param_part:
                        key, value = param_part.split('=', 1)
                        params[key] = value
                
                next_page = params.get("next_page", None)
                
                if screenshots_dir and os.path.exists(screenshots_dir):
                    screenshot_path = find_closest_screenshot(screenshots_dir, timestamp)
                    
                    if screenshot_path and not next_page:
                        detected_page = detect_page_from_screenshot(screenshot_path, reference_screenshots)
                        if detected_page:
                            next_page = detected_page
                            params["detected_from_screenshot"] = "true"
                            params["screenshot_path"] = os.path.basename(screenshot_path)
                
                sequence.add_action(action_type, next_page, params)
    except Exception as e:
        logger.error(f"Error processing action log {actions_log_path}: {e}")
    
    if output_path:
        sequence.save_to_file(output_path)
    
    return sequence

def compare_action_sequences(sequence1, sequence2):
    """Compare two action sequences and return similarity metrics"""
    transitions1 = set(sequence1.get_action_transitions())
    transitions2 = set(sequence2.get_action_transitions())
    
    # Calculate common transitions
    common_transitions = transitions1.intersection(transitions2)
    
    # Calculate Jaccard similarity
    union_size = len(transitions1.union(transitions2))
    jaccard_similarity = len(common_transitions) / union_size if union_size > 0 else 0.0
    
    # Calculate other metrics
    precision = len(common_transitions) / len(transitions1) if transitions1 else 0.0
    recall = len(common_transitions) / len(transitions2) if transitions2 else 0.0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "jaccard_similarity": jaccard_similarity,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "common_transitions": len(common_transitions),
        "sequence1_transitions": len(transitions1),
        "sequence2_transitions": len(transitions2)
    }

def visualize_action_coverage(coverage_result, output_path=None):
    """Generate a visualization of action coverage"""
    try:
        import matplotlib.pyplot as plt
        import networkx as nx
        
        # Create a directed graph
        G = nx.DiGraph()
        
        # Add nodes and edges for covered transitions
        for transition in coverage_result["details"]["covered_transitions"]:
            action_type = transition["type"]
            next_page = transition["next_page"] or "unknown"
            count = transition["count"]
            
            # Add nodes if they don't exist
            if not G.has_node(action_type):
                G.add_node(action_type, type="action")
            if not G.has_node(next_page):
                G.add_node(next_page, type="page")
            
            # Add edge with weight based on count
            G.add_edge(action_type, next_page, weight=count, covered=True)
        
        # Add nodes and edges for uncovered transitions
        for transition in coverage_result["details"]["uncovered_transitions"]:
            action_type = transition["type"]
            next_page = transition["next_page"] or "unknown"
            
            # Add nodes if they don't exist
            if not G.has_node(action_type):
                G.add_node(action_type, type="action")
            if not G.has_node(next_page):
                G.add_node(next_page, type="page")
            
            # Add edge with weight 0 (uncovered)
            G.add_edge(action_type, next_page, weight=0, covered=False)
        
        # Create the plot
        plt.figure(figsize=(12, 8))
        
        # Use spring layout for node positioning
        pos = nx.spring_layout(G, seed=42)
        
        # Draw nodes with different colors for actions and pages
        action_nodes = [n for n, attr in G.nodes(data=True) if attr.get("type") == "action"]
        page_nodes = [n for n, attr in G.nodes(data=True) if attr.get("type") == "page"]
        
        nx.draw_networkx_nodes(G, pos, nodelist=action_nodes, node_color="lightblue", node_size=500)
        nx.draw_networkx_nodes(G, pos, nodelist=page_nodes, node_color="lightgreen", node_size=500)
        
        # Draw edges with different colors for covered and uncovered
        covered_edges = [(u, v) for u, v, attr in G.edges(data=True) if attr.get("covered")]
        uncovered_edges = [(u, v) for u, v, attr in G.edges(data=True) if not attr.get("covered")]
        
        nx.draw_networkx_edges(G, pos, edgelist=covered_edges, edge_color="green", width=2)
        nx.draw_networkx_edges(G, pos, edgelist=uncovered_edges, edge_color="red", width=1, style="dashed")
        
        # Add labels
        nx.draw_networkx_labels(G, pos)
        
        # Add title with coverage information
        plt.title(f"Action Coverage: {coverage_result['coverage_percentage']:.2f}% ({coverage_result['covered_actions']}/{coverage_result['total_actions']})")
        
        # Remove axis
        plt.axis("off")
        
        # Save or show the plot
        if output_path:
            plt.savefig(output_path)
            logger.info(f"Coverage visualization saved to {output_path}")
        else:
            plt.show()
            
    except ImportError:
        logger.error("Matplotlib or NetworkX not installed. Cannot generate visualization.")
    except Exception as e:
        logger.error(f"Error generating visualization: {e}")

if __name__ == "__main__":
    # Test code
    import sys
    if len(sys.argv) < 3:
        print("Usage: python action_coverage.py <test_sequence_path> <benchmark_sequence_path> [visualization_output]")
        print("       python action_coverage.py generate <screenshots_dir> <actions_log_path> [output_path] [reference_screenshots]")
        print("       python action_coverage.py compare <sequence1_path> <sequence2_path>")
        sys.exit(1)
    
    if sys.argv[1] == "generate":
        if len(sys.argv) < 4:
            print("Usage: python action_coverage.py generate <screenshots_dir> <actions_log_path> [output_path] [reference_screenshots]")
            sys.exit(1)
        
        screenshots_dir = sys.argv[2]
        actions_log_path = sys.argv[3]
        output_path = sys.argv[4] if len(sys.argv) > 4 else None
        reference_screenshots = sys.argv[5] if len(sys.argv) > 5 else None
        
        sequence = generate_action_sequence(screenshots_dir, actions_log_path, output_path, reference_screenshots)
        print(f"Generated action sequence with {len(sequence.actions)} actions")
        if output_path:
            print(f"Saved to {output_path}")
    
    elif sys.argv[1] == "compare":
        if len(sys.argv) < 4:
            print("Usage: python action_coverage.py compare <sequence1_path> <sequence2_path>")
            sys.exit(1)
        
        sequence1_path = sys.argv[2]
        sequence2_path = sys.argv[3]
        
        sequence1 = ActionSequence()
        sequence1.load_from_file(sequence1_path)
        
        sequence2 = ActionSequence()
        sequence2.load_from_file(sequence2_path)
        
        result = compare_action_sequences(sequence1, sequence2)
        print(f"Comparison results:")
        print(f"  Jaccard similarity: {result['jaccard_similarity']:.4f}")
        print(f"  Precision: {result['precision']:.4f}")
        print(f"  Recall: {result['recall']:.4f}")
        print(f"  F1 score: {result['f1_score']:.4f}")
        print(f"  Common transitions: {result['common_transitions']}")
        print(f"  Sequence 1 transitions: {result['sequence1_transitions']}")
        print(f"  Sequence 2 transitions: {result['sequence2_transitions']}")
    
    else:
        test_sequence_path = sys.argv[1]
        benchmark_sequence_path = sys.argv[2]
        visualization_output = sys.argv[3] if len(sys.argv) > 3 else None
        
        result = calculate_action_coverage(test_sequence_path, benchmark_sequence_path)
        print(f"Action coverage: {result['coverage_percentage']:.2f}% ({result['covered_actions']}/{result['total_actions']})")
        
        if visualization_output:
            visualize_action_coverage(result, visualization_output) 