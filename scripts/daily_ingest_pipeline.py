"""
Daily Ingest Pipeline - Complete End-to-End Data Processing
Phase 1 -> Phase 2 Integration Pipeline

This script orchestrates:
1. Scraping latest data from URLs
2. Processing and chunking scraped data
3. Generating embeddings for chunks
4. Updating FAISS vector database

Designed to run daily at 9:15 AM via GitHub Actions
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / 'phase1' / 'scraping_service'))
sys.path.append(str(project_root / 'phase1' / 'scheduler_service'))
sys.path.append(str(project_root / 'phase2'))
sys.path.append(str(project_root / 'scripts'))

# Import pipeline components
try:
    from scraping_service import GrowwScraper
    from scheduler_service import FundDataScheduler
    from free_embedding_pipeline import EmbeddingPipeline
    from vector_store_manager import VectorStoreManager
    from document_processor import DocumentProcessor
    from hybrid_chunking_pipeline import HybridChunkingPipeline
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required modules are available")
    sys.exit(1)

class DailyIngestPipeline:
    """Complete daily ingest pipeline orchestrator"""
    
    def __init__(self):
        self.setup_logging()
        self.project_root = project_root
        self.raw_data_dir = self.project_root / 'raw_data'
        self.processed_data_dir = self.project_root / 'processed_data'
        self.phase2_dir = self.project_root / 'phase2'
        
        # Ensure directories exist
        self.raw_data_dir.mkdir(exist_ok=True)
        self.processed_data_dir.mkdir(exist_ok=True)
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f'daily_ingest_{datetime.now().strftime("%Y%m%d")}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Daily Ingest Pipeline initialized")
    
    def step_1_scrape_latest_data(self):
        """Step 1: Scrape latest data from Groww URLs"""
        self.logger.info("=" * 60)
        self.logger.info("STEP 1: Scraping Latest Data")
        self.logger.info("=" * 60)
        
        try:
            # Initialize scraper
            scraper = GrowwScraper(headless=True)
            
            # Scrape all schemes
            schemes_data = scraper.scrape_all_schemes()
            
            if not schemes_data:
                raise Exception("No data scraped")
            
            # Save scraped data with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.raw_data_dir / f'fund_data_{timestamp}.json'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'scraped_at': datetime.now().isoformat(),
                    'total_schemes': len(schemes_data),
                    'schemes': schemes_data
                }, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ Scraped {len(schemes_data)} schemes")
            self.logger.info(f"📁 Saved to: {output_file}")
            
            return output_file, schemes_data
            
        except Exception as e:
            self.logger.error(f"❌ Scraping failed: {e}")
            raise
    
    def step_2_process_scraped_data(self, scraped_data_file, schemes_data):
        """Step 2: Process scraped data into chunks"""
        self.logger.info("=" * 60)
        self.logger.info("STEP 2: Processing Scraped Data into Chunks")
        self.logger.info("=" * 60)
        
        try:
            # Initialize document processor
            processor = DocumentProcessor()
            chunking_pipeline = HybridChunkingPipeline()
            
            # Convert scraped data to document format
            documents = []
            for scheme in schemes_data:
                # Create document text from scheme data
                doc_text = f"""
                Scheme Name: {scheme.get('scheme_name', 'Unknown')}
                
                NAV: {scheme.get('nav', 'N/A')}
                Expense Ratio: {scheme.get('expense_ratio', 'N/A')}
                Exit Load: {scheme.get('exit_load', 'N/A')}
                Minimum SIP: {scheme.get('minimum_sip', 'N/A')}
                Benchmark: {scheme.get('benchmark', 'N/A')}
                Riskometer: {scheme.get('riskometer', 'N/A')}
                AUM: {scheme.get('aum', 'N/A')}
                Returns 1Y: {scheme.get('returns_1yr', 'N/A')}
                Returns 3Y: {scheme.get('returns_3yr', 'N/A')}
                Returns 5Y: {scheme.get('returns_5yr', 'N/A')}
                
                Source URL: {scheme.get('source_url', 'N/A')}
                Last Updated: {scheme.get('last_updated', 'N/A')}
                """.strip()
                
                documents.append({
                    'text': doc_text,
                    'metadata': {
                        'scheme_name': scheme.get('scheme_name'),
                        'source_url': scheme.get('source_url'),
                        'scraped_at': scheme.get('scraped_at'),
                        'document_type': 'scraped_data',
                        'scheme_data': scheme
                    }
                })
            
            # Chunk documents
            chunks = chunking_pipeline.chunk_documents(documents)
            
            # Save chunks
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            chunks_file = self.processed_data_dir / f'chunks_{timestamp}.json'
            
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'created_at': datetime.now().isoformat(),
                    'total_chunks': len(chunks),
                    'source_file': str(scraped_data_file),
                    'chunks': chunks
                }, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ Processed {len(documents)} documents into {len(chunks)} chunks")
            self.logger.info(f"📁 Saved to: {chunks_file}")
            
            return chunks_file, chunks
            
        except Exception as e:
            self.logger.error(f"❌ Data processing failed: {e}")
            raise
    
    def step_3_generate_embeddings(self, chunks_file, chunks):
        """Step 3: Generate embeddings for chunks"""
        self.logger.info("=" * 60)
        self.logger.info("STEP 3: Generating Embeddings")
        self.logger.info("=" * 60)
        
        try:
            # Initialize embedding pipeline
            embedding_pipeline = EmbeddingPipeline()
            
            # Extract text from chunks
            chunk_texts = [chunk['text'] for chunk in chunks]
            
            # Generate embeddings
            embeddings = embedding_pipeline.generate_embeddings(chunk_texts)
            
            if len(embeddings) != len(chunks):
                raise Exception(f"Embedding count mismatch: {len(embeddings)} vs {len(chunks)}")
            
            # Save embeddings
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            embeddings_file = self.phase2_dir / f'embeddings_{timestamp}.pkl'
            
            import pickle
            with open(embeddings_file, 'wb') as f:
                pickle.dump(embeddings, f)
            
            # Also save human-readable version
            embeddings_json_file = self.phase2_dir / f'embeddings_{timestamp}.json'
            embeddings_data = {
                'created_at': datetime.now().isoformat(),
                'model': 'BGE-small-en-v1.5',
                'dimensions': len(embeddings[0]) if embeddings else 0,
                'total_chunks': len(chunks),
                'source_chunks_file': str(chunks_file),
                'embeddings': [emb.tolist() for emb in embeddings]
            }
            
            with open(embeddings_json_file, 'w', encoding='utf-8') as f:
                json.dump(embeddings_data, f, indent=2)
            
            self.logger.info(f"✅ Generated {len(embeddings)} embeddings")
            self.logger.info(f"📁 Saved to: {embeddings_file}")
            self.logger.info(f"📄 JSON saved to: {embeddings_json_file}")
            
            return embeddings_file, embeddings
            
        except Exception as e:
            self.logger.error(f"❌ Embedding generation failed: {e}")
            raise
    
    def step_4_update_faiss_database(self, chunks, embeddings):
        """Step 4: Update FAISS vector database"""
        self.logger.info("=" * 60)
        self.logger.info("STEP 4: Updating FAISS Vector Database")
        self.logger.info("=" * 60)
        
        try:
            # Initialize vector store manager
            vector_manager = VectorStoreManager()
            
            # Prepare metadata for FAISS
            metadata = []
            for chunk in chunks:
                metadata.append({
                    'text': chunk['text'],
                    'metadata': chunk.get('metadata', {}),
                    'chunk_id': chunk.get('chunk_id', len(metadata))
                })
            
            # Update FAISS index
            vector_manager.update_index(embeddings, metadata)
            
            # Save updated index
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup old index
            if (self.phase2_dir / 'faiss_index.bin').exists():
                backup_file = self.phase2_dir / f'faiss_index_backup_{timestamp}.bin'
                import shutil
                shutil.copy2(self.phase2_dir / 'faiss_index.bin', backup_file)
                self.logger.info(f"📦 Backed up old index to: {backup_file}")
            
            # Save new index and metadata
            vector_manager.save_index(str(self.phase2_dir / 'faiss_index.bin'))
            vector_manager.save_metadata(str(self.phase2_dir / 'metadata_store.json'))
            
            self.logger.info(f"✅ Updated FAISS index with {len(embeddings)} vectors")
            self.logger.info(f"📁 Index saved to: {self.phase2_dir / 'faiss_index.bin'}")
            self.logger.info(f"📄 Metadata saved to: {self.phase2_dir / 'metadata_store.json'}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ FAISS update failed: {e}")
            raise
    
    def run_complete_pipeline(self):
        """Run the complete ingest pipeline"""
        start_time = datetime.now()
        
        self.logger.info("🚀 Starting Daily Ingest Pipeline")
        self.logger.info(f"⏰ Started at: {start_time}")
        
        try:
            # Step 1: Scrape latest data
            scraped_data_file, schemes_data = self.step_1_scrape_latest_data()
            
            # Step 2: Process and chunk data
            chunks_file, chunks = self.step_2_process_scraped_data(scraped_data_file, schemes_data)
            
            # Step 3: Generate embeddings
            embeddings_file, embeddings = self.step_3_generate_embeddings(chunks_file, chunks)
            
            # Step 4: Update FAISS database
            self.step_4_update_faiss_database(chunks, embeddings)
            
            # Success
            end_time = datetime.now()
            duration = end_time - start_time
            
            self.logger.info("=" * 60)
            self.logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY")
            self.logger.info("=" * 60)
            self.logger.info(f"⏰ Completed at: {end_time}")
            self.logger.info(f"⏱️ Duration: {duration}")
            self.logger.info(f"📊 Processed {len(schemes_data)} schemes")
            self.logger.info(f"🧩 Created {len(chunks)} chunks")
            self.logger.info(f"🔢 Generated {len(embeddings)} embeddings")
            
            return {
                'status': 'success',
                'duration': str(duration),
                'schemes_processed': len(schemes_data),
                'chunks_created': len(chunks),
                'embeddings_generated': len(embeddings),
                'completed_at': end_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error("=" * 60)
            self.logger.error("❌ PIPELINE FAILED")
            self.logger.error("=" * 60)
            self.logger.error(f"💥 Error: {e}")
            
            return {
                'status': 'failed',
                'error': str(e),
                'failed_at': datetime.now().isoformat()
            }

def main():
    """Main entry point for the daily ingest pipeline"""
    pipeline = DailyIngestPipeline()
    result = pipeline.run_complete_pipeline()
    
    # Print summary for GitHub Actions
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        print(f"Duration: {result['duration']}")
        print(f"Schemes: {result['schemes_processed']}")
        print(f"Chunks: {result['chunks_created']}")
        print(f"Embeddings: {result['embeddings_generated']}")
    else:
        print(f"Error: {result['error']}")
    
    print("=" * 60)
    
    # Exit with appropriate code for GitHub Actions
    sys.exit(0 if result['status'] == 'success' else 1)

if __name__ == "__main__":
    main()
