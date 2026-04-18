"""
Demo setup for embeddings when OpenAI API key is not available
Creates mock embeddings for testing the vector database setup
"""

import json
import numpy as np
import pickle
import logging
from typing import List, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_demo_embeddings():
    """Create demo embeddings for testing"""
    logger.info("Creating demo embeddings for testing...")
    
    # Load chunks
    try:
        with open("chunked_documents.json", 'r') as f:
            data = json.load(f)
            chunks = data.get('chunks', [])
    except Exception as e:
        logger.error(f"Error loading chunks: {str(e)}")
        return
    
    logger.info(f"Loaded {len(chunks)} chunks")
    
    # Create mock embeddings (1536 dimensions for text-embedding-3-small)
    embedding_dimension = 1536
    embeddings = []
    
    for i, chunk in enumerate(chunks):
        # Create mock embedding with some variation based on chunk content
        np.random.seed(hash(chunk['chunk_id']) % 2**32)  # Reproducible seed
        mock_embedding = np.random.randn(embedding_dimension).astype(np.float32)
        
        embedding_object = {
            "chunk_id": chunk['chunk_id'],
            "embedding": mock_embedding.tolist(),
            "metadata": {
                "scheme_name": chunk['scheme_name'],
                "chunk_type": chunk['chunk_type'],
                "source_url": chunk['source_url'],
                "filename": chunk['filename'],
                "section_title": chunk['section_title'],
                "token_count": chunk['token_count'],
                "last_updated": chunk['last_updated']
            },
            "text_preview": chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text'],
            "generated_at": datetime.now().isoformat(),
            "batch_number": 1,
            "chunk_index": i,
            "is_demo": True
        }
        embeddings.append(embedding_object)
    
    # Save embeddings
    with open("embeddings.pkl", 'wb') as f:
        pickle.dump(embeddings, f)
    
    # Also save as JSON
    with open("embeddings.json", 'w') as f:
        json.dump(embeddings, f, indent=2)
    
    logger.info(f"Created {len(embeddings)} demo embeddings")
    logger.info("Files saved: embeddings.pkl, embeddings.json")
    
    return embeddings

def main():
    """Main function"""
    embeddings = create_demo_embeddings()
    
    # Print statistics
    schemes = set(emb['metadata']['scheme_name'] for emb in embeddings)
    chunk_types = set(emb['metadata']['chunk_type'] for emb in embeddings)
    
    logger.info(f"Demo embeddings created successfully!")
    logger.info(f"Total embeddings: {len(embeddings)}")
    logger.info(f"Schemes covered: {list(schemes)}")
    logger.info(f"Chunk types: {list(chunk_types)}")
    logger.info("Note: These are demo embeddings for testing. Replace with real embeddings using:")
    logger.info("export OPENAI_API_KEY='your-key-here'")
    logger.info("python embedding_pipeline.py")

if __name__ == "__main__":
    main()
