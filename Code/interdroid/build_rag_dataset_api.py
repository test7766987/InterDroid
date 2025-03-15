"""
Build RAG dataset using GME API version
"""

import os
from pathlib import Path
import json
from PIL import Image
import torch
import numpy as np
import base64
import dashscope
import configparser
from http import HTTPStatus
from tqdm import tqdm
import configparser
from generate_app_description import AppDescriptionGenerator

class RAGDatasetBuilder:
    def __init__(self, data_dir: str = None):
        """Initialize RAG dataset builder
        
        Args:
            data_dir: Data directory path, if None, read from config file
        """
        # Read config file
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        # Get data_dir
        self.data_dir = Path(data_dir if data_dir else config['data']['data_dir'])
        
        # Initialize description generator using API key from config file
        self.description_generator = AppDescriptionGenerator(
            llm_api_key=config['llm']['llm_api_key']
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

    def _image_to_base64(self, image_path: str) -> str:
        """Convert image to base64 format
        
        Args:
            image_path: Image path
            
        Returns:
            str: Base64 encoded image data
        """
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        image_format = image_path.split('.')[-1].lower()
        return f"data:image/{image_format};base64,{base64_image}"

    def generate_app_embedding(self, combined_description: str, screenshot_path: str) -> np.ndarray:
        """Generate APP embedding
        
        Args:
            combined_description: Combined description text
            screenshot_path: Screenshot path
            
        Returns:
            np.ndarray: Generated embedding
        """
        # Prepare input data
        image_data = self._image_to_base64(screenshot_path)
        inputs = [
            {
                'text': combined_description,
                'image': image_data
            }
        ]

        dashscope.api_key = "xxx"
        
        # Call GME API
        resp = dashscope.MultiModalEmbedding.call(
            model="multimodal-embedding-v1",
            input=inputs
        )
        
        if resp.status_code == HTTPStatus.OK:
            # Get embedding vector
            embedding = np.array(resp.output['embeddings'][0]['embedding'])
            return embedding
        else:
            raise Exception(f"GME API call failed: {resp.message}")

    def build_dataset(self):
        """Build RAG dataset"""
        # Get all record directories to process
        record_dirs = list(self.data_dir.glob("record_*"))
        
        # Create progress bar using tqdm
        for record_dir in tqdm(record_dirs, desc="Processing records", unit="record"):
            record_id = record_dir.name
            
            # Skip if already processed
            if record_id in self.embedding_cache:
                continue
                
            # Read record.json
            with open(record_dir / "record.json", 'r', encoding='utf-8') as f:
                record_data = json.load(f)
            
            # Get description information
            combined_description = record_data["gpt_app_description"]
            screenshot_path = record_dir / "screenshots" / "step_0.png"
            
            # Generate embedding
            embedding = self.generate_app_embedding(
                combined_description,
                str(screenshot_path)
            )
            
            # Save to cache
            self.embedding_cache[record_id] = embedding
            
            # Save periodically
            self._save_embeddings()

    def find_similar_app(self, test_app_dir: str, activity_info: str) -> str:
        """Find similar APP
        
        Args:
            test_app_dir: Test APP directory path
            activity_info: Activity information of test APP
            
        Returns:
            str: ID of the most similar record directory
        """
        test_dir = Path(test_app_dir)
        screenshot_path = test_dir / "screenshot.png"
        ui_tree_path = test_dir / "ui_tree.xml"
        
        # Generate description
        gpt_description = self.description_generator.generate_app_description(
            str(screenshot_path),
            activity_info,
            str(ui_tree_path)
        )
        
        # Generate embedding for test APP
        query_embedding = self.generate_app_embedding(
            gpt_description, 
            str(screenshot_path)
        )
        
        # Calculate similarity and find the most similar
        max_similarity = -1
        most_similar_id = None
        
        # Add progress bar
        for record_id, embedding in tqdm(self.embedding_cache.items(), desc="Calculating similarity", unit="record"):
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
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
        activity_info="com.example.TestActivity"
    )

    print(f"Found most similar record: {similar_record}") 