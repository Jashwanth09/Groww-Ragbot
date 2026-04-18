"""
Pipeline Testing Script - Tests the complete daily ingest pipeline
Validates each step of the scraping -> chunking -> embedding -> FAISS workflow
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def setup_test_environment():
    """Setup test environment with logging"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / f'pipeline_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported"""
    logger = logging.getLogger(__name__)
    logger.info("Testing module imports...")
    
    try:
        # Test Phase 1 imports
        sys.path.append(str(project_root / 'phase1' / 'scraping_service'))
        sys.path.append(str(project_root / 'phase1' / 'scheduler_service'))
        sys.path.append(str(project_root / 'phase2'))
        sys.path.append(str(project_root / 'scripts'))
        
        from scraping_service import GrowwScraper
        logger.info("✅ GrowwScraper import successful")
        
        from scheduler_service import FundDataScheduler
        logger.info("✅ FundDataScheduler import successful")
        
        # Test Phase 2 imports
        from free_embedding_pipeline import EmbeddingPipeline
        logger.info("✅ EmbeddingPipeline import successful")
        
        from vector_store_manager import VectorStoreManager
        logger.info("✅ VectorStoreManager import successful")
        
        # Test scripts imports
        from document_processor import DocumentProcessor
        logger.info("✅ DocumentProcessor import successful")
        
        from hybrid_chunking_pipeline import HybridChunkingPipeline
        logger.info("✅ HybridChunkingPipeline import successful")
        
        from scraped_data_processor import ScrapedDataProcessor
        logger.info("✅ ScrapedDataProcessor import successful")
        
        from daily_ingest_pipeline import DailyIngestPipeline
        logger.info("✅ DailyIngestPipeline import successful")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False

def test_directory_structure():
    """Test that required directories exist"""
    logger = logging.getLogger(__name__)
    logger.info("Testing directory structure...")
    
    required_dirs = [
        'phase1/scraping_service',
        'phase1/scheduler_service', 
        'phase2',
        'scripts',
        'raw_data',
        'processed_data',
        'logs',
        'config'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            logger.info(f"✅ {dir_path} exists")
        else:
            logger.error(f"❌ {dir_path} missing")
            all_exist = False
    
    return all_exist

def test_configuration_files():
    """Test that configuration files exist"""
    logger = logging.getLogger(__name__)
    logger.info("Testing configuration files...")
    
    config_files = [
        'config/scheduler_config.json',
        'requirements.txt',
        '.env.example'
    ]
    
    all_exist = True
    for config_file in config_files:
        full_path = project_root / config_file
        if full_path.exists():
            logger.info(f"✅ {config_file} exists")
        else:
            logger.error(f"❌ {config_file} missing")
            all_exist = False
    
    return all_exist

def test_phase2_components():
    """Test Phase 2 components (embeddings and vector store)"""
    logger = logging.getLogger(__name__)
    logger.info("Testing Phase 2 components...")
    
    try:
        # Test embedding pipeline
        embedding_pipeline = EmbeddingPipeline()
        logger.info("✅ EmbeddingPipeline initialized")
        
        # Test vector store manager
        vector_manager = VectorStoreManager()
        logger.info("✅ VectorStoreManager initialized")
        
        # Check for existing embeddings
        phase2_dir = project_root / 'phase2'
        embeddings_file = phase2_dir / 'embeddings.pkl'
        metadata_file = phase2_dir / 'metadata_store.json'
        faiss_index = phase2_dir / 'faiss_index.bin'
        
        if embeddings_file.exists():
            logger.info("✅ Existing embeddings file found")
        else:
            logger.warning("⚠️ No existing embeddings file (expected for first run)")
        
        if metadata_file.exists():
            logger.info("✅ Existing metadata file found")
        else:
            logger.warning("⚠️ No existing metadata file (expected for first run)")
        
        if faiss_index.exists():
            logger.info("✅ Existing FAISS index found")
        else:
            logger.warning("⚠️ No existing FAISS index (expected for first run)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Phase 2 component test failed: {e}")
        return False

def test_github_actions_workflow():
    """Test GitHub Actions workflow file"""
    logger = logging.getLogger(__name__)
    logger.info("Testing GitHub Actions workflow...")
    
    workflow_file = project_root / '.github' / 'workflows' / 'scraping.yml'
    
    if workflow_file.exists():
        logger.info("✅ GitHub Actions workflow file exists")
        
        try:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            # Check for key components
            required_components = [
                'Complete Daily Ingest Pipeline',
                'daily_ingest_pipeline.py',
                'cron: \'15 9 * * 1-5\'',
                'Validate Pipeline Results',
                'Upload pipeline artifacts'
            ]
            
            all_present = True
            for component in required_components:
                if component in content:
                    logger.info(f"✅ Workflow contains: {component}")
                else:
                    logger.error(f"❌ Workflow missing: {component}")
                    all_present = False
            
            return all_present
            
        except Exception as e:
            logger.error(f"❌ Failed to read workflow file: {e}")
            return False
    else:
        logger.error("❌ GitHub Actions workflow file missing")
        return False

def run_mini_pipeline_test():
    """Run a mini version of the pipeline to test functionality"""
    logger = logging.getLogger(__name__)
    logger.info("Running mini pipeline test...")
    
    try:
        # Test document processing
        from scraped_data_processor import ScrapedDataProcessor
        processor = ScrapedDataProcessor()
        
        # Create sample scraped data
        sample_data = [{
            'scheme_name': 'Test Scheme Direct Growth',
            'nav': '15.234',
            'expense_ratio': '0.42%',
            'exit_load': '1% after 1 year',
            'minimum_sip': '5000',
            'benchmark': 'Nifty 50 TRI',
            'riskometer': 'High Risk',
            'aum': '15234.56 Cr',
            'returns_1yr': '12.34%',
            'returns_3yr': '15.67%',
            'returns_5yr': '14.89%',
            'source_url': 'https://example.com/test-scheme',
            'scraped_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }]
        
        # Save sample data
        raw_data_dir = project_root / 'raw_data'
        raw_data_dir.mkdir(exist_ok=True)
        
        sample_file = raw_data_dir / 'test_data.json'
        with open(sample_file, 'w') as f:
            json.dump({'schemes': sample_data}, f)
        
        # Test processing
        documents = processor.process_scraped_file(sample_file)
        logger.info(f"✅ Mini pipeline test: Processed {len(documents)} documents")
        
        # Test chunking
        from hybrid_chunking_pipeline import HybridChunkingPipeline
        chunking_pipeline = HybridChunkingPipeline()
        chunks = chunking_pipeline.chunk_documents(documents)
        logger.info(f"✅ Mini pipeline test: Created {len(chunks)} chunks")
        
        # Test embedding generation (small sample)
        from free_embedding_pipeline import EmbeddingPipeline
        embedding_pipeline = EmbeddingPipeline()
        
        sample_texts = [chunk['text'] for chunk in chunks[:2]]  # Just 2 chunks for test
        embeddings = embedding_pipeline.generate_embeddings(sample_texts)
        logger.info(f"✅ Mini pipeline test: Generated {len(embeddings)} embeddings")
        
        # Clean up test files
        sample_file.unlink()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Mini pipeline test failed: {e}")
        return False

def main():
    """Run all pipeline tests"""
    logger = setup_test_environment()
    
    logger.info("=" * 80)
    logger.info("PIPELINE TESTING STARTED")
    logger.info("=" * 80)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Configuration Files", test_configuration_files),
        ("Module Imports", test_imports),
        ("Phase 2 Components", test_phase2_components),
        ("GitHub Actions Workflow", test_github_actions_workflow),
        ("Mini Pipeline Test", run_mini_pipeline_test)
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Pipeline is ready for production.")
        return 0
    else:
        logger.error(f"💥 {total - passed} tests failed. Fix issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
