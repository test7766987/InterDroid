import os
from pathlib import Path
import json
from PIL import Image
import torch
from gme_inference import GmeQwen2VL
from llm_api import SiliconFlowAPI
import numpy as np
from generate_app_description import AppDescriptionGenerator

class RAGDatasetBuilder:
    def __init__(self, data_dir: str):
        """Initialize RAG dataset builder
        
        Args:
            data_dir: Data directory path
        """
        self.data_dir = Path(data_dir)
        self.gme_model = GmeQwen2VL("./gme-Qwen2-VL-2B-Instruct")
        self.description_generator = AppDescriptionGenerator(
            llm_api_key="xxx"
        )
        
        # Create embeddings storage directory
        self.embeddings_dir = self.data_dir / "embeddings"
        self.embeddings_dir.mkdir(exist_ok=True)
        
        # Load existing embeddings
        self.embedding_cache = {}
        self._load_existing_embeddings()

    def _load_existing_embeddings(self):
        """Load existing embeddings"""
        if (self.embeddings_dir / "embeddings.npz").exists():
            data = np.load(self.embeddings_dir / "embeddings.npz", allow_pickle=True)
            self.embedding_cache = {
                record_id: embedding for record_id, embedding in 
                zip(data["record_ids"], data["embeddings"])
            }

    def _save_embeddings(self):
        """Save embeddings to file"""
        record_ids = list(self.embedding_cache.keys())
        embeddings = [self.embedding_cache[rid] for rid in record_ids]
        np.savez(
            self.embeddings_dir / "embeddings.npz",
            record_ids=record_ids,
            embeddings=embeddings
        )

    def generate_app_embedding(self, combined_description: str, screenshot_path: str) -> torch.Tensor:
        """Generate APP embedding
        
        Args:
            combined_description: Combined description text
            screenshot_path: Screenshot path
            
        Returns:
            torch.Tensor: Generated embedding
        """
        image = Image.open(screenshot_path)
        embedding = self.gme_model.get_fused_embeddings(
            texts=[combined_description],
            images=[image]
        )
        # embedding.shape: torch.Size([1, 1536])
        return embedding[0]

    def build_dataset(self):
        """Build RAG dataset"""
        for record_dir in self.data_dir.glob("record_*"):
            record_id = record_dir.name
            
            # Skip if already processed
            if record_id in self.embedding_cache:
                continue
                
            # Read record.json
            with open(record_dir / "record.json", 'r', encoding='utf-8') as f:
                record_data = json.load(f)
            
            # Get descriptions from record.json
            combined_description = record_data["app_combined_description"]
            screenshot_path = record_dir / "screenshots" / "step_0.png"
            
            # Generate embedding
            embedding = self.generate_app_embedding(
                combined_description,
                str(screenshot_path)
            )
            
            # Save to cache
            self.embedding_cache[record_id] = embedding.cpu().numpy()
            
            # Periodically save
            self._save_embeddings()

    def find_similar_app(self, test_app_dir: str, activity_info: str) -> str:
        """Find similar APP
        
        Args:
            test_app_dir: Path to test APP directory
            activity_info: Activity information of the test APP
            
        Returns:
            str: ID of the most similar record directory
        """
        test_dir = Path(test_app_dir)
        screenshot_path = test_dir / "screenshot.png"
        ui_tree_path = test_dir / "ui_tree.xml"
        
        # Generate descriptions
        gpt_description = self.description_generator.generate_app_description(
            str(screenshot_path),
            activity_info
        )
        combined_description = self.description_generator.generate_combined_description(
            gpt_description,
            str(ui_tree_path)
        )
        
        # Generate embedding for test APP
        query_embedding = self.generate_app_embedding(
            combined_description, 
            str(screenshot_path)
        )
        
        # Calculate similarity and find the most similar
        max_similarity = -1
        most_similar_id = None
        
        for record_id, embedding in self.embedding_cache.items():
            similarity = torch.cosine_similarity(
                query_embedding,
                torch.from_numpy(embedding),
                dim=0
            )
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_id = record_id
                
        return most_similar_id

if __name__ == "__main__":
    # Example usage
    builder = RAGDatasetBuilder(
        data_dir="real_data"
    )
    
    # Build dataset
    builder.build_dataset()
    
    # Test finding similar APP
    similar_record = builder.find_similar_app(
        test_app_dir="test_app",
        activity_info="com.example.TestActivity"  # Provide actual activity information
    )
    print(f"similar record: {similar_record}")