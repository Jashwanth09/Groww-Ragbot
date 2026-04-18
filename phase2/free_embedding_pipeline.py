"""
Free Embedding Generation Pipeline using BGE-small-en-v1.5
Generates high-quality embeddings without API costs
"""

import json
import pickle
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FreeEmbeddingGenerator:
    """Generates embeddings using BGE model - completely free"""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self.embedding_dimension = 384  # BGE-small dimensions
        
        logger.info(f"Loading BGE model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Successfully loaded {model_name}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def load_chunks(self, chunks_file: str = "chunked_documents.json") -> List[Dict]:
        """Load chunked documents"""
        try:
            with open(chunks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                chunks = data.get('chunks', [])
                logger.info(f"Loaded {len(chunks)} chunks from {chunks_file}")
                return chunks
        except Exception as e:
            logger.error(f"Error loading chunks: {str(e)}")
            return []
    
    def generate_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """Generate embeddings for all chunks using BGE"""
        if not chunks:
            logger.error("No chunks provided for embedding generation")
            return []
        
        embeddings = []
        batch_size = 32  # Optimal for BGE
        
        logger.info(f"Generating BGE embeddings for {len(chunks)} chunks...")
        
        # Extract texts
        texts = [chunk['text'] for chunk in chunks]
        
        # Generate embeddings in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_chunks = chunks[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"Processing batch {batch_num}/{(len(texts) + batch_size - 1) // batch_size}")
            
            try:
                # Generate embeddings
                batch_embeddings = self.model.encode(
                    batch_texts,
                    batch_size=batch_size,
                    normalize_embeddings=True  # Important for BGE
                )
                
                # Create embedding objects
                for j, (chunk, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
                    embedding_object = {
                        "chunk_id": chunk['chunk_id'],
                        "embedding": embedding.tolist(),
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
                        "batch_number": batch_num,
                        "chunk_index": j,
                        "model_name": self.model_name,
                        "embedding_dimension": self.embedding_dimension
                    }
                    embeddings.append(embedding_object)
                
            except Exception as e:
                logger.error(f"Failed to process batch {batch_num}: {str(e)}")
                # Add placeholder for failed batch
                for chunk in batch_chunks:
                    embeddings.append({
                        "chunk_id": chunk.get("chunk_id", "unknown"),
                        "error": str(e),
                        "embedding": None
                    })
        
        successful_embeddings = [e for e in embeddings if e.get('embedding')]
        logger.info(f"Generated {len(successful_embeddings)} successful BGE embeddings")
        return embeddings
    
    def save_embeddings(self, embeddings: List[Dict], output_file: str = "embeddings_bge.pkl"):
        """Save embeddings to file"""
        # Filter out failed embeddings
        successful_embeddings = [e for e in embeddings if e.get('embedding')]
        
        # Save as pickle
        output_path = Path(output_file)
        with open(output_path, 'wb') as f:
            pickle.dump(successful_embeddings, f)
        
        # Also save as JSON for inspection
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(successful_embeddings, f, indent=2)
        
        logger.info(f"Saved {len(successful_embeddings)} BGE embeddings to {output_path}")
        logger.info(f"Also saved JSON version to {json_path}")
        
        return str(output_path)
    
    def get_embedding_stats(self, embeddings: List[Dict]) -> Dict[str, Any]:
        """Calculate embedding statistics"""
        if not embeddings:
            return {'total_embeddings': 0}
        
        successful_embeddings = [e for e in embeddings if e.get('embedding')]
        
        return {
            'total_embeddings': len(successful_embeddings),
            'failed_embeddings': len(embeddings) - len(successful_embeddings),
            'embedding_dimension': len(successful_embeddings[0]['embedding']) if successful_embeddings else 0,
            'model_used': self.model_name,
            'generation_date': successful_embeddings[0]['generated_at'] if successful_embeddings else None,
            'schemes_covered': list(set(emb['metadata']['scheme_name'] for emb in successful_embeddings)),
            'chunk_types': list(set(emb['metadata']['chunk_type'] for emb in successful_embeddings))
        }
    
    def validate_embeddings(self, embeddings: List[Dict]) -> Dict[str, Any]:
        """Validate embedding quality"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': self.get_embedding_stats(embeddings)
        }
        
        # Check embedding dimensions
        if embeddings:
            successful_embeddings = [e for e in embeddings if e.get('embedding')]
            if successful_embeddings:
                expected_dim = len(successful_embeddings[0]['embedding'])
                for i, emb in enumerate(successful_embeddings):
                    if len(emb['embedding']) != expected_dim:
                        validation_result['errors'].append(f"Embedding {i}: Incorrect dimension {len(emb['embedding'])}, expected {expected_dim}")
        
        # Check for missing embeddings
        failed_count = len([e for e in embeddings if not e.get('embedding')])
        if failed_count > 0:
            validation_result['warnings'].append(f"{failed_count} embeddings failed to generate")
        
        validation_result['valid'] = len(validation_result['errors']) == 0
        return validation_result

def main():
    """Main function to run free embedding pipeline"""
    logger.info("Starting BGE embedding generation pipeline...")
    
    # Initialize generator
    generator = FreeEmbeddingGenerator()
    
    # Load chunks
    chunks = generator.load_chunks()
    if not chunks:
        logger.error("No chunks found. Run chunking_pipeline.py first.")
        return
    
    # Generate embeddings
    embeddings = generator.generate_embeddings(chunks)
    
    # Validate embeddings
    validation_result = generator.validate_embeddings(embeddings)
    
    if validation_result['errors']:
        logger.error("Validation errors found:")
        for error in validation_result['errors']:
            logger.error(f"  - {error}")
        return
    
    if validation_result['warnings']:
        logger.warning("Validation warnings:")
        for warning in validation_result['warnings']:
            logger.warning(f"  - {warning}")
    
    # Print statistics
    stats = validation_result['stats']
    logger.info(f"BGE embedding generation completed!")
    logger.info(f"Total embeddings: {stats['total_embeddings']}")
    logger.info(f"Failed embeddings: {stats['failed_embeddings']}")
    logger.info(f"Embedding dimension: {stats['embedding_dimension']}")
    logger.info(f"Model used: {stats['model_used']}")
    logger.info(f"Schemes covered: {stats['schemes_covered']}")
    
    # Save embeddings
    output_file = generator.save_embeddings(embeddings)
    logger.info(f"BGE embeddings saved to: {output_file}")

if __name__ == "__main__":
    main()
