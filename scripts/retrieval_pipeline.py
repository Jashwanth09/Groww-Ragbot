"""
Retrieval Pipeline for Phase 2.3
Implements semantic search with BGE embeddings and FAISS
"""

import json
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from vector_store_manager import VectorStoreManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RetrievalPipeline:
    """Handles semantic search and retrieval for mutual fund FAQ system"""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self.embedding_model = SentenceTransformer(model_name)
        self.vector_manager = VectorStoreManager()
        
        # Load existing index and metadata
        if not self.vector_manager.load_existing_index():
            logger.error("Failed to load FAISS index. Run vector_store_manager.py first.")
            raise ValueError("No vector index found")
        
        logger.info(f"Retrieval pipeline initialized with {self.vector_manager.index.ntotal} vectors")
    
    def generate_query_embedding(self, query: str) -> np.ndarray:
        """Generate BGE embedding for user query"""
        try:
            # Generate embedding with normalization (important for BGE)
            embedding = self.embedding_model.encode(
                query,
                normalize_embeddings=True  # Important for BGE
            )
            return embedding
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise
    
    def process_query(self, query: str, k: int = 5) -> List[Dict]:
        """Process user query and return relevant chunks"""
        try:
            # 1. Generate query embedding
            query_embedding = self.generate_query_embedding(query)
            
            # 2. Search FAISS index
            results = self.vector_manager.search(query_embedding, k)
            
            # 3. Enhance results with additional metadata
            enhanced_results = []
            for result in results:
                enhanced_result = {
                    "rank": result["rank"],
                    "chunk_id": result["chunk_id"],
                    "text": result["metadata"].get("text_preview", "Text not found"),
                    "metadata": result["metadata"],
                    "distance": result["distance"],
                    "similarity_score": result["similarity_score"],
                    "relevance": self._calculate_relevance(result["similarity_score"])
                }
                enhanced_results.append(enhanced_result)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return []
    
    def _get_chunk_text(self, chunk_id: str) -> str:
        """Get full text for chunk from chunked_documents.json"""
        try:
            with open("chunked_documents.json", 'r') as f:
                data = json.load(f)
                chunks = data.get('chunks', [])
                
                for chunk in chunks:
                    if chunk['chunk_id'] == chunk_id:
                        return chunk['text']
                
                logger.warning(f"Chunk {chunk_id} not found in chunked_documents.json")
                return "Text not found"
                
        except Exception as e:
            logger.error(f"Error getting chunk text: {str(e)}")
            return "Error retrieving text"
    
    def _calculate_relevance(self, similarity_score: float) -> str:
        """Calculate relevance level based on similarity score"""
        if similarity_score >= 0.8:
            return "high"
        elif similarity_score >= 0.6:
            return "medium"
        elif similarity_score >= 0.4:
            return "low"
        else:
            return "very_low"
    
    def filter_results(self, results: List[Dict], min_similarity: float = 0.4) -> List[Dict]:
        """Filter results by minimum similarity threshold"""
        return [r for r in results if r["similarity_score"] >= min_similarity]
    
    def get_diverse_results(self, results: List[Dict], max_per_scheme: int = 2) -> List[Dict]:
        """Ensure diversity of schemes in results"""
        scheme_counts = {}
        diverse_results = []
        
        for result in results:
            scheme = result["metadata"]["scheme_name"]
            
            if scheme not in scheme_counts or scheme_counts[scheme] < max_per_scheme:
                diverse_results.append(result)
                scheme_counts[scheme] = scheme_counts.get(scheme, 0) + 1
        
        return diverse_results
    
    def get_retrieval_stats(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate retrieval statistics"""
        if not results:
            return {"total_results": 0}
        
        schemes = [r["metadata"]["scheme_name"] for r in results]
        chunk_types = [r["metadata"]["chunk_type"] for r in results]
        similarities = [r["similarity_score"] for r in results]
        
        return {
            "total_results": len(results),
            "avg_similarity": sum(similarities) / len(similarities),
            "max_similarity": max(similarities),
            "min_similarity": min(similarities),
            "schemes_covered": list(set(schemes)),
            "scheme_distribution": {scheme: schemes.count(scheme) for scheme in set(schemes)},
            "chunk_types": list(set(chunk_types)),
            "chunk_type_distribution": {chunk_type: chunk_types.count(chunk_type) for chunk_type in set(chunk_types)},
            "relevance_distribution": {
                relevance: len([r for r in results if r["relevance"] == relevance])
                for relevance in set(r["relevance"] for r in results)
            }
        }
    
    def validate_retrieval_quality(self, results: List[Dict]) -> Dict[str, Any]:
        """Validate retrieval quality"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": self.get_retrieval_stats(results)
        }
        
        # Check minimum results
        if len(results) == 0:
            validation["errors"].append("No results retrieved")
            validation["valid"] = False
        
        # Check similarity thresholds
        low_similarity_results = [r for r in results if r["similarity_score"] < 0.4]
        if len(low_similarity_results) > len(results) * 0.5:
            validation["warnings"].append("More than 50% of results have low similarity")
        
        # Check scheme diversity
        schemes = [r["metadata"]["scheme_name"] for r in results]
        if len(set(schemes)) == 1 and len(results) > 3:
            validation["warnings"].append("All results from same scheme")
        
        return validation

class ReRanker:
    """Optional re-ranking using cross-encoder for better precision"""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name)
            logger.info(f"Loaded re-ranker: {model_name}")
        except ImportError:
            logger.warning("CrossEncoder not available. Install with: pip install sentence-transformers")
            self.model = None
    
    def rerank_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """Re-rank results using cross-encoder"""
        if not self.model or not results:
            return results
        
        try:
            # Prepare query-document pairs
            pairs = [[query, result["text"]] for result in results]
            
            # Predict relevance scores
            scores = self.model.predict(pairs)
            
            # Update results with rerank scores
            for i, result in enumerate(results):
                result["rerank_score"] = float(scores[i])
            
            # Sort by rerank score
            reranked = sorted(results, key=lambda x: x["rerank_score"], reverse=True)
            
            # Update ranks
            for i, result in enumerate(reranked):
                result["rerank_rank"] = i + 1
            
            logger.info(f"Re-ranked {len(results)} results")
            return reranked
            
        except Exception as e:
            logger.error(f"Error during re-ranking: {str(e)}")
            return results

def main():
    """Test the retrieval pipeline"""
    logger.info("Testing retrieval pipeline...")
    
    # Initialize pipeline
    try:
        pipeline = RetrievalPipeline()
    except ValueError as e:
        logger.error(f"Failed to initialize pipeline: {str(e)}")
        return
    
    # Test queries
    test_queries = [
        "What is the expense ratio of ICICI Prudential Large Cap Fund?",
        "What is the minimum SIP amount?",
        "How to download capital gains statement?",
        "What is the exit load for ICICI Prudential Dynamic Plan?"
    ]
    
    for query in test_queries:
        logger.info(f"\nQuery: {query}")
        
        # Process query
        results = pipeline.process_query(query, k=5)
        
        # Validate results
        validation = pipeline.validate_retrieval_quality(results)
        
        if validation["valid"]:
            # Filter low similarity results
            filtered_results = pipeline.filter_results(results, min_similarity=0.4)
            
            # Ensure diversity
            diverse_results = pipeline.get_diverse_results(filtered_results, max_per_scheme=2)
            
            # Print top 3 results
            for i, result in enumerate(diverse_results[:3]):
                logger.info(f"  {i+1}. {result['metadata']['scheme_name']} ({result['metadata']['chunk_type']})")
                logger.info(f"     Score: {result['similarity_score']:.3f} ({result['relevance']})")
                logger.info(f"     Text: {result['text'][:100]}...")
                logger.info(f"     Source: {result['metadata']['source_url']}")
        else:
            logger.error(f"Retrieval validation failed: {validation['errors']}")
    
    logger.info("\nRetrieval pipeline test completed!")

if __name__ == "__main__":
    main()
