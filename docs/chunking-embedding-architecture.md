# Chunking & Embedding Pipeline Architecture

## Overview
This document details the automated chunking and embedding pipeline that processes scraped mutual fund data from GitHub Actions and updates the vector database for the RAG system.

## Phase 1: GitHub Actions Workflow Integration

### 1.1 Workflow Trigger Configuration
```yaml
# .github/workflows/process-fund-data.yml
name: Process Fund Data & Update Vector DB

on:
  workflow_dispatch:  # Manual trigger for testing
  schedule:
    - cron: '15 9 * * 1-5'  # 9:15 AM Monday-Friday (market days)
  push:
    paths:
      - 'raw_data/fund_data_*.json'  # Trigger when new data files are added

jobs:
  process-fund-data:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          
      - name: Process scraped data
        run: python scripts/chunking_pipeline.py
        
      - name: Generate embeddings
        run: python scripts/embedding_pipeline.py
        
      - name: Update vector database
        run: python scripts/vector_store_update.py
        
      - name: Commit updated embeddings
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add processed_data/ embeddings/
          git commit -m "Update vector database with latest fund data" || exit 0
          git push
```

### 1.2 Environment Variables & Secrets
```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  DATA_DATE: ${{ github.event.head_commit.timestamp }}
  WORKFLOW_RUN_ID: ${{ github.run_id }}
```

## Phase 2: Data Ingestion & Preprocessing

### 2.1 Raw Data Validation
```python
# scripts/data_validator.py
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

class FundDataValidator:
    """Validates scraped fund data before processing"""
    
    REQUIRED_FIELDS = [
        'scheme_name', 'nav', 'expense_ratio', 'exit_load',
        'minimum_sip', 'benchmark', 'riskometer', 'aum',
        'returns_1yr', 'returns_3yr', 'returns_5yr',
        'last_updated', 'source_url'
    ]
    
    EXPECTED_SCHEMES = [
        "ICICI Prudential Dynamic Plan Direct Growth",
        "ICICI Prudential Large Cap Fund Direct Growth", 
        "ICICI Prudential Nifty Next 50 Index Fund Direct Growth",
        "ICICI Prudential Top 100 Fund Direct Growth"
    ]
    
    def validate_data_file(self, file_path: str) -> Dict[str, Any]:
        """Validate a single scraped data file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'schemes_found': []
            }
            
            # Check if we have data for all expected schemes
            scheme_names = [item.get('scheme_name', '') for item in data]
            
            for expected_scheme in self.EXPECTED_SCHEMES:
                if expected_scheme not in scheme_names:
                    validation_result['errors'].append(f"Missing data for: {expected_scheme}")
                    validation_result['valid'] = False
                else:
                    validation_result['schemes_found'].append(expected_scheme)
            
            # Validate each scheme's data
            for i, scheme_data in enumerate(data):
                scheme_errors = self._validate_scheme_data(scheme_data, i)
                validation_result['errors'].extend(scheme_errors)
            
            validation_result['valid'] = len(validation_result['errors']) == 0
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"File validation failed: {str(e)}"],
                'warnings': [],
                'schemes_found': []
            }
    
    def _validate_scheme_data(self, scheme_data: Dict, index: int) -> List[str]:
        """Validate individual scheme data"""
        errors = []
        
        for field in self.REQUIRED_FIELDS:
            if field not in scheme_data or not scheme_data[field]:
                errors.append(f"Scheme {index}: Missing or empty field '{field}'")
        
        # Validate data formats
        if 'nav' in scheme_data and scheme_data['nav'] != 'N/A':
            try:
                float(scheme_data['nav'].replace('Rs.', '').replace(',', '').strip())
            except ValueError:
                errors.append(f"Scheme {index}: Invalid NAV format")
        
        if 'expense_ratio' in scheme_data and scheme_data['expense_ratio'] != 'N/A':
            try:
                float(scheme_data['expense_ratio'].replace('%', '').strip())
            except ValueError:
                errors.append(f"Scheme {index}: Invalid expense ratio format")
        
        return errors
```

### 2.2 Data Normalization Pipeline
```python
# scripts/data_normalizer.py
import re
from typing import Dict, Any

class FundDataNormalizer:
    """Normalizes scraped data to consistent format"""
    
    def normalize_scheme_data(self, raw_data: Dict) -> Dict:
        """Convert raw scraped data to standardized format"""
        normalized = {
            'scheme_name': self._normalize_scheme_name(raw_data.get('scheme_name', '')),
            'nav': self._normalize_nav(raw_data.get('nav', 'N/A')),
            'expense_ratio': self._normalize_percentage(raw_data.get('expense_ratio', 'N/A')),
            'exit_load': self._normalize_exit_load(raw_data.get('exit_load', 'N/A')),
            'minimum_sip': self._normalize_currency(raw_data.get('minimum_sip', 'N/A')),
            'benchmark': self._clean_text(raw_data.get('benchmark', 'N/A')),
            'riskometer': self._normalize_riskometer(raw_data.get('riskometer', 'N/A')),
            'aum': self._normalize_aum(raw_data.get('aum', 'N/A')),
            'returns_1yr': self._normalize_percentage(raw_data.get('returns_1yr', 'N/A')),
            'returns_3yr': self._normalize_percentage(raw_data.get('returns_3yr', 'N/A')),
            'returns_5yr': self._normalize_percentage(raw_data.get('returns_5yr', 'N/A')),
            'last_updated': raw_data.get('last_updated', ''),
            'source_url': raw_data.get('source_url', ''),
            'data_date': raw_data.get('last_updated', '').split('T')[0] if raw_data.get('last_updated') else ''
        }
        
        return normalized
    
    def _normalize_scheme_name(self, name: str) -> str:
        """Standardize scheme names"""
        name_mapping = {
            'ICICI Pru Dynamic Plan': 'ICICI Prudential Dynamic Plan Direct Growth',
            'ICICI Pru Large Cap Fund': 'ICICI Prudential Large Cap Fund Direct Growth',
            'ICICI Pru Nifty Next 50': 'ICICI Prudential Nifty Next 50 Index Fund Direct Growth',
            'ICICI Pru Top 100 Fund': 'ICICI Prudential Top 100 Fund Direct Growth'
        }
        
        for short_name, full_name in name_mapping.items():
            if short_name in name:
                return full_name
        
        return name.strip()
    
    def _normalize_nav(self, nav_str: str) -> str:
        """Extract NAV value from various formats"""
        if nav_str == 'N/A' or not nav_str:
            return 'N/A'
        
        # Extract numeric value from formats like "Rs. 15.2345" or "15.2345"
        nav_match = re.search(r'[\d,.]+', nav_str.replace('Rs.', '').replace('Rs', '').strip())
        if nav_match:
            return nav_match.group().replace(',', '')
        
        return 'N/A'
    
    def _normalize_percentage(self, perc_str: str) -> str:
        """Extract percentage value"""
        if perc_str == 'N/A' or not perc_str:
            return 'N/A'
        
        # Extract numeric value from formats like "0.42%" or "0.42 %"
        perc_match = re.search(r'[\d.]+', perc_str)
        if perc_match:
            return perc_match.group()
        
        return 'N/A'
    
    def _normalize_currency(self, curr_str: str) -> str:
        """Extract currency amount"""
        if curr_str == 'N/A' or not curr_str:
            return 'N/A'
        
        # Extract numeric value from formats like "Rs. 5000" or "5000"
        curr_match = re.search(r'[\d,]+', curr_str.replace('Rs.', '').replace('Rs', '').strip())
        if curr_match:
            return curr_match.group().replace(',', '')
        
        return 'N/A'
    
    def _normalize_exit_load(self, exit_load: str) -> str:
        """Normalize exit load information"""
        if exit_load == 'N/A' or not exit_load:
            return 'N/A'
        
        # Extract percentage and time period
        exit_load = exit_load.lower().strip()
        
        # Handle various formats: "1% after 1 year", "Nil after 365 days", etc.
        if 'nil' in exit_load or 'none' in exit_load:
            return '0%'
        
        # Extract percentage
        perc_match = re.search(r'[\d.]+%', exit_load)
        if perc_match:
            return perc_match.group()
        
        return exit_load
    
    def _normalize_riskometer(self, risk: str) -> str:
        """Standardize riskometer ratings"""
        risk_mapping = {
            'very high': 'Very High Risk',
            'high': 'High Risk', 
            'moderately high': 'Moderately High Risk',
            'moderate': 'Moderate Risk',
            'moderately low': 'Moderately Low Risk',
            'low': 'Low Risk'
        }
        
        risk_lower = risk.lower().strip()
        for key, value in risk_mapping.items():
            if key in risk_lower:
                return value
        
        return risk.strip()
    
    def _normalize_aum(self, aum_str: str) -> str:
        """Normalize AUM values"""
        if aum_str == 'N/A' or not aum_str:
            return 'N/A'
        
        # Handle formats like "Rs. 15,234 Cr" or "15234.56 Cr"
        aum_str = aum_str.lower().replace('rs.', '').replace('rs', '').strip()
        
        # Extract numeric value and unit
        num_match = re.search(r'[\d,.]+', aum_str)
        unit_match = re.search(r'(cr|lakh|thousand)', aum_str)
        
        if num_match:
            value = num_match.group().replace(',', '')
            unit = unit_match.group() if unit_match else ''
            
            # Convert to crores for consistency
            if unit == 'lakh':
                value = str(float(value) / 100)
            elif unit == 'thousand':
                value = str(float(value) / 10000)
            
            return f"{value} Cr"
        
        return 'N/A'
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text fields"""
        if text == 'N/A' or not text:
            return 'N/A'
        
        return text.strip().replace('\n', ' ').replace('\t', ' ')
```

## Phase 3: Hybrid Chunking Strategy

### 3.1 Hybrid Semantic + Fixed-Size Chunking
```python
# scripts/hybrid_chunking_pipeline.py
import json
from typing import List, Dict, Any, Tuple
from datetime import datetime

class HybridDocumentChunker:
    """Implements hybrid chunking: semantic + fixed-size with overlap"""
    
    def __init__(self):
        self.chunk_id_counter = 0
        
        # Hybrid chunking parameters
        self.target_chunk_size = 400    # characters
        self.chunk_overlap = 100        # 25% overlap
        self.min_chunk_size = 50        # minimum viable chunk
        
        # Semantic section markers
        self.section_markers = [
            "Fund Objective", "Investment Objective", "Objective",
            "Expense Ratio", "Total Expense Ratio", "TER",
            "Exit Load", "Exit Load Structure",
            "Minimum Investment", "Minimum SIP", "Minimum Application",
            "Benchmark", "Benchmark Index",
            "Riskometer", "Risk Profile", "Risk Factors",
            "Asset Allocation", "Portfolio Allocation",
            "How to Download", "Download Statement", "Capital Gains",
            "Top Holdings", "Portfolio",
            "Performance", "Returns",
            "Fund Manager", "Launch Date",
            "Taxation", "Tax"
        ]
    
    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """Apply hybrid chunking strategy to all documents"""
        all_chunks = []
        
        for doc in documents:
            # Determine chunking strategy based on document type
            if doc['content_type'] in ['factsheet', 'kim']:
                chunks = self._hybrid_structured_chunking(doc)
            else:
                chunks = self._hybrid_general_chunking(doc)
            
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def _hybrid_structured_chunking(self, doc: Dict) -> List[Dict]:
        """Hybrid chunking for structured documents (factsheets, KIM)"""
        chunks = []
        
        # Step 1: Split by semantic sections
        sections = self._split_by_sections(doc['content'])
        
        for section_title, section_content in sections:
            # Step 2: Apply fixed-size chunking with overlap
            section_chunks = self._chunk_with_overlap(
                section_content, section_title, doc
            )
            chunks.extend(section_chunks)
        
        return chunks
    
    def _chunk_with_overlap(self, content: str, section_title: str, doc: Dict) -> List[Dict]:
        """Apply fixed-size chunking with overlap to content"""
        chunks = []
        
        # Clean and normalize content
        content = self._clean_text(content)
        
        if len(content) <= self.target_chunk_size:
            # Single chunk for small content
            chunk = self._create_chunk_object(content, section_title, doc, 0)
            chunks.append(chunk)
        else:
            # Sliding window chunking with overlap
            start = 0
            chunk_index = 0
            
            while start < len(content):
                end = start + self.target_chunk_size
                
                # Try to break at sentence boundary
                if end < len(content):
                    end = self._find_sentence_boundary(content, end)
                
                chunk_text = content[start:end].strip()
                
                if len(chunk_text) >= self.min_chunk_size:
                    chunk = self._create_chunk_object(
                        chunk_text, section_title, doc, chunk_index
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Move start position with overlap
                start = end - self.chunk_overlap
                if start < 0:
                    start = 0
                
                if start >= len(content):
                    break
        
        return chunks
        
        # 6. Historical Data Chunk (if available)
        if self._has_historical_data(scheme_data):
            chunks.append(self._create_historical_chunk(scheme_data, scheme_name))
        
        return chunks
    
    def _create_basic_info_chunk(self, scheme_data: Dict, scheme_name: str) -> Dict:
        """Create chunk with basic scheme information"""
        text = f"""
        {scheme_name} - Basic Information:
        
        Current NAV: {scheme_data['nav']}
        Assets Under Management (AUM): {scheme_data['aum']}
        Benchmark Index: {scheme_data['benchmark']}
        Last Updated: {scheme_data['last_updated']}
        
        Source: {scheme_data['source_url']}
        """.strip()
        
        return self._create_chunk_object(
            text=text,
            scheme_name=scheme_name,
            chunk_type="basic_info",
            source_url=scheme_data['source_url'],
            data_date=scheme_data['data_date']
        )
    
    def _create_performance_chunk(self, scheme_data: Dict, scheme_name: str) -> Dict:
        """Create chunk with performance metrics"""
        text = f"""
        {scheme_name} - Performance Analysis:
        
        1 Year Returns: {scheme_data['returns_1yr']}
        3 Year Returns: {scheme_data['returns_3yr']}
        5 Year Returns: {scheme_data['returns_5yr']}
        
        Performance data as of: {scheme_data['last_updated']}
        Note: Past performance does not guarantee future results.
        
        Source: {scheme_data['source_url']}
        """.strip()
        
        return self._create_chunk_object(
            text=text,
            scheme_name=scheme_name,
            chunk_type="performance",
            source_url=scheme_data['source_url'],
            data_date=scheme_data['data_date']
        )
    
    def _create_cost_analysis_chunk(self, scheme_data: Dict, scheme_name: str) -> Dict:
        """Create chunk with cost-related information"""
        text = f"""
        {scheme_name} - Cost Structure:
        
        Total Expense Ratio (TER): {scheme_data['expense_ratio']}%
        Exit Load: {scheme_data['exit_load']}
        
        The expense ratio is charged annually and affects your returns.
        Exit load applies if you redeem units within the specified period.
        
        Source: {scheme_data['source_url']}
        """.strip()
        
        return self._create_chunk_object(
            text=text,
            scheme_name=scheme_name,
            chunk_type="cost_analysis",
            source_url=scheme_data['source_url'],
            data_date=scheme_data['data_date']
        )
    
    def _create_risk_chunk(self, scheme_data: Dict, scheme_name: str) -> Dict:
        """Create chunk with risk assessment"""
        text = f"""
        {scheme_name} - Risk Profile:
        
        Riskometer Rating: {scheme_data['riskometer']}
        
        This rating indicates the level of risk associated with the scheme.
        Higher risk schemes have the potential for higher returns but also higher losses.
        
        Source: {scheme_data['source_url']}
        """.strip()
        
        return self._create_chunk_object(
            text=text,
            scheme_name=scheme_name,
            chunk_type="risk_assessment",
            source_url=scheme_data['source_url'],
            data_date=scheme_data['data_date']
        )
    
    def _create_investment_chunk(self, scheme_data: Dict, scheme_name: str) -> Dict:
        """Create chunk with investment details"""
        text = f"""
        {scheme_name} - Investment Details:
        
        Minimum SIP Amount: {scheme_data['minimum_sip']}
        
        Systematic Investment Plan (SIP) allows regular investments.
        The minimum amount varies by scheme and can be as low as {scheme_data['minimum_sip']}.
        
        Source: {scheme_data['source_url']}
        """.strip()
        
        return self._create_chunk_object(
            text=text,
            scheme_name=scheme_name,
            chunk_type="investment_details",
            source_url=scheme_data['source_url'],
            data_date=scheme_data['data_date']
        )
    
    def _create_historical_chunk(self, scheme_data: Dict, scheme_name: str) -> Dict:
        """Create chunk with historical context"""
        text = f"""
        {scheme_name} - Historical Context:
        
        Data Date: {scheme_data['data_date']}
        Last Updated: {scheme_data['last_updated']}
        
        This data represents the most recent available information.
        Historical trends should be analyzed for investment decisions.
        
        Source: {scheme_data['source_url']}
        """.strip()
        
        return self._create_chunk_object(
            text=text,
            scheme_name=scheme_name,
            chunk_type="historical_context",
            source_url=scheme_data['source_url'],
            data_date=scheme_data['data_date']
        )
    
    def _create_chunk_object(self, text: str, scheme_name: str, chunk_type: str, 
                           source_url: str, data_date: str) -> Dict:
        """Create standardized chunk object"""
        self.chunk_id_counter += 1
        
        return {
            "chunk_id": f"{scheme_name.replace(' ', '_').lower()}_{chunk_type}_{self.chunk_id_counter:03d}",
            "text": text,
            "scheme_name": scheme_name,
            "chunk_type": chunk_type,
            "source_url": source_url,
            "data_date": data_date,
            "created_at": datetime.now().isoformat(),
            "token_count": self._estimate_tokens(text),
            "last_updated": data_date
        }
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ~ 4 characters)"""
        return len(text) // 4
    
    def _has_historical_data(self, scheme_data: Dict) -> bool:
        """Check if scheme has sufficient historical data"""
        return (scheme_data.get('returns_1yr') != 'N/A' and 
                scheme_data.get('returns_3yr') != 'N/A' and 
                scheme_data.get('returns_5yr') != 'N/A')
```

### 3.2 Chunk Quality Control
```python
# scripts/chunk_quality_control.py
import re
from typing import List, Dict

class ChunkQualityController:
    """Ensures chunk quality and consistency"""
    
    def validate_chunks(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Validate all chunks before embedding"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': self._calculate_chunk_stats(chunks)
        }
        
        for i, chunk in enumerate(chunks):
            chunk_errors = self._validate_single_chunk(chunk, i)
            validation_result['errors'].extend(chunk_errors)
        
        # Check for duplicate chunks
        duplicates = self._find_duplicate_chunks(chunks)
        if duplicates:
            validation_result['warnings'].append(f"Found {len(duplicates)} potentially duplicate chunks")
        
        validation_result['valid'] = len(validation_result['errors']) == 0
        return validation_result
    
    def _validate_single_chunk(self, chunk: Dict, index: int) -> List[str]:
        """Validate individual chunk"""
        errors = []
        required_fields = ['chunk_id', 'text', 'scheme_name', 'chunk_type', 'source_url']
        
        for field in required_fields:
            if field not in chunk or not chunk[field]:
                errors.append(f"Chunk {index}: Missing or empty field '{field}'")
        
        # Validate text length
        if 'text' in chunk:
            text_length = len(chunk['text'])
            if text_length < 50:
                errors.append(f"Chunk {index}: Text too short ({text_length} chars)")
            elif text_length > 2000:
                errors.append(f"Chunk {index}: Text too long ({text_length} chars)")
        
        # Validate scheme name
        if 'scheme_name' in chunk:
            valid_schemes = [
                "ICICI Prudential Dynamic Plan Direct Growth",
                "ICICI Prudential Large Cap Fund Direct Growth",
                "ICICI Prudential Nifty Next 50 Index Fund Direct Growth",
                "ICICI Prudential Top 100 Fund Direct Growth"
            ]
            if chunk['scheme_name'] not in valid_schemes:
                errors.append(f"Chunk {index}: Invalid scheme name '{chunk['scheme_name']}'")
        
        return errors
    
    def _find_duplicate_chunks(self, chunks: List[Dict]) -> List[int]:
        """Find potentially duplicate chunks"""
        seen_texts = set()
        duplicates = []
        
        for i, chunk in enumerate(chunks):
            text_hash = hash(chunk['text'])
            if text_hash in seen_texts:
                duplicates.append(i)
            seen_texts.add(text_hash)
        
        return duplicates
    
    def _calculate_chunk_stats(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Calculate chunk statistics"""
        if not chunks:
            return {'total_chunks': 0}
        
        token_counts = [chunk.get('token_count', 0) for chunk in chunks]
        chunk_types = [chunk.get('chunk_type', '') for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'avg_token_count': sum(token_counts) / len(token_counts),
            'min_token_count': min(token_counts),
            'max_token_count': max(token_counts),
            'chunk_type_distribution': {
                chunk_type: chunk_types.count(chunk_type) 
                for chunk_type in set(chunk_types)
            }
        }
```

## Phase 4: Embedding Generation Pipeline

### 4.1 BGE Free Embeddings Service
```python
# scripts/embedding_pipeline.py
import json
import pickle
import logging
from typing import List, Dict, Any
from datetime import datetime
from sentence_transformers import SentenceTransformer

class EmbeddingGenerator:
    """Generates embeddings for fund data chunks"""
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.embedding_dimension = 384  # for BGE-small-en-v1.5
        
    def generate_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """Generate embeddings for all chunks"""
        embeddings = []
        
        # Generate embeddings in batches
        batch_size = 32  # Optimal for BGE
        texts = [chunk['text'] for chunk in chunks]
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_chunks = chunks[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            # Generate embeddings using BGE
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
                        "data_date": chunk['data_date'],
                        "created_at": chunk['created_at'],
                        "token_count": chunk['token_count']
                    },
                    "text_preview": chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text'],
                    "generated_at": datetime.now().isoformat(),
                    "batch_number": batch_num,
                    "chunk_index": j
                }
                embeddings.append(embedding_object)
            
            logging.info(f"Processed batch {batch_num}/{(len(texts) + batch_size - 1) // batch_size}")
        
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
                        "data_date": chunk['data_date'],
                        "created_at": chunk['created_at'],
                        "token_count": chunk['token_count']
                    },
                    "text_preview": chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text'],
                    "generated_at": datetime.now().isoformat(),
                    "batch_number": batch_num,
                    "chunk_index": i
                }
                batch_embeddings.append(embedding_object)
            
            return batch_embeddings
            
        except Exception as e:
            logging.error(f"Failed to generate embeddings for batch {batch_num}: {str(e)}")
            raise
    
    def save_embeddings(self, embeddings: List[Dict], file_path: str):
        """Save embeddings to file"""
        with open(file_path, 'wb') as f:
            pickle.dump(embeddings, f)
        
        # Also save as JSON for inspection
        json_path = file_path.replace('.pkl', '.json')
        with open(json_path, 'w') as f:
            json.dump(embeddings, f, indent=2)
        
        logging.info(f"Saved {len(embeddings)} embeddings to {file_path}")
    
    def load_embeddings(self, file_path: str) -> List[Dict]:
        """Load embeddings from file"""
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    
    def get_embedding_stats(self, embeddings: List[Dict]) -> Dict[str, Any]:
        """Calculate embedding statistics"""
        if not embeddings:
            return {'total_embeddings': 0}
        
        return {
            'total_embeddings': len(embeddings),
            'embedding_dimension': len(embeddings[0]['embedding']),
            'model_used': self.model,
            'generation_date': embeddings[0]['generated_at'],
            'schemes_covered': list(set(emb['metadata']['scheme_name'] for emb in embeddings)),
            'chunk_types': list(set(emb['metadata']['chunk_type'] for emb in embeddings))
        }
```

### 4.2 Embedding Quality Assurance
```python
# scripts/embedding_quality_control.py
import numpy as np
from typing import List, Dict
from sklearn.metrics.pairwise import cosine_similarity

class EmbeddingQualityController:
    """Validates embedding quality and consistency"""
    
    def validate_embeddings(self, embeddings: List[Dict]) -> Dict[str, Any]:
        """Validate all embeddings"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': self._calculate_embedding_stats(embeddings)
        }
        
        # Check embedding dimensions
        if embeddings:
            expected_dim = len(embeddings[0]['embedding'])
            for i, emb in enumerate(embeddings):
                if len(emb['embedding']) != expected_dim:
                    validation_result['errors'].append(f"Embedding {i}: Incorrect dimension {len(emb['embedding'])}, expected {expected_dim}")
        
        # Check for zero vectors
        zero_vectors = self._find_zero_vectors(embeddings)
        if zero_vectors:
            validation_result['warnings'].append(f"Found {len(zero_vectors)} zero vectors")
        
        # Check embedding similarity distribution
        similarity_stats = self._analyze_similarity_distribution(embeddings)
        validation_result['similarity_analysis'] = similarity_stats
        
        validation_result['valid'] = len(validation_result['errors']) == 0
        return validation_result
    
    def _find_zero_vectors(self, embeddings: List[Dict]) -> List[int]:
        """Find embeddings that are zero vectors"""
        zero_indices = []
        
        for i, emb in enumerate(embeddings):
            embedding_vector = np.array(emb['embedding'])
            if np.allclose(embedding_vector, 0):
                zero_indices.append(i)
        
        return zero_indices
    
    def _analyze_similarity_distribution(self, embeddings: List[Dict]) -> Dict[str, Any]:
        """Analyze similarity distribution among embeddings"""
        if len(embeddings) < 2:
            return {'error': 'Need at least 2 embeddings for similarity analysis'}
        
        # Sample 100 embeddings for analysis (to avoid memory issues)
        sample_size = min(100, len(embeddings))
        sample_indices = np.random.choice(len(embeddings), sample_size, replace=False)
        sample_embeddings = [embeddings[i]['embedding'] for i in sample_indices]
        
        # Calculate pairwise similarities
        embedding_matrix = np.array(sample_embeddings)
        similarities = cosine_similarity(embedding_matrix)
        
        # Extract upper triangle (excluding diagonal)
        upper_triangle = similarities[np.triu_indices_from(similarities, k=1)]
        
        return {
            'sample_size': sample_size,
            'avg_similarity': float(np.mean(upper_triangle)),
            'min_similarity': float(np.min(upper_triangle)),
            'max_similarity': float(np.max(upper_triangle)),
            'std_similarity': float(np.std(upper_triangle))
        }
    
    def _calculate_embedding_stats(self, embeddings: List[Dict]) -> Dict[str, Any]:
        """Calculate embedding statistics"""
        if not embeddings:
            return {'total_embeddings': 0}
        
        embedding_vectors = [np.array(emb['embedding']) for emb in embeddings]
        
        return {
            'total_embeddings': len(embeddings),
            'embedding_dimension': len(embeddings[0]['embedding']),
            'avg_norm': float(np.mean([np.linalg.norm(v) for v in embedding_vectors])),
            'schemes_covered': len(set(emb['metadata']['scheme_name'] for emb in embeddings)),
            'chunk_types': len(set(emb['metadata']['chunk_type'] for emb in embeddings))
        }
```

## Phase 5: Vector Database Update

### 5.1 FAISS Index Management
```python
# scripts/vector_store_update.py
import faiss
import numpy as np
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

class VectorStoreManager:
    """Manages FAISS vector index for semantic search"""
    
    def __init__(self, index_path: str = "faiss_index.bin", 
                 metadata_path: str = "metadata_store.json"):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.index = None
        self.metadata_store = {}
        
    def load_existing_index(self):
        """Load existing FAISS index and metadata"""
        try:
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'r') as f:
                self.metadata_store = json.load(f)
            logging.info(f"Loaded existing index with {self.index.ntotal} vectors")
        except FileNotFoundError:
            logging.info("No existing index found, creating new one")
            self.index = None
            self.metadata_store = {}
    
    def create_new_index(self, embeddings: List[Dict]):
        """Create new FAISS index from embeddings"""
        if not embeddings:
            raise ValueError("No embeddings provided")
        
        # Determine embedding dimension
        dimension = 384  # for BGE-small-en-v1.5
        index = faiss.IndexFlatL2(dimension)
        
        # Add embeddings to index
        embedding_matrix = np.array([emb['embedding'] for emb in embeddings])
        index.add(embedding_matrix)
        
        # Create metadata store
        self.metadata_store = {
            i: {
                'chunk_id': emb['chunk_id'],
                'scheme_name': emb['metadata']['scheme_name'],
                'chunk_type': emb['metadata']['chunk_type'],
                'source_url': emb['metadata']['source_url'],
                'data_date': emb['metadata']['data_date'],
                'text_preview': emb['text_preview']
            }
            for i, emb in enumerate(embeddings)
        }
        
        logging.info(f"Created new index with {len(embeddings)} vectors")
    
    def update_index(self, new_embeddings: List[Dict]):
        """Update existing index with new embeddings"""
        if not self.index:
            self.create_new_index(new_embeddings)
            return
        
        # Add new embeddings
        embedding_matrix = np.array([emb['embedding'] for emb in new_embeddings])
        start_index = self.index.ntotal
        self.index.add(embedding_matrix)
        
        # Update metadata store
        for i, emb in enumerate(new_embeddings):
            self.metadata_store[start_index + i] = {
                'chunk_id': emb['chunk_id'],
                'scheme_name': emb['metadata']['scheme_name'],
                'chunk_type': emb['metadata']['chunk_type'],
                'source_url': emb['metadata']['source_url'],
                'data_date': emb['metadata']['data_date'],
                'text_preview': emb['text_preview']
            }
        
        logging.info(f"Updated index with {len(new_embeddings)} new vectors")
    
    def save_index(self):
        """Save FAISS index and metadata to disk"""
        if self.index:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata_store, f, indent=2)
            logging.info(f"Saved index with {self.index.ntotal} vectors")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get current index statistics"""
        if not self.index:
            return {'total_vectors': 0, 'status': 'no_index'}
        
        return {
            'total_vectors': self.index.ntotal,
            'embedding_dimension': self.index.d,
            'index_type': type(self.index).__name__,
            'metadata_entries': len(self.metadata_store),
            'last_updated': datetime.now().isoformat(),
            'schemes_covered': len(set(meta['scheme_name'] for meta in self.metadata_store.values())),
            'chunk_types': len(set(meta['chunk_type'] for meta in self.metadata_store.values()))
        }
    
    def validate_index_integrity(self) -> Dict[str, Any]:
        """Validate index integrity"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if not self.index:
            validation_result['errors'].append("No index loaded")
            validation_result['valid'] = False
            return validation_result
        
        # Check index vs metadata consistency
        if self.index.ntotal != len(self.metadata_store):
            validation_result['errors'].append(
                f"Index vectors ({self.index.ntotal}) != metadata entries ({len(self.metadata_store)})"
            )
            validation_result['valid'] = False
        
        # Check for duplicate chunk IDs
        chunk_ids = [meta['chunk_id'] for meta in self.metadata_store.values()]
        if len(chunk_ids) != len(set(chunk_ids)):
            validation_result['warnings'].append("Duplicate chunk IDs found in metadata")
        
        return validation_result
```

### 5.2 Deployment Verification
```python
# scripts/deployment_verification.py
import json
import logging
from typing import Dict, Any

class DeploymentVerifier:
    """Verifies successful deployment of updated vector database"""
    
    def verify_deployment(self, deployment_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Verify deployment meets requirements"""
        verification_result = {
            'success': True,
            'errors': [],
            'warnings': [],
            'metrics': deployment_stats
        }
        
        # Check minimum requirements
        if deployment_stats.get('total_vectors', 0) < 20:
            verification_result['errors'].append(
                f"Insufficient vectors: {deployment_stats.get('total_vectors', 0)} < 20"
            )
            verification_result['success'] = False
        
        # Check scheme coverage
        expected_schemes = [
            "ICICI Prudential Dynamic Plan Direct Growth",
            "ICICI Prudential Large Cap Fund Direct Growth",
            "ICICI Prudential Nifty Next 50 Index Fund Direct Growth",
            "ICICI Prudential Top 100 Fund Direct Growth"
        ]
        
        schemes_covered = deployment_stats.get('schemes_covered', 0)
        if schemes_covered < len(expected_schemes):
            verification_result['warnings'].append(
                f"Only {schemes_covered}/{len(expected_schemes)} schemes covered"
            )
        
        # Check chunk type diversity
        chunk_types = deployment_stats.get('chunk_types', 0)
        if chunk_types < 4:
            verification_result['warnings'].append(
                f"Only {chunk_types} chunk types, expected at least 4"
            )
        
        return verification_result
    
    def generate_deployment_report(self, verification_result: Dict[str, Any]) -> str:
        """Generate human-readable deployment report"""
        report = f"""
# Vector Database Deployment Report

**Status**: {'SUCCESS' if verification_result['success'] else 'FAILED'}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Metrics
- Total Vectors: {verification_result['metrics'].get('total_vectors', 0)}
- Embedding Dimension: {verification_result['metrics'].get('embedding_dimension', 'N/A')}
- Schemes Covered: {verification_result['metrics'].get('schemes_covered', 0)}
- Chunk Types: {verification_result['metrics'].get('chunk_types', 0)}
- Last Updated: {verification_result['metrics'].get('last_updated', 'N/A')}

## Issues
"""
        
        if verification_result['errors']:
            report += "### Errors:\n"
            for error in verification_result['errors']:
                report += f"- {error}\n"
        
        if verification_result['warnings']:
            report += "\n### Warnings:\n"
            for warning in verification_result['warnings']:
                report += f"- {warning}\n"
        
        if not verification_result['errors'] and not verification_result['warnings']:
            report += "No issues detected. Deployment successful!\n"
        
        return report
```

## Phase 6: Monitoring & Alerting

### 6.1 Pipeline Monitoring
```python
# scripts/pipeline_monitor.py
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

class PipelineMonitor:
    """Monitors pipeline health and performance"""
    
    def __init__(self, log_file: str = "pipeline_logs.json"):
        self.log_file = log_file
        
    def log_pipeline_event(self, event_type: str, details: Dict[str, Any]):
        """Log a pipeline event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        }
        
        # Append to log file
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logging.error(f"Failed to log event: {str(e)}")
    
    def get_pipeline_health(self) -> Dict[str, Any]:
        """Get overall pipeline health status"""
        try:
            events = self._load_recent_events(days=7)
            
            health_status = {
                'overall_health': 'healthy',
                'last_run': None,
                'success_rate': 0,
                'error_count': 0,
                'warning_count': 0,
                'recent_events': len(events)
            }
            
            if events:
                # Calculate success rate
                successful_runs = len([e for e in events if e['event_type'] == 'pipeline_success'])
                total_runs = len([e for e in events if e['event_type'].startswith('pipeline_')])
                health_status['success_rate'] = (successful_runs / total_runs * 100) if total_runs > 0 else 0
                
                # Count errors and warnings
                health_status['error_count'] = len([e for e in events if e['event_type'] == 'pipeline_error'])
                health_status['warning_count'] = len([e for e in events if e['event_type'] == 'pipeline_warning'])
                
                # Get last run time
                health_status['last_run'] = events[-1]['timestamp']
                
                # Determine overall health
                if health_status['success_rate'] < 80:
                    health_status['overall_health'] = 'unhealthy'
                elif health_status['success_rate'] < 95:
                    health_status['overall_health'] = 'degraded'
            
            return health_status
            
        except Exception as e:
            logging.error(f"Failed to get pipeline health: {str(e)}")
            return {'overall_health': 'unknown', 'error': str(e)}
    
    def _load_recent_events(self, days: int = 7) -> List[Dict]:
        """Load recent events from log file"""
        events = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        event_time = datetime.fromisoformat(event['timestamp'])
                        if event_time >= cutoff_date:
                            events.append(event)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        
        return events
```

## Phase 7: Configuration Management

### 7.1 Pipeline Configuration
```yaml
# config/pipeline_config.yaml
pipeline:
  chunking:
    max_chunk_size: 2000
    min_chunk_size: 50
    chunk_types:
      - basic_info
      - performance
      - cost_analysis
      - risk_assessment
      - investment_details
      - historical_context
  
  embeddings:
    model: "BAAI/bge-small-en-v1.5"
    dimensions: 384
    batch_size: 32
    normalize_embeddings: true
  
  vector_store:
    index_path: "faiss_index.bin"
    metadata_path: "metadata_store.json"
    index_type: "IndexFlatL2"
  
  validation:
    min_total_vectors: 20
    min_schemes_covered: 4
    min_chunk_types: 4
  
  monitoring:
    log_retention_days: 30
    health_check_interval: 3600  # seconds

schemes:
  - "ICICI Prudential Dynamic Plan Direct Growth"
  - "ICICI Prudential Large Cap Fund Direct Growth"
  - "ICICI Prudential Nifty Next 50 Index Fund Direct Growth"
  - "ICICI Prudential Top 100 Fund Direct Growth"

data_sources:
  base_urls:
    - "https://groww.in/mutual-funds/icici-prudential-dynamic-plan-direct-growth"
    - "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth"
    - "https://groww.in/mutual-funds/icici-prudential-nifty-next-50-index-fund-direct-growth"
    - "https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth"
```

## Summary

This architecture provides a comprehensive, automated pipeline for:

1. **Data Validation**: Ensures scraped data quality and completeness
2. **Intelligent Chunking**: Creates semantic chunks optimized for retrieval
3. **Embedding Generation**: Produces high-quality embeddings using OpenAI
4. **Vector Store Management**: Maintains FAISS index with metadata
5. **Quality Control**: Validates embeddings and index integrity
6. **Monitoring**: Tracks pipeline health and performance
7. **GitHub Actions Integration**: Automates the entire workflow

The pipeline runs automatically when new data is scraped, ensuring the RAG system always has the latest, high-quality embeddings for accurate user responses.
