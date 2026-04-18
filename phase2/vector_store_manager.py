"""
Vector Store Manager for Phase 2
Manages FAISS vector database for semantic search
"""

import faiss
import json
import numpy as np
import pickle
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Manages FAISS vector index for semantic search"""
    
    def __init__(self, index_path: str = "faiss_index.bin", 
                 metadata_path: str = "metadata_store.json"):
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.index = None
        self.metadata_store = {}
        self.embedding_dimension = 384  # for BGE-small-en-v1.5
        
    def create_index_from_embeddings(self, embeddings: List[Dict]) -> bool:
        """Create new FAISS index from embeddings"""
        try:
            # Filter successful embeddings
            successful_embeddings = [e for e in embeddings if e.get('embedding')]
            
            if not successful_embeddings:
                logger.error("No valid embeddings found")
                return False
            
            logger.info(f"Creating index from {len(successful_embeddings)} embeddings")
            
            # Determine embedding dimension
            dimension = len(successful_embeddings[0]['embedding'])
            self.embedding_dimension = dimension
            
            # Create FAISS index
            self.index = faiss.IndexFlatL2(dimension)
            
            # Convert embeddings to numpy array
            embedding_matrix = np.array([emb['embedding'] for emb in successful_embeddings], dtype=np.float32)
            
            # Add embeddings to index
            self.index.add(embedding_matrix)
            
            # Create metadata store
            self.metadata_store = {
                i: {
                    'chunk_id': emb['chunk_id'],
                    'scheme_name': emb['metadata']['scheme_name'],
                    'chunk_type': emb['metadata']['chunk_type'],
                    'source_url': emb['metadata']['source_url'],
                    'filename': emb['metadata']['filename'],
                    'section_title': emb['metadata']['section_title'],
                    'text_preview': emb['text_preview'],
                    'token_count': emb['metadata']['token_count'],
                    'last_updated': emb['metadata']['last_updated']
                }
                for i, emb in enumerate(successful_embeddings)
            }
            
            logger.info(f"Successfully created index with {self.index.ntotal} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            return False
    
    def load_existing_index(self) -> bool:
        """Load existing FAISS index and metadata"""
        try:
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                logger.info(f"Loaded existing index with {self.index.ntotal} vectors")
            else:
                logger.info("No existing index found")
                return False
            
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r') as f:
                    self.metadata_store = json.load(f)
                logger.info(f"Loaded metadata for {len(self.metadata_store)} chunks")
            else:
                logger.warning("No metadata file found")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading existing index: {str(e)}")
            return False
    
    def save_index(self) -> bool:
        """Save FAISS index and metadata to files"""
        try:
            if self.index is None:
                logger.error("No index to save")
                return False
            
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save metadata
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata_store, f, indent=2)
            
            logger.info(f"Saved index with {self.index.ntotal} vectors to {self.index_path}")
            logger.info(f"Saved metadata for {len(self.metadata_store)} chunks to {self.metadata_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            return False
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        """Search for similar vectors"""
        try:
            if self.index is None:
                logger.error("No index loaded for search")
                return []
            
            # Ensure query embedding is correct format
            if len(query_embedding.shape) == 1:
                query_embedding = query_embedding.reshape(1, -1)
            
            # Search FAISS index
            distances, indices = self.index.search(query_embedding, k)
            
            # Prepare results
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx >= 0 and idx < len(self.metadata_store):
                    result = {
                        'rank': i + 1,
                        'chunk_id': self.metadata_store[idx]['chunk_id'],
                        'metadata': self.metadata_store[idx],
                        'distance': float(distance),
                        'similarity_score': 1 / (1 + float(distance))  # Convert to similarity
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return []
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector index"""
        if self.index is None:
            return {'status': 'no_index'}
        
        stats = {
            'total_vectors': self.index.ntotal,
            'embedding_dimension': self.embedding_dimension,
            'index_type': 'IndexFlatL2',
            'metadata_count': len(self.metadata_store),
            'created_at': datetime.now().isoformat()
        }
        
        # Calculate scheme distribution
        schemes = [meta['scheme_name'] for meta in self.metadata_store.values()]
        stats['scheme_distribution'] = {
            scheme: schemes.count(scheme) for scheme in set(schemes)
        }
        
        # Calculate chunk type distribution
        chunk_types = [meta['chunk_type'] for meta in self.metadata_store.values()]
        stats['chunk_type_distribution'] = {
            chunk_type: chunk_types.count(chunk_type) for chunk_type in set(chunk_types)
        }
        
        return stats
    
    def validate_index(self) -> Dict[str, Any]:
        """Validate index integrity"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': self.get_index_stats()
        }
        
        # Check if index exists
        if self.index is None:
            validation_result['errors'].append("No index loaded")
            validation_result['valid'] = False
            return validation_result
        
        # Check vector count consistency
        vector_count = self.index.ntotal
        metadata_count = len(self.metadata_store)
        
        if vector_count != metadata_count:
            validation_result['errors'].append(
                f"Vector count ({vector_count}) doesn't match metadata count ({metadata_count})"
            )
            validation_result['valid'] = False
        
        # Check metadata completeness
        required_fields = ['chunk_id', 'scheme_name', 'chunk_type', 'source_url']
        for idx, metadata in self.metadata_store.items():
            for field in required_fields:
                if field not in metadata or not metadata[field]:
                    validation_result['warnings'].append(
                        f"Missing field '{field}' in metadata for index {idx}"
                    )
        
        return validation_result
    
    def update_index(self, new_embeddings: List[Dict]) -> bool:
        """Add new embeddings to existing index"""
        try:
            # Filter successful embeddings
            successful_embeddings = [e for e in new_embeddings if e.get('embedding')]
            
            if not successful_embeddings:
                logger.error("No valid embeddings to add")
                return False
            
            if self.index is None:
                logger.info("No existing index, creating new one")
                return self.create_index_from_embeddings(new_embeddings)
            
            logger.info(f"Adding {len(successful_embeddings)} new embeddings to existing index")
            
            # Convert embeddings to numpy array
            embedding_matrix = np.array([emb['embedding'] for emb in successful_embeddings], dtype=np.float32)
            
            # Add to existing index
            start_idx = self.index.ntotal
            self.index.add(embedding_matrix)
            
            # Update metadata store
            for i, emb in enumerate(successful_embeddings):
                metadata_idx = start_idx + i
                self.metadata_store[metadata_idx] = {
                    'chunk_id': emb['chunk_id'],
                    'scheme_name': emb['metadata']['scheme_name'],
                    'chunk_type': emb['metadata']['chunk_type'],
                    'source_url': emb['metadata']['source_url'],
                    'filename': emb['metadata']['filename'],
                    'section_title': emb['metadata']['section_title'],
                    'text_preview': emb['text_preview'],
                    'token_count': emb['metadata']['token_count'],
                    'last_updated': emb['metadata']['last_updated']
                }
            
            logger.info(f"Successfully added embeddings. Index now has {self.index.ntotal} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Error updating index: {str(e)}")
            return False

def main():
    """Main function to set up vector store"""
    logger.info("Setting up vector store...")
    
    # Initialize manager
    manager = VectorStoreManager()
    
    # Try to load existing index
    if not manager.load_existing_index():
        logger.info("Creating new index from embeddings...")
        
        # Load embeddings
        try:
            with open("embeddings.pkl", 'rb') as f:
                embeddings = pickle.load(f)
            logger.info(f"Loaded {len(embeddings)} embeddings")
        except FileNotFoundError:
            logger.error("No embeddings found. Run embedding_pipeline.py first.")
            return
        
        # Create new index
        if manager.create_index_from_embeddings(embeddings):
            # Save index
            if manager.save_index():
                logger.info("Vector store setup completed successfully!")
            else:
                logger.error("Failed to save index")
        else:
            logger.error("Failed to create index")
    else:
        logger.info("Existing index loaded successfully")
    
    # Validate index
    validation_result = manager.validate_index()
    if validation_result['valid']:
        logger.info("Index validation passed")
        stats = validation_result['stats']
        logger.info(f"Total vectors: {stats['total_vectors']}")
        logger.info(f"Schemes covered: {list(stats['scheme_distribution'].keys())}")
    else:
        logger.error("Index validation failed:")
        for error in validation_result['errors']:
            logger.error(f"  - {error}")

if __name__ == "__main__":
    main()
