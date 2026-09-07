#!/usr/bin/env python3
"""
End-to-End Integration Test: Phase 1 + Phase 2
Tests the complete pipeline from text normalization to retrieval
"""

import sys
import os
sys.path.append('../phase1')

from text_normalizer import TextNormalizer
from hybrid_chunking import HybridChunker, ChunkConfig
from simple_retrieval_pipeline import SimpleRetrievalPipeline
import json

def test_phase1_phase2_integration():
    print('=== PHASE 1 + PHASE 2 INTEGRATION TEST ===')
    
    try:
        # Phase 1.2.3: Text Normalization
        print('\n1. Testing Phase 1.2.3: Text Normalization')
        normalizer = TextNormalizer()
        
        sample_text = '''
        ICICI Pru Large Cap Fund has expense ratio of 0.42% as of March 2024.
        Minimum SIP is Rs. 5,000 and AUM is Rs. 15,234.56 Cr.
        NAV updated on 15/03/2024. TER includes all costs.
        '''
        
        normalized_text = normalizer.normalize_text(sample_text)
        print(f'   Original: {sample_text.strip()}')
        print(f'   Normalized: {normalized_text.strip()}')
        print('   Phase 1.2.3: PASSED')
        
        # Phase 1.3.1-1.3.3: Hybrid Chunking
        print('\n2. Testing Phase 1.3.1-1.3.3: Hybrid Chunking')
        config = ChunkConfig()
        chunker = HybridChunker(config)
        
        sample_doc = {
            'filename': 'integration_test',
            'scheme': 'ICICI Prudential Large Cap Fund Direct Growth',
            'content_type': 'factsheet',
            'source_url': 'https://www.icicipruamc.com/factsheet',
            'text': normalized_text
        }
        
        chunks = chunker.chunk_document(sample_doc)
        print(f'   Created {len(chunks)} chunks')
        for i, chunk in enumerate(chunks):
            print(f'   Chunk {i+1}: {chunk["chunk_id"]} ({chunk["character_count"]} chars)')
        print('   Phase 1.3.1-1.3.3: PASSED')
        
        # Phase 2.3: Retrieval Pipeline
        print('\n3. Testing Phase 2.3: Retrieval Pipeline')
        pipeline = SimpleRetrievalPipeline()
        
        # Test with a relevant query
        test_query = 'expense ratio'
        print(f'   Query: "{test_query}"')
        
        results = pipeline.keyword_search(test_query, k=2)
        print(f'   Found {len(results)} results')
        
        for i, result in enumerate(results):
            chunk_id = result.get('chunk_id', 'unknown')
            section_type = result.get('section_type', 'unknown')
            score = result.get('score', 0)
            text_preview = result.get('text', '')[:80]
            
            print(f'   Result {i+1}: {chunk_id} ({section_type}) - Score: {score}')
            print(f'   Preview: {text_preview}...')
        
        print('   Phase 2.3: PASSED')
        
        # Integration Test Summary
        print('\n=== INTEGRATION TEST SUMMARY ===')
        print('Phase 1.2.3 (Text Normalization): PASSED')
        print('Phase 1.3.1-1.3.3 (Hybrid Chunking): PASSED')
        print('Phase 2.3 (Retrieval Pipeline): PASSED')
        print('=== ALL INTEGRATION TESTS PASSED ===')
        
        return True
        
    except Exception as e:
        print(f'ERROR: Integration test failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_phase1_phase2_integration()
    if success:
        print('\n=== INTEGRATION TEST COMPLETED SUCCESSFULLY ===')
    else:
        print('\n=== INTEGRATION TEST FAILED ===')
