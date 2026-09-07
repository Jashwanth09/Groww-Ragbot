import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

project_root = Path(os.path.abspath('.'))
sys.path.append(str(project_root / 'phase1' / 'scraping_service'))
sys.path.append(str(project_root / 'phase2'))
sys.path.append(str(project_root / 'scripts'))

from free_embedding_pipeline import EmbeddingPipeline
from vector_store_manager import VectorStoreManager
from document_processor import DocumentProcessor
from hybrid_chunking_pipeline import HybridChunkingPipeline

def rebuild():
    print("Rebuilding FAISS DB with BGE-small...")
    
    # 1. Load raw data
    raw_file = project_root / 'raw_data' / 'fund_data_20260417_183141.json'
    with open(raw_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    schemes_data = data['schemes']
    
    # 2. Process
    processor = DocumentProcessor()
    chunking_pipeline = HybridChunkingPipeline()
    documents = []
    for scheme in schemes_data:
        doc_text = f"Scheme Name: {scheme.get('scheme_name', 'Unknown')}\nNAV: {scheme.get('nav', 'N/A')}\nExpense Ratio: {scheme.get('expense_ratio', 'N/A')}\nExit Load: {scheme.get('exit_load', 'N/A')}\nMinimum SIP: {scheme.get('minimum_sip', 'N/A')}\nBenchmark: {scheme.get('benchmark', 'N/A')}\nRiskometer: {scheme.get('riskometer', 'N/A')}\nReturns 1Y: {scheme.get('returns_1yr', 'N/A')}\nReturns 3Y: {scheme.get('returns_3yr', 'N/A')}\nReturns 5Y: {scheme.get('returns_5yr', 'N/A')}\nSource URL: {scheme.get('source_url', 'N/A')}\nLast Updated: {scheme.get('last_updated', 'N/A')}".strip()
        documents.append({
            'text': doc_text,
            'metadata': {
                'scheme_name': scheme.get('scheme_name'),
                'source_url': scheme.get('source_url'),
                'document_type': 'scraped_data',
                'scheme_data': scheme
            }
        })
    
    chunks = chunking_pipeline.chunk_documents(documents)
    print(f"Created {len(chunks)} chunks.")
    
    # 3. Embed
    embedding_pipeline = EmbeddingPipeline()
    embeddings = embedding_pipeline.generate_embeddings(chunks)
    print(f"Generated {len(embeddings)} embeddings.")
    
    # 4. Save to FAISS
    # First, delete old index
    phase2_dir = project_root / 'phase2'
    if (phase2_dir / 'faiss_index.bin').exists():
        os.remove(phase2_dir / 'faiss_index.bin')
    
    vector_manager = VectorStoreManager()
    metadata = []
    for chunk in chunks:
        metadata.append({
            'text': chunk['text'],
            'metadata': chunk.get('metadata', {}),
            'chunk_id': chunk.get('chunk_id', len(metadata))
        })
        
    vector_manager.create_index_from_embeddings(embeddings)
    vector_manager.save_index()
    print("Rebuild complete!")

if __name__ == "__main__":
    rebuild()
