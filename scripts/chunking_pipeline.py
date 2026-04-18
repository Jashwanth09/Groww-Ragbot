"""
Chunking Pipeline for Phase 1.3
Implements semantic chunking strategy for document processing
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentChunker:
    """Implements semantic chunking strategy for RAG system"""
    
    def __init__(self, raw_documents_dir: str = "raw_documents"):
        self.raw_documents_dir = Path(raw_documents_dir)
        self.chunk_id_counter = 0
        
        # Section markers for semantic chunking
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
    
    def load_documents(self) -> List[Dict]:
        """Load all processed documents from raw_documents directory"""
        documents = []
        
        json_files = list(self.raw_documents_dir.glob("*.json"))
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
                    documents.append(doc_data)
                    logger.info(f"Loaded document: {json_file.name}")
            except Exception as e:
                logger.error(f"Error loading {json_file}: {str(e)}")
        
        return documents
    
    def create_chunks(self, documents: List[Dict]) -> List[Dict]:
        """Create semantic chunks from all documents"""
        all_chunks = []
        
        for document in documents:
            doc_chunks = self._chunk_document(document)
            all_chunks.extend(doc_chunks)
        
        logger.info(f"Created {len(all_chunks)} chunks from {len(documents)} documents")
        return all_chunks
    
    def _chunk_document(self, document: Dict) -> List[Dict]:
        """Chunk a single document"""
        chunks = []
        filename = document.get('filename', 'unknown')
        
        for content_section in document.get('content', []):
            text = content_section.get('text', '')
            scheme = content_section.get('scheme', 'General')
            content_type = content_section.get('content_type', 'general')
            source_url = content_section.get('source_url', '')
            
            # Create chunks based on content type
            if content_type in ['factsheet', 'kim']:
                section_chunks = self._chunk_structured_document(
                    text, scheme, content_type, source_url, filename
                )
            else:
                section_chunks = self._chunk_general_document(
                    text, scheme, content_type, source_url, filename
                )
            
            chunks.extend(section_chunks)
        
        return chunks
    
    def _chunk_structured_document(self, text: str, scheme: str, content_type: str, 
                                 source_url: str, filename: str) -> List[Dict]:
        """Chunk structured documents (factsheets, KIM) by sections"""
        chunks = []
        
        # Split by section markers
        sections = self._split_by_sections(text)
        
        for section_title, section_content in sections:
            if not section_content.strip():
                continue
            
            # Further split if content is too long
            sub_chunks = self._split_long_content(section_content)
            
            for i, sub_chunk in enumerate(sub_chunks):
                chunk = self._create_chunk_object(
                    text=sub_chunk,
                    scheme_name=scheme,
                    chunk_type=self._determine_chunk_type(section_title, content_type),
                    source_url=source_url,
                    filename=filename,
                    section_title=section_title,
                    chunk_index=i
                )
                chunks.append(chunk)
        
        return chunks
    
    def _chunk_general_document(self, text: str, scheme: str, content_type: str,
                               source_url: str, filename: str) -> List[Dict]:
        """Chunk general documents by paragraphs and semantic boundaries"""
        chunks = []
        
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Check if adding this paragraph exceeds chunk size
            if len(current_chunk) + len(paragraph) > 800:  # Target ~800 chars
                if current_chunk:
                    chunk = self._create_chunk_object(
                        text=current_chunk,
                        scheme_name=scheme,
                        chunk_type=content_type,
                        source_url=source_url,
                        filename=filename,
                        section_title="General Content",
                        chunk_index=len(chunks)
                    )
                    chunks.append(chunk)
                    current_chunk = paragraph
                else:
                    # Single paragraph too long, split it
                    sub_chunks = self._split_long_content(paragraph)
                    for sub_chunk in sub_chunks:
                        chunk = self._create_chunk_object(
                            text=sub_chunk,
                            scheme_name=scheme,
                            chunk_type=content_type,
                            source_url=source_url,
                            filename=filename,
                            section_title="General Content",
                            chunk_index=len(chunks)
                        )
                        chunks.append(chunk)
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        # Add remaining content
        if current_chunk:
            chunk = self._create_chunk_object(
                text=current_chunk,
                scheme_name=scheme,
                chunk_type=content_type,
                source_url=source_url,
                filename=filename,
                section_title="General Content",
                chunk_index=len(chunks)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_by_sections(self, text: str) -> List[tuple]:
        """Split text by section markers"""
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
                current_section += line + "\n"
        
        # Add last section
        if current_section.strip():
            sections.append((current_title, current_section.strip()))
        
        return sections
    
    def _split_long_content(self, content: str, max_length: int = 800) -> List[str]:
        """Split long content into smaller chunks"""
        if len(content) <= max_length:
            return [content]
        
        chunks = []
        sentences = re.split(r'[.!?]+', content)
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _determine_chunk_type(self, section_title: str, content_type: str) -> str:
        """Determine chunk type based on section title and content type"""
        section_lower = section_title.lower()
        
        if any(keyword in section_lower for keyword in ['objective', 'investment']):
            return 'fund_objective'
        elif any(keyword in section_lower for keyword in ['expense', 'ter', 'ratio']):
            return 'expense_ratio'
        elif any(keyword in section_lower for keyword in ['exit load']):
            return 'exit_load'
        elif any(keyword in section_lower for keyword in ['minimum', 'sip', 'investment']):
            return 'minimum_investment'
        elif any(keyword in section_lower for keyword in ['benchmark']):
            return 'benchmark'
        elif any(keyword in section_lower for keyword in ['risk', 'riskometer']):
            return 'risk_assessment'
        elif any(keyword in section_lower for keyword in ['allocation', 'portfolio']):
            return 'asset_allocation'
        elif any(keyword in section_lower for keyword in ['holding']):
            return 'top_holdings'
        elif any(keyword in section_lower for keyword in ['performance', 'returns']):
            return 'performance'
        elif any(keyword in section_lower for keyword in ['download', 'statement', 'cas']):
            return 'download_guide'
        elif any(keyword in section_lower for keyword in ['tax', 'taxation']):
            return 'taxation'
        else:
            return content_type
    
    def _create_chunk_object(self, text: str, scheme_name: str, chunk_type: str,
                           source_url: str, filename: str, section_title: str,
                           chunk_index: int) -> Dict:
        """Create standardized chunk object"""
        self.chunk_id_counter += 1
        
        # Generate unique chunk ID
        scheme_short = scheme_name.replace("ICICI Prudential ", "").replace(" Direct Growth", "").lower().replace(" ", "_")
        chunk_id = f"{scheme_short}_{chunk_type}_{self.chunk_id_counter:03d}"
        
        # Estimate token count (1 token ~ 4 characters)
        token_count = len(text) // 4
        
        # Create chunk metadata
        chunk = {
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
            "content_hash": hashlib.md5(text.encode()).hexdigest()[:8]
        }
        
        return chunk
    
    def validate_chunks(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Validate chunks for quality and completeness"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": self._calculate_chunk_stats(chunks)
        }
        
        # Check each chunk
        for i, chunk in enumerate(chunks):
            errors = self._validate_single_chunk(chunk, i)
            validation_result["errors"].extend(errors)
        
        # Check for duplicates
        duplicates = self._find_duplicate_chunks(chunks)
        if duplicates:
            validation_result["warnings"].append(f"Found {len(duplicates)} potentially duplicate chunks")
        
        # Check scheme coverage
        schemes_covered = set(chunk["scheme_name"] for chunk in chunks)
        missing_schemes = set(self.target_schemes) - schemes_covered
        if missing_schemes:
            validation_result["warnings"].append(f"Missing data for schemes: {list(missing_schemes)}")
        
        validation_result["valid"] = len(validation_result["errors"]) == 0
        return validation_result
    
    def _validate_single_chunk(self, chunk: Dict, index: int) -> List[str]:
        """Validate individual chunk"""
        errors = []
        required_fields = [
            "chunk_id", "text", "scheme_name", "chunk_type", 
            "source_url", "token_count"
        ]
        
        for field in required_fields:
            if field not in chunk or chunk[field] is None:
                errors.append(f"Chunk {index}: Missing field '{field}'")
            elif isinstance(chunk[field], str) and not chunk[field].strip():
                errors.append(f"Chunk {index}: Empty field '{field}'")
        
        # Validate text length
        if "text" in chunk:
            text_length = len(chunk["text"])
            if text_length < 10:  # Further reduced for better chunking
                errors.append(f"Chunk {index}: Text too short ({text_length} chars)")
            elif text_length > 2000:
                errors.append(f"Chunk {index}: Text too long ({text_length} chars)")
        
        # Validate scheme name
        if "scheme_name" in chunk and chunk["scheme_name"] not in self.target_schemes + ["General"]:
            errors.append(f"Chunk {index}: Invalid scheme name '{chunk['scheme_name']}'")
        
        return errors
    
    def _find_duplicate_chunks(self, chunks: List[Dict]) -> List[int]:
        """Find potentially duplicate chunks"""
        seen_hashes = set()
        duplicates = []
        
        for i, chunk in enumerate(chunks):
            content_hash = chunk.get("content_hash", "")
            if content_hash in seen_hashes:
                duplicates.append(i)
            seen_hashes.add(content_hash)
        
        return duplicates
    
    def _calculate_chunk_stats(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Calculate chunk statistics"""
        if not chunks:
            return {"total_chunks": 0}
        
        token_counts = [chunk.get("token_count", 0) for chunk in chunks]
        chunk_types = [chunk.get("chunk_type", "") for chunk in chunks]
        schemes = [chunk.get("scheme_name", "") for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_token_count": sum(token_counts) / len(token_counts),
            "min_token_count": min(token_counts),
            "max_token_count": max(token_counts),
            "chunk_type_distribution": {
                chunk_type: chunk_types.count(chunk_type) 
                for chunk_type in set(chunk_types)
            },
            "scheme_distribution": {
                scheme: schemes.count(scheme) 
                for scheme in set(schemes)
            }
        }
    
    def save_chunks(self, chunks: List[Dict], output_file: str = "chunked_documents.json"):
        """Save chunks to JSON file"""
        output_data = {
            "metadata": {
                "total_chunks": len(chunks),
                "created_at": datetime.now().isoformat(),
                "version": "1.0",
                "description": "Chunked documents for ICICI Prudential Mutual Fund RAG system"
            },
            "chunks": chunks
        }
        
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(chunks)} chunks to {output_path}")
        return str(output_path)

def main():
    """Main function to run the chunking pipeline"""
    # Initialize chunker
    chunker = DocumentChunker()
    
    # Load documents
    logger.info("Loading documents...")
    documents = chunker.load_documents()
    
    if not documents:
        logger.error("No documents found. Run document_processor.py first.")
        return
    
    # Create chunks
    logger.info("Creating chunks...")
    chunks = chunker.create_chunks(documents)
    
    # Validate chunks
    logger.info("Validating chunks...")
    validation_result = chunker.validate_chunks(chunks)
    
    if validation_result["errors"]:
        logger.error("Validation errors found:")
        for error in validation_result["errors"]:
            logger.error(f"  - {error}")
        return
    
    if validation_result["warnings"]:
        logger.warning("Validation warnings:")
        for warning in validation_result["warnings"]:
            logger.warning(f"  - {warning}")
    
    # Print statistics
    stats = validation_result["stats"]
    logger.info(f"Chunking completed successfully!")
    logger.info(f"Total chunks: {stats['total_chunks']}")
    logger.info(f"Average token count: {stats['avg_token_count']:.1f}")
    logger.info(f"Chunk types: {list(stats['chunk_type_distribution'].keys())}")
    
    # Save chunks
    output_file = chunker.save_chunks(chunks)
    logger.info(f"Chunks saved to: {output_file}")

if __name__ == "__main__":
    main()
