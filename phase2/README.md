# Phase 2: Embedding & Vector Store Setup

## Overview
This phase implements the embedding generation and vector database setup for the mutual fund FAQ RAG system using BGE-small-en-v1.5 free embeddings and FAISS vector database.

## Phase Structure

### Phase 2.1: Embedding Model Selection
- **Model**: BAAI/bge-small-en-v1.5 (Free, 384 dimensions)
- **Alternative**: OpenAI text-embedding-3-small (Paid, 1536 dimensions)
- **Choice**: BGE for cost-free development

### Phase 2.2: Vector Database Setup
- **Database**: FAISS (Local, free)
- **Index Type**: IndexFlatL2
- **Dimensions**: 384 (BGE embeddings)

### Phase 2.3: Retrieval Pipeline
- **Search**: Hybrid semantic + keyword
- **Quality**: Relevance scoring and filtering
- **Diversity**: Multiple scheme coverage

## Files Description

### Core Scripts
- **`free_embedding_pipeline.py`** - BGE embedding generation
- **`vector_store_manager.py`** - FAISS index management
- **`simple_retrieval_pipeline.py`** - Semantic search and retrieval

### Data Files
- **`embeddings.pkl`** - BGE embeddings (54 chunks)
- **`embeddings.json`** - Human-readable embeddings
- **`faiss_index.bin`** - FAISS vector index
- **`metadata_store.json`** - Chunk metadata lookup

### Utility Scripts
- **`embedding_pipeline.py`** - OpenAI embedding pipeline (backup)
- **`setup_demo_embeddings.py`** - Demo embeddings for testing

## Usage

### Generate Embeddings
```bash
python free_embedding_pipeline.py
```

### Setup Vector Database
```bash
python vector_store_manager.py
```

### Test Retrieval
```bash
python simple_retrieval_pipeline.py
```

## Current Status
- **54 chunks** embedded with BGE
- **384-dimensional** vectors
- **FAISS index** operational
- **Semantic search** functional
- **4 schemes** + general documents covered

## Dependencies
- sentence-transformers (BGE model)
- faiss-cpu (vector database)
- numpy (vector operations)
- json (metadata handling)

## Integration
Ready for Phase 3: LLM Integration & Answer Generation.
