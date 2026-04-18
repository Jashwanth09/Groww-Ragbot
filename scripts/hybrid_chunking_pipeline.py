"""
Hybrid Chunking Pipeline for Phase 1.3
Combines semantic section-based and fixed-size chunking with overlap
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridDocumentChunker:
    """Implements hybrid chunking strategy: semantic + fixed-size with overlap"""
    
    def __init__(self, raw_documents_dir: str = "../raw_documents"):
        self.raw_documents_dir = Path(raw_documents_dir)
        self.chunk_id_counter = 0
        
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
        
        # Target schemes
        self.target_schemes = [
            "ICICI Prudential Dynamic Plan Direct Growth",
            "ICICI Prudential Large Cap Fund Direct Growth",
            "ICICI Prudential Nifty Next 50 Index Fund Direct Growth",
            "ICICI Prudential Top 100 Fund Direct Growth"
        ]
        
        # Hybrid chunking parameters
        self.target_chunk_size = 400  # Smaller for better overlap
        self.chunk_overlap = 100      # 25% overlap
        self.min_chunk_size = 50      # Minimum viable chunk
    
    def load_documents(self) -> List[Dict]:
        """Load all processed documents from raw_documents directory"""
        documents = []
        
        if not self.raw_documents_dir.exists():
            logger.error(f"Directory {self.raw_documents_dir} not found")
            return documents
        
        for file_path in self.raw_documents_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'content' in data:
                        # Handle content that might be a list or string
                        content = data['content']
                        if isinstance(content, list):
                            content = '\n'.join(str(item) for item in content)
                        elif not isinstance(content, str):
                            content = str(content)
                        
                        documents.append({
                            'filename': file_path.stem,
                            'content': content,
                            'scheme': data.get('scheme', 'General'),
                            'content_type': data.get('content_type', 'unknown'),
                            'source_url': data.get('source_url', 'https://www.icicipruamc.com'),
                            'data_date': data.get('data_date', datetime.now().strftime('%Y-%m-%d'))
                        })
                        logger.info(f"Loaded document: {file_path.name}")
            except Exception as e:
                logger.error(f"Error loading {file_path}: {str(e)}")
        
        return documents
    
    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """Apply hybrid chunking strategy to all documents"""
        all_chunks = []
        
        for doc in documents:
            logger.info(f"Processing document: {doc['filename']}")
            
            # Determine chunking strategy based on document type
            if doc['content_type'] in ['factsheet', 'kim']:
                chunks = self._hybrid_structured_chunking(doc)
            else:
                chunks = self._hybrid_general_chunking(doc)
            
            all_chunks.extend(chunks)
            logger.info(f"Generated {len(chunks)} chunks from {doc['filename']}")
        
        return all_chunks
    
    def _hybrid_structured_chunking(self, doc: Dict) -> List[Dict]:
        """Hybrid chunking for structured documents (factsheets, KIM)"""
        chunks = []
        
        # Step 1: Split by semantic sections
        sections = self._split_by_sections(doc['content'])
        
        for section_title, section_content in sections:
            if not section_content.strip():
                continue
            
            # Step 2: Apply fixed-size chunking with overlap to each section
            section_chunks = self._chunk_with_overlap(
                section_content,
                section_title,
                doc['scheme'],
                doc['content_type'],
                doc['source_url'],
                doc['filename']
            )
            
            chunks.extend(section_chunks)
        
        return chunks
    
    def _hybrid_general_chunking(self, doc: Dict) -> List[Dict]:
        """Hybrid chunking for general documents"""
        chunks = []
        
        # Split into meaningful paragraphs
        paragraphs = self._split_into_paragraphs(doc['content'])
        
        # Group paragraphs into semantic units
        semantic_groups = self._group_paragraphs_semantically(paragraphs)
        
        for group_title, group_content in semantic_groups:
            # Apply fixed-size chunking with overlap
            group_chunks = self._chunk_with_overlap(
                group_content,
                group_title,
                doc['scheme'],
                doc['content_type'],
                doc['source_url'],
                doc['filename']
            )
            chunks.extend(group_chunks)
        
        return chunks
    
    def _split_by_sections(self, text: str) -> List[Tuple[str, str]]:
        """Split text by semantic section markers"""
        sections = []
        current_section = ""
        current_title = "Introduction"
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check if line is a section marker
            is_section_marker = False
            for marker in self.section_markers:
                if marker.lower() in line.lower():
                    # Save previous section
                    if current_section.strip():
                        sections.append((current_title, current_section.strip()))
                    
                    # Start new section
                    current_title = line
                    current_section = ""
                    is_section_marker = True
                    break
            
            if not is_section_marker:
                current_section += line + '\n'
        
        # Add last section
        if current_section.strip():
            sections.append((current_title, current_section.strip()))
        
        return sections
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into meaningful paragraphs"""
        paragraphs = []
        
        # Split by double newlines first
        sections = text.split('\n\n')
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Further split by single newlines if section is too long
            if len(section) > self.target_chunk_size * 2:
                lines = section.split('\n')
                for line in lines:
                    line = line.strip()
                    if line:
                        paragraphs.append(line)
            else:
                paragraphs.append(section)
        
        return paragraphs
    
    def _group_paragraphs_semantically(self, paragraphs: List[str]) -> List[Tuple[str, str]]:
        """Group paragraphs into semantic units"""
        groups = []
        current_group = []
        current_title = "General Information"
        
        for paragraph in paragraphs:
            # Check if paragraph starts a new semantic group
            new_group = False
            
            # Check for section markers
            for marker in self.section_markers:
                if marker.lower() in paragraph.lower()[:50]:
                    # Save previous group
                    if current_group:
                        group_content = '\n'.join(current_group)
                        groups.append((current_title, group_content))
                    
                    # Start new group
                    current_group = [paragraph]
                    current_title = paragraph
                    new_group = True
                    break
            
            if not new_group:
                current_group.append(paragraph)
                
                # Check if group is getting too large
                group_size = sum(len(p) for p in current_group)
                if group_size > self.target_chunk_size * 1.5:
                    # Save current group and start new one
                    group_content = '\n'.join(current_group)
                    groups.append((current_title, group_content))
                    current_group = []
                    current_title = "Additional Information"
        
        # Add last group
        if current_group:
            group_content = '\n'.join(current_group)
            groups.append((current_title, group_content))
        
        return groups
    
    def _chunk_with_overlap(self, content: str, section_title: str, scheme: str,
                           content_type: str, source_url: str, filename: str) -> List[Dict]:
        """Apply fixed-size chunking with overlap to content"""
        chunks = []
        
        # Clean and normalize content
        content = self._clean_text(content)
        
        if len(content) <= self.target_chunk_size:
            # Content is small enough for single chunk
            chunk = self._create_chunk_object(
                text=content,
                scheme_name=scheme,
                chunk_type=self._determine_chunk_type(section_title, content_type),
                source_url=source_url,
                filename=filename,
                section_title=section_title,
                chunk_index=0
            )
            chunks.append(chunk)
        else:
            # Apply sliding window chunking with overlap
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
                        text=chunk_text,
                        scheme_name=scheme,
                        chunk_type=self._determine_chunk_type(section_title, content_type),
                        source_url=source_url,
                        filename=filename,
                        section_title=section_title,
                        chunk_index=chunk_index
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Move start position with overlap
                start = end - self.chunk_overlap
                if start < 0:
                    start = 0
                
                # Prevent infinite loop
                if start >= len(content):
                    break
        
        return chunks
    
    def _find_sentence_boundary(self, text: str, preferred_end: int) -> int:
        """Find the best sentence boundary near preferred_end"""
        # Look for sentence endings near preferred_end
        search_range = min(50, len(text) - preferred_end)
        
        for i in range(preferred_end, min(preferred_end + search_range, len(text))):
            if text[i] in '.!?' and i + 1 < len(text) and text[i + 1] in ' \n\t':
                return i + 1
        
        # If no sentence boundary found, look for word boundary
        for i in range(preferred_end, max(preferred_end - 20, 0), -1):
            if text[i] in ' \n\t':
                return i
        
        # Fallback to preferred_end
        return preferred_end
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common encoding issues
        text = text.replace('â', ' ').replace('¬', ' ')
        
        # Remove excessive punctuation
        text = re.sub(r'[^\w\s\.\!\?\,\;\:\-\(\)\/\%\&\@]', '', text)
        
        return text.strip()
    
    def _determine_chunk_type(self, section_title: str, content_type: str) -> str:
        """Determine chunk type based on section title and content type"""
        title_lower = section_title.lower()
        
        if any(keyword in title_lower for keyword in ['objective', 'investment']):
            return 'fund_objective'
        elif any(keyword in title_lower for keyword in ['expense', 'ter', 'ratio']):
            return 'expense_ratio'
        elif any(keyword in title_lower for keyword in ['exit', 'load']):
            return 'exit_load'
        elif any(keyword in title_lower for keyword in ['minimum', 'sip', 'application']):
            return 'minimum_investment'
        elif any(keyword in title_lower for keyword in ['benchmark', 'index']):
            return 'benchmark'
        elif any(keyword in title_lower for keyword in ['risk', 'riskometer']):
            return 'risk_assessment'
        elif any(keyword in title_lower for keyword in ['asset', 'allocation', 'portfolio']):
            return 'asset_allocation'
        elif any(keyword in title_lower for keyword in ['holding', 'top']):
            return 'top_holdings'
        elif any(keyword in title_lower for keyword in ['performance', 'return']):
            return 'performance'
        elif any(keyword in title_lower for keyword in ['download', 'statement', 'capital gains']):
            return 'investor_services'
        elif any(keyword in title_lower for keyword in ['tax', 'taxation']):
            return 'taxation'
        else:
            return content_type
    
    def _create_chunk_object(self, text: str, scheme_name: str, chunk_type: str,
                            source_url: str, filename: str, section_title: str,
                            chunk_index: int) -> Dict:
        """Create a chunk object with metadata"""
        self.chunk_id_counter += 1
        
        # Generate short scheme name for chunk ID
        scheme_short = scheme_name.lower().replace(' ', '_').replace('icici_prudential_', '')
        chunk_id = f"{scheme_short}_{chunk_type}_{self.chunk_id_counter:03d}"
        
        # Calculate token count (rough estimation: 1 token ~ 4 characters)
        token_count = len(text) // 4
        
        return {
            "chunk_id": chunk_id,
            "text": text.strip(),
            "scheme_name": scheme_name,
            "chunk_type": chunk_type,
            "source_url": source_url,
            "filename": filename,
            "section_title": section_title,
            "chunk_index": chunk_index,
            "token_count": token_count,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().strftime('%Y-%m-%d'),
            "content_hash": hashlib.md5(text.encode()).hexdigest()[:8],
            "chunking_strategy": "hybrid_semantic_fixed_size",
            "chunk_size": len(text),
            "overlap_applied": self.chunk_overlap
        }
    
    def validate_chunks(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Validate chunk quality and completeness"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        required_fields = ['chunk_id', 'text', 'scheme_name', 'chunk_type', 'source_url']
        
        for index, chunk in enumerate(chunks):
            # Check required fields
            for field in required_fields:
                if field not in chunk or chunk[field] is None:
                    validation_result['errors'].append(f"Chunk {index}: Missing field '{field}'")
                elif isinstance(chunk[field], str) and not chunk[field].strip():
                    validation_result['errors'].append(f"Chunk {index}: Empty field '{field}'")
            
            # Validate text length
            if "text" in chunk:
                text_length = len(chunk["text"])
                if text_length < 10:
                    validation_result['errors'].append(f"Chunk {index}: Text too short ({text_length} chars)")
                elif text_length > 2000:
                    validation_result['warnings'].append(f"Chunk {index}: Text too long ({text_length} chars)")
        
        # Calculate statistics
        if chunks:
            text_lengths = [len(chunk["text"]) for chunk in chunks]
            validation_result['stats'] = {
                'total_chunks': len(chunks),
                'avg_chunk_size': sum(text_lengths) / len(text_lengths),
                'min_chunk_size': min(text_lengths),
                'max_chunk_size': max(text_lengths),
                'chunk_types': list(set(chunk['chunk_type'] for chunk in chunks)),
                'schemes_covered': list(set(chunk['scheme_name'] for chunk in chunks)),
                'overlap_chunks': len([c for c in chunks if c.get('overlap_applied')])
            }
        
        validation_result['valid'] = len(validation_result['errors']) == 0
        return validation_result
    
    def save_chunks(self, chunks: List[Dict], output_file: str = "chunked_documents.json"):
        """Save chunks to JSON file"""
        output_data = {
            "metadata": {
                "total_chunks": len(chunks),
                "created_at": datetime.now().isoformat(),
                "version": "2.0",
                "chunking_strategy": "hybrid_semantic_fixed_size",
                "target_chunk_size": self.target_chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "description": "Hybrid chunked documents for ICICI Prudential Mutual Fund RAG system"
            },
            "chunks": chunks
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(chunks)} chunks to {output_file}")
        return output_file

def main():
    """Main function to run hybrid chunking pipeline"""
    logger.info("Starting hybrid chunking pipeline...")
    
    # Initialize chunker
    chunker = HybridDocumentChunker()
    
    # Load documents
    documents = chunker.load_documents()
    if not documents:
        logger.error("No documents found. Run document_processor.py first.")
        return
    
    # Chunk documents
    chunks = chunker.chunk_documents(documents)
    
    # Validate chunks
    validation_result = chunker.validate_chunks(chunks)
    
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
    logger.info(f"Hybrid chunking completed successfully!")
    logger.info(f"Total chunks: {stats['total_chunks']}")
    logger.info(f"Average chunk size: {stats['avg_chunk_size']:.1f} chars")
    logger.info(f"Chunk types: {stats['chunk_types']}")
    logger.info(f"Schemes covered: {stats['schemes_covered']}")
    logger.info(f"Overlap chunks: {stats['overlap_chunks']}")
    
    # Save chunks
    output_file = chunker.save_chunks(chunks)
    logger.info(f"Chunks saved to: {output_file}")

if __name__ == "__main__":
    main()
