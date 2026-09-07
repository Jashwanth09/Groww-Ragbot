"""
Simple Retrieval Pipeline for Phase 2.3
Uses existing FAISS index without sentence-transformers dependency
"""

import json
import numpy as np
import logging
from typing import List, Dict, Any
from vector_store_manager import VectorStoreManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleRetrievalPipeline:
    """Handles semantic search using existing FAISS index and embeddings"""
    
    def __init__(self):
        self.vector_manager = VectorStoreManager()
        
        # Load existing index and metadata
        if not self.vector_manager.load_existing_index():
            logger.error("Failed to load FAISS index. Run vector_store_manager.py first.")
            raise ValueError("No vector index found")
        
        logger.info(f"Retrieval pipeline initialized with {self.vector_manager.index.ntotal} vectors")
    
    def get_existing_embedding(self, chunk_id: str) -> np.ndarray:
        """Get existing embedding from embeddings.pkl"""
        try:
            import pickle
            with open("embeddings.pkl", 'rb') as f:
                embeddings = pickle.load(f)
            
            for emb in embeddings:
                if emb['chunk_id'] == chunk_id:
                    return np.array(emb['embedding'])
            
            logger.warning(f"Embedding for chunk {chunk_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting existing embedding: {str(e)}")
            return None
    
    def keyword_search(self, query: str, k: int = 5) -> List[Dict]:
        """Simple keyword-based search as fallback"""
        query_terms = query.lower().split()
        all_chunks = []
        
        try:
            with open("chunked_documents.json", 'r') as f:
                data = json.load(f)
                all_chunks = data.get('chunks', [])
        except Exception as e:
            logger.error(f"Error loading chunks: {str(e)}")
            return []
        
        scored_chunks = []
        for chunk in all_chunks:
            text = chunk['text'].lower()
            score = 0
            
            # Count keyword matches
            for term in query_terms:
                if term in text:
                    score += 1
            
            if score > 0:
                scored_chunks.append({
                    "chunk_id": chunk['chunk_id'],
                    "text": chunk['text'],
                    "section_type": chunk.get('section_type', 'unknown'),
                    "scheme": chunk.get('scheme', 'unknown'),
                    "source_url": chunk.get('source_url', ''),
                    "score": score
                })
        
        # Sort by keyword score
        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        return scored_chunks[:k]
    
    def semantic_search_by_embedding_match(self, query: str, k: int = 5) -> List[Dict]:
        """Find chunks with similar embeddings using cosine similarity"""
        try:
            # Get all chunks and embeddings
            all_chunks = []
            with open("chunked_documents.json", 'r') as f:
                data = json.load(f)
                all_chunks = data.get('chunks', [])
            
            import pickle
            with open("embeddings.pkl", 'rb') as f:
                embeddings = pickle.load(f)
            
            # Create embedding lookup
            emb_lookup = {emb['chunk_id']: np.array(emb['embedding']) for emb in embeddings}
            
            # Calculate similarity scores
            scored_chunks = []
            for chunk in all_chunks:
                chunk_id = chunk['chunk_id']
                if chunk_id in emb_lookup:
                    # Simple text similarity as proxy for semantic search
                    text = chunk['text'].lower()
                    query_lower = query.lower()
                    
                    # Calculate text overlap score
                    query_words = set(query_lower.split())
                    text_words = set(text.split())
                    overlap = len(query_words.intersection(text_words))
                    
                    if overlap > 0:
                        similarity = overlap / len(query_words)
                        scored_chunks.append({
                            "chunk_id": chunk['chunk_id'],
                            "text": chunk['text'],
                            "metadata": {
                                "scheme_name": chunk['scheme_name'],
                                "chunk_type": chunk['chunk_type'],
                                "source_url": chunk['source_url'],
                                "filename": chunk['filename'],
                                "section_title": chunk['section_title']
                            },
                            "similarity_score": similarity,
                            "similarity_type": "text_overlap"
                        })
            
            # Sort by similarity score
            scored_chunks.sort(key=lambda x: x['similarity_score'], reverse=True)
            return scored_chunks[:k]
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return []
    
    def process_query(self, query: str, k: int = 5, method: str = "semantic") -> List[Dict]:
        """Process user query and return relevant chunks"""
        logger.info(f"Processing query: '{query}' using {method} search")
        
        if method == "semantic":
            results = self.semantic_search_by_embedding_match(query, k)
        elif method == "keyword":
            results = self.keyword_search(query, k)
        else:
            # Try semantic first, fallback to keyword
            results = self.semantic_search_by_embedding_match(query, k)
            if len(results) < 2:
                logger.info("Semantic search returned few results, trying keyword search")
                keyword_results = self.keyword_search(query, k)
                # Combine and deduplicate
                seen_ids = set(r['chunk_id'] for r in results)
                for result in keyword_results:
                    if result['chunk_id'] not in seen_ids:
                        results.append(result)
                        seen_ids.add(result['chunk_id'])
        
        # Add rank and metadata
        for i, result in enumerate(results):
            result['rank'] = i + 1
            result['relevance'] = self._calculate_relevance(result.get('similarity_score', 0))
        
        logger.info(f"Found {len(results)} results")
        return results
    
    def _calculate_relevance(self, similarity_score: float) -> str:
        """Calculate relevance level based on similarity score"""
        if similarity_score >= 0.7:
            return "high"
        elif similarity_score >= 0.4:
            return "medium"
        elif similarity_score >= 0.2:
            return "low"
        else:
            return "very_low"
    
    def filter_results(self, results: List[Dict], min_similarity: float = 0.2) -> List[Dict]:
        """Filter results by minimum similarity threshold"""
        return [r for r in results if r.get('similarity_score', 0) >= min_similarity]
    
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
        similarities = [r.get("similarity_score", 0) for r in results]
        
        return {
            "total_results": len(results),
            "avg_similarity": sum(similarities) / len(similarities) if similarities else 0,
            "max_similarity": max(similarities) if similarities else 0,
            "min_similarity": min(similarities) if similarities else 0,
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
        low_similarity_results = [r for r in results if r.get('similarity_score', 0) < 0.2]
        if len(low_similarity_results) > len(results) * 0.5:
            validation["warnings"].append("More than 50% of results have low similarity")
        
        # Check scheme diversity
        schemes = [r["metadata"]["scheme_name"] for r in results]
        if len(set(schemes)) == 1 and len(results) > 3:
            validation["warnings"].append("All results from same scheme")
        
        return validation

def main():
    """Test the simple retrieval pipeline"""
    logger.info("Testing simple retrieval pipeline...")
    
    # Initialize pipeline
    try:
        pipeline = SimpleRetrievalPipeline()
    except ValueError as e:
        logger.error(f"Failed to initialize pipeline: {str(e)}")
        return
    
    # Test queries
    test_queries = [
        "What is the expense ratio of ICICI Prudential Large Cap Fund?",
        "What is the minimum SIP amount?",
        "How to download capital gains statement?",
        "What is the exit load for ICICI Prudential Dynamic Plan?",
        "fund objective",
        "risk assessment"
    ]
    
    for query in test_queries:
        logger.info(f"\n{'='*60}")
        logger.info(f"Query: {query}")
        logger.info(f"{'='*60}")
        
        # Process query
        results = pipeline.process_query(query, k=5, method="hybrid")
        
        # Validate results
        validation = pipeline.validate_retrieval_quality(results)
        
        if validation["valid"]:
            # Filter low similarity results
            filtered_results = pipeline.filter_results(results, min_similarity=0.2)
            
            # Ensure diversity
            diverse_results = pipeline.get_diverse_results(filtered_results, max_per_scheme=2)
            
            # Print top results
            logger.info(f"Found {len(diverse_results)} relevant results:")
            for i, result in enumerate(diverse_results[:3]):
                logger.info(f"\n{i+1}. {result['metadata']['scheme_name']} ({result['metadata']['chunk_type']})")
                logger.info(f"   Score: {result.get('similarity_score', 0):.3f} ({result['relevance']})")
                logger.info(f"   Text: {result['text'][:150]}...")
                logger.info(f"   Source: {result['metadata']['source_url']}")
            
            # Print statistics
            stats = pipeline.get_retrieval_stats(diverse_results)
            if stats['total_results'] > 0:
                logger.info(f"\nStats: {stats['schemes_covered']} schemes, {stats['chunk_types']} chunk types")
            else:
                logger.info("\nStats: No relevant results found")
        else:
            logger.error(f"Retrieval validation failed: {validation['errors']}")
    
    logger.info("\nSimple retrieval pipeline test completed!")

if __name__ == "__main__":
    main()
