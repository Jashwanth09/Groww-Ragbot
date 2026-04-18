"""
Embedding Generation Pipeline for Phase 2
Generates OpenAI embeddings for chunked documents
"""

import json
import openai
import pickle
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import time
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generates embeddings for fund data chunks using OpenAI"""
    
    def __init__(self, api_key: str = None, model: str = "text-embedding-3-small"):
        self.model = model
        self.embedding_dimension = 1536  # for text-embedding-3-small
        
        # Set API key
        if api_key:
            openai.api_key = api_key
        elif os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
        else:
            logger.warning("No OpenAI API key found. Set OPENAI_API_KEY environment variable.")
        
        logger.info(f"Initialized embedding generator with model: {model}")
    
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
        """Generate embeddings for all chunks"""
        if not chunks:
            logger.error("No chunks provided for embedding generation")
            return []
        
        embeddings = []
        batch_size = 100  # API limit
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"Processing batch {batch_num}/{(len(chunks) + batch_size - 1) // batch_size}")
            
            try:
                batch_embeddings = self._process_batch(batch, batch_num)
                embeddings.extend(batch_embeddings)
                
                # Rate limiting
                if i + batch_size < len(chunks):
                    time.sleep(1)  # 1 second between batches
                    
            except Exception as e:
                logger.error(f"Failed to process batch {batch_num}: {str(e)}")
                # Add placeholder for failed batch
                for chunk in batch:
                    embeddings.append({
                        "chunk_id": chunk.get("chunk_id", "unknown"),
                        "error": str(e),
                        "embedding": None
                    })
        
        logger.info(f"Generated {len(e for e in embeddings if e.get('embedding'))} successful embeddings")
        return embeddings
    
    def _process_batch(self, batch: List[Dict], batch_num: int) -> List[Dict]:
        """Process a single batch of chunks"""
        texts = [chunk['text'] for chunk in batch]
        
        try:
            response = openai.embeddings.create(
                input=texts,
                model=self.model
            )
            
            batch_embeddings = []
            for i, (chunk, embedding_data) in enumerate(zip(batch, response.data)):
                embedding_object = {
                    "chunk_id": chunk['chunk_id'],
                    "embedding": embedding_data.embedding,
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
                    "chunk_index": i
                }
                batch_embeddings.append(embedding_object)
            
            return batch_embeddings
            
        except Exception as e:
            logger.error(f"OpenAI API error in batch {batch_num}: {str(e)}")
            raise
    
    def save_embeddings(self, embeddings: List[Dict], output_file: str = "scripts/embeddings.pkl"):
        """Save embeddings to file"""
        # Filter out failed embeddings
        successful_embeddings = [e for e in embeddings if e.get('embedding')]
        
        # Save as pickle
        output_path = Path(output_file)
        with open(output_path, 'wb') as f:
            pickle.dump(successful_embeddings, f)
        
        # Also save as JSON for inspection
        json_path = output_path.with_suffix('.json')
        # Convert numpy arrays to lists for JSON serialization
        json_embeddings = []
        for emb in successful_embeddings:
            json_emb = emb.copy()
            if 'embedding' in json_emb:
                json_emb['embedding'] = list(json_emb['embedding'])
            json_embeddings.append(json_emb)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_embeddings, f, indent=2)
        
        logger.info(f"Saved {len(successful_embeddings)} embeddings to {output_path}")
        logger.info(f"Also saved JSON version to {json_path}")
        
        return str(output_path)
    
    def load_embeddings(self, file_path: str) -> List[Dict]:
        """Load embeddings from file"""
        try:
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading embeddings: {str(e)}")
            return []
    
    def get_embedding_stats(self, embeddings: List[Dict]) -> Dict[str, Any]:
        """Calculate embedding statistics"""
        if not embeddings:
            return {'total_embeddings': 0}
        
        successful_embeddings = [e for e in embeddings if e.get('embedding')]
        
        return {
            'total_embeddings': len(successful_embeddings),
            'failed_embeddings': len(embeddings) - len(successful_embeddings),
            'embedding_dimension': len(successful_embeddings[0]['embedding']) if successful_embeddings else 0,
            'model_used': self.model,
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
    """Main function to run embedding pipeline"""
    logger.info("Starting embedding generation pipeline...")
    
    # Initialize generator
    generator = EmbeddingGenerator()
    
    # Load chunks
    chunks = generator.load_chunks()
    if not chunks:
        logger.error("No chunks found. Run chunking_pipeline.py first.")
        return
    
    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        logger.error("OPENAI_API_KEY environment variable not set")
        logger.info("Set it with: export OPENAI_API_KEY='your-key-here'")
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
    logger.info(f"Embedding generation completed!")
    logger.info(f"Total embeddings: {stats['total_embeddings']}")
    logger.info(f"Failed embeddings: {stats['failed_embeddings']}")
    logger.info(f"Embedding dimension: {stats['embedding_dimension']}")
    logger.info(f"Schemes covered: {stats['schemes_covered']}")
    
    # Save embeddings
    output_file = generator.save_embeddings(embeddings)
    logger.info(f"Embeddings saved to: {output_file}")

if __name__ == "__main__":
    main()
