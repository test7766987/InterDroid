import os
import numpy as np
import logging
from PIL import Image
import torch
from torchvision import transforms, models
from sklearn.metrics.pairwise import cosine_similarity
import json
import matplotlib.pyplot as plt
from collections import defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('page_coverage')

class ImageEmbedding:
    """Image embedding class for computing image embedding vectors"""
    
    def __init__(self, model_name='resnet50'):
        """Initialize model"""
        # Use pre-trained ResNet model
        if model_name == 'resnet50':
            self.model = models.resnet50(pretrained=True)
        elif model_name == 'resnet18':
            self.model = models.resnet18(pretrained=True)
        elif model_name == 'vgg16':
            self.model = models.vgg16(pretrained=True).features
        else:
            logger.info(f"Using default ResNet50 model (requested {model_name} not recognized)")
            self.model = models.resnet50(pretrained=True)
            
        # Remove the last fully connected layer, only use feature extraction part
        if model_name.startswith('resnet'):
            self.model = torch.nn.Sequential(*list(self.model.children())[:-1])
        
        self.model.eval()
        
        # Use GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        self.model = self.model.to(self.device)
        
        # Image preprocessing
        self.preprocess = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    
    def get_embedding(self, image_path):
        """Get embedding vector for an image"""
        try:
            # Load image
            image = Image.open(image_path).convert('RGB')
            
            # Preprocess image
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
            
            # Compute embedding vector
            with torch.no_grad():
                embedding = self.model(image_tensor)
                
            # Convert embedding vector to numpy array
            embedding = embedding.squeeze().cpu().numpy()
            
            return embedding
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return None
    
    def get_batch_embeddings(self, image_paths, batch_size=16):
        """Get embeddings for a batch of images"""
        embeddings = {}
        
        # Process images in batches
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i+batch_size]
            batch_tensors = []
            valid_paths = []
            
            # Preprocess each image in the batch
            for path in batch_paths:
                try:
                    image = Image.open(path).convert('RGB')
                    tensor = self.preprocess(image).unsqueeze(0)
                    batch_tensors.append(tensor)
                    valid_paths.append(path)
                except Exception as e:
                    logger.error(f"Error preprocessing image {path}: {e}")
            
            if not batch_tensors:
                continue
                
            # Stack tensors and compute embeddings
            batch_tensor = torch.cat(batch_tensors, 0).to(self.device)
            
            with torch.no_grad():
                batch_embedding = self.model(batch_tensor)
            
            # Store embeddings
            batch_embedding = batch_embedding.cpu().numpy()
            for j, path in enumerate(valid_paths):
                embeddings[path] = batch_embedding[j].squeeze()
        
        return embeddings

def calculate_similarity(embedding1, embedding2):
    """Calculate similarity between two embedding vectors"""
    # Use cosine similarity
    similarity = cosine_similarity(embedding1.reshape(1, -1), embedding2.reshape(1, -1))
    return similarity[0][0]

def load_benchmark_embeddings(benchmark_dir, model_name='resnet50', cache_file=None):
    """Load benchmark embedding vectors"""
    embeddings = {}
    
    # Try to load from cache if available
    if cache_file and os.path.exists(cache_file):
        try:
            logger.info(f"Loading embeddings from cache: {cache_file}")
            with open(cache_file, 'rb') as f:
                import pickle
                cached_data = pickle.load(f)
                if cached_data.get('model_name') == model_name:
                    return cached_data.get('embeddings', {})
                else:
                    logger.info(f"Cache was created with different model ({cached_data.get('model_name')}), recomputing embeddings")
        except Exception as e:
            logger.error(f"Error loading cache file: {e}")
    
    # Initialize embedding model
    embedding_model = ImageEmbedding(model_name)
    
    # Find all images in benchmark directory
    image_paths = []
    for root, _, files in os.walk(benchmark_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(root, file)
                image_paths.append(image_path)
    
    if not image_paths:
        logger.error(f"No images found in benchmark directory: {benchmark_dir}")
        return embeddings
    
    logger.info(f"Computing embeddings for {len(image_paths)} benchmark images")
    
    # Compute embeddings in batches
    embeddings = embedding_model.get_batch_embeddings(image_paths)
    
    # Save to cache if requested
    if cache_file:
        try:
            logger.info(f"Saving embeddings to cache: {cache_file}")
            os.makedirs(os.path.dirname(os.path.abspath(cache_file)), exist_ok=True)
            with open(cache_file, 'wb') as f:
                import pickle
                pickle.dump({
                    'model_name': model_name,
                    'embeddings': embeddings
                }, f)
        except Exception as e:
            logger.error(f"Error saving cache file: {e}")
    
    return embeddings

def calculate_page_coverage(test_dir, benchmark_dir, similarity_threshold=0.8, model_name='resnet50', cache_file=None):
    """Calculate page coverage"""
    # Load benchmark embedding vectors
    benchmark_embeddings = load_benchmark_embeddings(benchmark_dir, model_name, cache_file)
    
    if not benchmark_embeddings:
        logger.error(f"No valid images found in benchmark directory {benchmark_dir}")
        return {
            "covered_pages": 0,
            "total_pages": 0,
            "coverage_percentage": 0.0,
            "details": {}
        }
    
    # Initialize embedding model
    embedding_model = ImageEmbedding(model_name)
    
    # Find all images in test directory
    test_images = []
    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                test_image_path = os.path.join(root, file)
                test_images.append(test_image_path)
    
    if not test_images:
        logger.error(f"No images found in test directory: {test_dir}")
        return {
            "covered_pages": 0,
            "total_pages": 0,
            "coverage_percentage": 0.0,
            "details": {}
        }
    
    logger.info(f"Processing {len(test_images)} test images")
    
    # Compute test image embeddings in batches
    test_embeddings = embedding_model.get_batch_embeddings(test_images)
    
    # Calculate coverage
    covered_pages = set()
    page_matches = {}
    
    for test_path, test_embedding in test_embeddings.items():
        # Calculate similarity with all benchmark images
        best_match = None
        best_similarity = 0.0
        
        for benchmark_path, benchmark_embedding in benchmark_embeddings.items():
            similarity = calculate_similarity(test_embedding, benchmark_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = benchmark_path
        
        # If similarity exceeds threshold, consider the page covered
        if best_similarity >= similarity_threshold:
            covered_pages.add(best_match)
            page_matches[test_path] = {
                "matched_page": best_match,
                "similarity": float(best_similarity)
            }
    
    # Calculate coverage percentage
    total_pages = len(benchmark_embeddings)
    covered_count = len(covered_pages)
    coverage_percentage = (covered_count / total_pages) * 100 if total_pages > 0 else 0.0
    
    # Generate detailed results
    result = {
        "covered_pages": covered_count,
        "total_pages": total_pages,
        "coverage_percentage": coverage_percentage,
        "details": page_matches
    }
    
    return result

def visualize_page_coverage(coverage_result, output_path=None):
    """Visualize page coverage results"""
    try:
        # Extract data for visualization
        covered = coverage_result["covered_pages"]
        total = coverage_result["total_pages"]
        uncovered = total - covered
        
        # Create pie chart
        labels = ['Covered', 'Uncovered']
        sizes = [covered, uncovered]
        colors = ['#4CAF50', '#F44336']
        explode = (0.1, 0)  # explode the 1st slice (Covered)
        
        plt.figure(figsize=(10, 7))
        plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=140)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        
        plt.title(f'Page Coverage: {coverage_result["coverage_percentage"]:.2f}% ({covered}/{total})')
        
        # Add similarity distribution if we have matches
        if coverage_result["details"]:
            similarities = [match["similarity"] for match in coverage_result["details"].values()]
            
            # Create a small subplot for the histogram
            plt.figure(figsize=(10, 6))
            plt.hist(similarities, bins=20, color='#2196F3', alpha=0.7)
            plt.xlabel('Similarity Score')
            plt.ylabel('Count')
            plt.title('Distribution of Similarity Scores')
            plt.grid(alpha=0.3)
            
            # Add vertical line at the threshold
            plt.axvline(x=0.8, color='red', linestyle='--', label='Threshold (0.8)')
            plt.legend()
        
        # Save or display the visualization
        if output_path:
            plt.savefig(output_path)
            logger.info(f"Visualization saved to {output_path}")
        else:
            plt.show()
            
    except Exception as e:
        logger.error(f"Error creating visualization: {e}")

def generate_coverage_report(test_dir, benchmark_dir, output_path, similarity_threshold=0.8, model_name='resnet50'):
    """Generate a comprehensive page coverage report"""
    # Calculate coverage
    coverage_result = calculate_page_coverage(
        test_dir, benchmark_dir, similarity_threshold, model_name,
        cache_file=os.path.join(os.path.dirname(output_path), "embeddings_cache.pkl")
    )
    
    # Group matches by benchmark page
    benchmark_matches = defaultdict(list)
    for test_path, match_info in coverage_result["details"].items():
        benchmark_path = match_info["matched_page"]
        benchmark_matches[benchmark_path].append({
            "test_image": test_path,
            "similarity": match_info["similarity"]
        })
    
    # Find uncovered benchmark pages
    all_benchmark_pages = set()
    for root, _, files in os.walk(benchmark_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                all_benchmark_pages.add(os.path.join(root, file))
    
    covered_pages = set(benchmark_matches.keys())
    uncovered_pages = all_benchmark_pages - covered_pages
    
    # Generate report
    report = {
        "summary": {
            "covered_pages": coverage_result["covered_pages"],
            "total_pages": coverage_result["total_pages"],
            "coverage_percentage": coverage_result["coverage_percentage"],
            "similarity_threshold": similarity_threshold,
            "model_used": model_name
        },
        "covered_benchmark_pages": [
            {
                "benchmark_page": benchmark_path,
                "matches": matches,
                "match_count": len(matches),
                "avg_similarity": sum(m["similarity"] for m in matches) / len(matches)
            }
            for benchmark_path, matches in benchmark_matches.items()
        ],
        "uncovered_benchmark_pages": list(uncovered_pages)
    }
    
    # Save report
    try:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Coverage report saved to {output_path}")
        
        # Generate visualization
        vis_path = os.path.splitext(output_path)[0] + ".png"
        visualize_page_coverage(coverage_result, vis_path)
        
        return True
    except Exception as e:
        logger.error(f"Error saving report: {e}")
        return False

if __name__ == "__main__":
    # Test code
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate page coverage between test and benchmark directories')
    parser.add_argument('test_dir', help='Directory containing test screenshots')
    parser.add_argument('benchmark_dir', help='Directory containing benchmark screenshots')
    parser.add_argument('--threshold', '-t', type=float, default=0.8, help='Similarity threshold (default: 0.8)')
    parser.add_argument('--model', '-m', default='resnet50', choices=['resnet18', 'resnet50', 'vgg16'], 
                        help='Model to use for embeddings (default: resnet50)')
    parser.add_argument('--report', '-r', help='Path to save detailed report')
    parser.add_argument('--visualize', '-v', action='store_true', help='Visualize results')
    
    args = parser.parse_args()
    
    if args.report:
        generate_coverage_report(args.test_dir, args.benchmark_dir, args.report, args.threshold, args.model)
    else:
        result = calculate_page_coverage(args.test_dir, args.benchmark_dir, args.threshold, args.model)
        print(f"Page coverage: {result['coverage_percentage']:.2f}% ({result['covered_pages']}/{result['total_pages']})")
        
        if args.visualize:
            visualize_page_coverage(result) 