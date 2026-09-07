"""
Phase 1.3.1: Hybrid Chunking Strategy
Splits documents into semantically meaningful chunks for accurate retrieval
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import os
import sys
from dataclasses import dataclass
from collections import defaultdict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'hybrid_chunking.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class ChunkConfig:
    """Configuration for chunking parameters"""
    target_chunk_size: int = 400  # characters (optimal for BGE embeddings)
    chunk_overlap: int = 100      # 25% overlap for context preservation
    min_chunk_size: int = 50      # minimum viable chunk
    max_chunk_size: int = 800     # maximum chunk size to avoid overly long chunks
    
    # Special case handling configurations
    table_max_chunk_size: int = 600     # Maximum size for table chunks
    guide_step_overlap: int = 150        # Overlap for step-by-step guides
    factoid_merge_threshold: int = 100   # Threshold for merging short factoids
    long_section_threshold: int = 1200   # Threshold for sliding window approach
    sliding_window_size: int = 500       # Window size for long sections
    
    # Metadata preservation settings
    preserve_source_metadata: bool = True
    track_overlap_relationships: bool = True
    include_token_estimates: bool = True
    include_section_hierarchy: bool = True
    
    def __post_init__(self):
        """Validate configuration parameters"""
        self._validate_config()
    
    def _validate_config(self):
        """Validate chunking configuration parameters"""
        if self.min_chunk_size >= self.target_chunk_size:
            raise ValueError("min_chunk_size must be less than target_chunk_size")
        
        if self.target_chunk_size >= self.max_chunk_size:
            raise ValueError("target_chunk_size must be less than max_chunk_size")
        
        if self.chunk_overlap >= self.target_chunk_size:
            raise ValueError("chunk_overlap must be less than target_chunk_size")
        
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        
        # Validate overlap percentage (should be reasonable)
        overlap_percentage = (self.chunk_overlap / self.target_chunk_size) * 100
        if overlap_percentage > 50:
            logger.warning(f"High overlap percentage: {overlap_percentage:.1f}%")
        
        # Validate special case configurations
        if self.table_max_chunk_size > self.max_chunk_size:
            raise ValueError("table_max_chunk_size cannot exceed max_chunk_size")
        
        if self.guide_step_overlap < self.chunk_overlap:
            logger.warning("guide_step_overlap should be >= chunk_overlap for better context")
        
        logger.info(f"ChunkConfig validated: target={self.target_chunk_size}, "
                   f"overlap={self.chunk_overlap}, min={self.min_chunk_size}, max={self.max_chunk_size}")

class HybridChunker:
    """Implements hybrid chunking strategy combining semantic and fixed-size approaches"""
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        """
        Initialize the hybrid chunker
        
        Args:
            config: Chunking configuration parameters
        """
        self.config = config or ChunkConfig()
        self.section_markers = self._initialize_section_markers()
        self.sentence_endings = self._initialize_sentence_patterns()
        
    def _initialize_section_markers(self) -> List[str]:
        """Initialize semantic section markers for mutual fund content"""
        return [
            # Fund information
            "fund objective", "investment objective", "objective",
            "fund overview", "about the fund", "fund details",
            
            # Financial metrics
            "expense ratio", "total expense ratio", "ter",
            "exit load", "exit load structure", "exit load policy",
            "minimum investment", "minimum sip", "minimum application",
            "nav", "net asset value", "current nav",
            
            # Performance and benchmark
            "benchmark", "benchmark index", "benchmark performance",
            "performance", "returns", "historical returns",
            "1 year", "3 year", "5 year", "since inception",
            
            # Risk and allocation
            "riskometer", "risk profile", "risk factors", "risk level",
            "asset allocation", "portfolio allocation", "portfolio composition",
            
            # Holdings and management
            "top holdings", "portfolio", "holdings", "sector allocation",
            "fund manager", "fund management", "investment team",
            
            # Operational details
            "launch date", "inception date", "fund inception",
            "fund size", "aum", "assets under management",
            "fund category", "fund type", "fund house",
            
            # Processes and procedures
            "how to download", "download statement", "capital gains",
            "statement download", "account statement", "tax statement",
            "redemption", "withdrawal", "switching",
            
            # Regulatory and compliance
            "taxation", "tax", "tax implications",
            "regulatory", "compliance", "disclosure",
            
            # Contact and support
            "contact", "support", "customer care", "investor services"
        ]
    
    def _initialize_sentence_patterns(self) -> List[str]:
        """Initialize sentence ending patterns"""
        return [
            r'[.!?]+\s+',      # Standard sentence endings
            r'[:;]\s+',        # Colon and semicolon endings
            r'\n\s*',          # Newline endings
            r'\]\s*',          # List item endings
            r'\)\s*',          # Parenthesis endings
        ]
    
    def _detect_sentence_boundaries(self, text: str) -> List[int]:
        """
        Detect sentence boundaries in text
        
        Args:
            text: Input text
            
        Returns:
            List of character positions where sentences end
        """
        boundaries = []
        
        for pattern in self.sentence_endings:
            matches = re.finditer(pattern, text)
            for match in matches:
                boundaries.append(match.end())
        
        # Sort boundaries and remove duplicates
        boundaries = sorted(list(set(boundaries)))
        
        # Filter boundaries that are too close to each other
        filtered_boundaries = []
        min_distance = 20  # Minimum characters between boundaries
        
        for boundary in boundaries:
            if not filtered_boundaries or boundary - filtered_boundaries[-1] >= min_distance:
                filtered_boundaries.append(boundary)
        
        return filtered_boundaries
    
    def _split_by_semantic_sections(self, text: str) -> List[Tuple[str, str]]:
        """
        Split text by semantic section markers
        
        Args:
            text: Input text
            
        Returns:
            List of tuples (section_type, section_text)
        """
        sections = []
        
        # Create regex pattern for section markers
        marker_pattern = '|'.join([re.escape(marker) for marker in self.section_markers])
        pattern = rf'\b({marker_pattern})\b[:\s]*'
        
        # Find all section markers
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        
        if not matches:
            # No sections found, return entire text as 'general'
            return [("general", text)]
        
        for i, match in enumerate(matches):
            section_type = match.group(1).lower()
            start_pos = match.end()
            
            # Find end position (next section or end of text)
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)
            
            section_text = text[start_pos:end_pos].strip()
            
            if section_text and len(section_text) >= self.config.min_chunk_size:
                sections.append((section_type, section_text))
        
        return sections
    
    def _split_fixed_size_with_overlap(self, text: str) -> List[str]:
        """
        Split text into fixed-size chunks with overlap
        
        Args:
            text: Input text
            
        Returns:
            List of text chunks
        """
        chunks = []
        
        if len(text) <= self.config.target_chunk_size:
            return [text]
        
        # Get sentence boundaries for natural breaks
        sentence_boundaries = self._detect_sentence_boundaries(text)
        
        start_pos = 0
        chunk_id = 0
        
        while start_pos < len(text):
            # Calculate ideal end position
            ideal_end = start_pos + self.config.target_chunk_size
            
            if ideal_end >= len(text):
                # Last chunk
                chunks.append(text[start_pos:].strip())
                break
            
            # Find best break point near ideal end
            best_end = ideal_end
            
            # Try to break at sentence boundary
            for boundary in sentence_boundaries:
                if start_pos < boundary <= ideal_end:
                    best_end = boundary
                    break
            
            # If no sentence boundary found, try to break at word boundary
            if best_end == ideal_end:
                # Find last space before ideal_end
                last_space = text.rfind(' ', start_pos, ideal_end)
                if last_space > start_pos:
                    best_end = last_space
            
            # Extract chunk
            chunk = text[start_pos:best_end].strip()
            
            if len(chunk) >= self.config.min_chunk_size:
                chunks.append(chunk)
                chunk_id += 1
            
            # Move to next position with overlap
            start_pos = max(start_pos + 1, best_end - self.config.chunk_overlap)
        
        return chunks
    
    def _create_chunk_metadata(self, chunk_text: str, section_type: str, 
                            source_doc: Dict[str, Any], chunk_index: int, 
                            total_chunks: int, special_case: Optional[str] = None) -> Dict[str, Any]:
        """
        Create enhanced metadata for a chunk per Phase 1.3.3 requirements
        
        Args:
            chunk_text: The chunk text
            section_type: Type of section the chunk belongs to
            source_doc: Source document metadata
            chunk_index: Index of this chunk in the section
            total_chunks: Total number of chunks in the section
            special_case: Type of special case handling applied
            
        Returns:
            Enhanced chunk metadata dictionary
        """
        # Core metadata schema per Phase 1.3.3
        base_metadata = {
            "chunk_id": f"{source_doc.get('filename', 'unknown')}_{section_type}_{chunk_index:03d}",
            "text": chunk_text,
            "scheme": source_doc.get('scheme', 'unknown'),
            "section_type": section_type,
            "source_url": source_doc.get('source_url', ''),
            "source_type": source_doc.get('content_type', 'unknown'),
            "last_updated": self._extract_last_updated_date(chunk_text, source_doc),
            "token_count": self._enhanced_token_estimation(chunk_text)
        }
        
        # Enhanced metadata preservation based on configuration
        if self.config.preserve_source_metadata:
            base_metadata.update({
                "source_filename": source_doc.get('filename', 'unknown'),
                "source_normalized": source_doc.get('normalized', False),
                "source_normalized_at": source_doc.get('normalized_at', None)
            })
        
        # Chunk processing metadata
        base_metadata.update({
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "character_count": len(chunk_text),
            "created_at": datetime.now().isoformat(),
            "chunking_method": "hybrid",
            "special_case": special_case
        })
        
        # Overlap relationship tracking
        if self.config.track_overlap_relationships:
            base_metadata.update({
                "overlap_used": self.config.chunk_overlap > 0,
                "overlap_size": self.config.chunk_overlap if self.config.chunk_overlap > 0 else 0,
                "has_overlap_with_previous": chunk_index > 0,
                "has_overlap_with_next": chunk_index < total_chunks - 1,
                "previous_chunk_id": f"{source_doc.get('filename', 'unknown')}_{section_type}_{chunk_index-1:03d}" if chunk_index > 0 else None,
                "next_chunk_id": f"{source_doc.get('filename', 'unknown')}_{section_type}_{chunk_index+1:03d}" if chunk_index < total_chunks - 1 else None
            })
        
        # Section hierarchy information
        if self.config.include_section_hierarchy:
            base_metadata.update({
                "section_priority": self._get_section_priority(section_type),
                "section_category": self._get_section_category(section_type),
                "is_table_content": special_case == "table_chunking",
                "is_step_guide": special_case == "step_by_step_guide",
                "is_short_factoid": special_case == "short_factoids",
                "is_long_section": special_case == "long_section"
            })
        
        # Quality metrics and validation
        base_metadata.update({
            "quality_metrics": self._calculate_quality_metrics(chunk_text, section_type),
            "validation_status": self._validate_chunk_content(chunk_text, section_type)
        })
        
        # Special case specific metadata
        if special_case:
            base_metadata.update({
                "special_case_config": self._get_special_case_config(special_case)
            })
        
        # Performance analytics
        base_metadata.update({
            "processing_info": {
                "token_estimate_method": "enhanced_word_count",
                "date_extraction_method": "pattern_matching",
                "quality_score": self._calculate_quality_score(chunk_text, section_type)
            }
        })
        
        return base_metadata
    
    def _extract_last_updated_date(self, chunk_text: str, source_doc: Dict[str, Any]) -> str:
        """
        Extract last updated date from chunk text or source document
        
        Args:
            chunk_text: The chunk text
            source_doc: Source document metadata
            
        Returns:
            ISO format date string or default
        """
        # Try to extract date from chunk text first
        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',           # YYYY-MM-DD
            r'(\d{1,2})/(\d{1,2})/(\d{4})',        # DD/MM/YYYY or MM/DD/YYYY
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',      # March 15, 2024
            r'(\w+)\s+(\d{4})',                    # March 2024
            r'as of\s+(\w+\s+\d{1,2},?\s+\d{4})',  # as of March 15, 2024
            r'as of\s+(\w+\s+\d{4})',              # as of March 2024
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, chunk_text, re.IGNORECASE)
            if matches:
                match = matches[0]
                if len(match) == 3:
                    # Full date
                    if pattern == r'(\d{4})-(\d{2})-(\d{2})':
                        return f"{match[0]}-{match[1]}-{match[2]}"
                    elif pattern == r'(\d{1,2})/(\d{1,2})/(\d{4})':
                        return f"{match[2]}-{match[1].zfill(2)}-{match[0].zfill(2)}"
                    elif pattern in [r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', r'as of\s+(\w+\s+\d{1,2},?\s+\d{4})']:
                        month_map = {
                            'january': '01', 'february': '02', 'march': '03', 'april': '04',
                            'may': '05', 'june': '06', 'july': '07', 'august': '08',
                            'september': '09', 'october': '10', 'november': '11', 'december': '12',
                            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
                        }
                        month = match[0].lower()[:3]
                        if month in month_map:
                            return f"{match[2]}-{month_map[month]}-{match[1].zfill(2)}"
                elif len(match) == 2:
                    # Month and year only
                    month_map = {
                        'january': '01', 'february': '02', 'march': '03', 'april': '04',
                        'may': '05', 'june': '06', 'july': '07', 'august': '08',
                        'september': '09', 'october': '10', 'november': '11', 'december': '12',
                        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
                    }
                    month = match[0].lower()[:3]
                    if month in month_map:
                        return f"{match[1]}-{month_map[month]}-01"  # Default to 1st day
        
        # Try to get from source document
        if 'processed_at' in source_doc:
            try:
                processed_date = source_doc['processed_at']
                # Extract date part from ISO timestamp
                return processed_date.split('T')[0]
            except:
                pass
        
        # Default to current date
        return datetime.now().strftime('%Y-%m-%d')
    
    def _enhanced_token_estimation(self, text: str) -> int:
        """
        Enhanced token estimation using multiple methods for accuracy
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Method 1: Word-based estimation (more accurate for English)
        words = len(text.split())
        word_based_tokens = int(words * 1.3)  # Average token is ~0.77 words
        
        # Method 2: Character-based estimation (fallback)
        char_based_tokens = max(1, len(text) // 4)
        
        # Method 3: GPT-style estimation (consider punctuation and special chars)
        # Count tokens for common patterns
        special_patterns = {
            r'\d+': 1,           # Numbers
            r'\w+': 1,           # Words
            r'[^\w\s]': 1,       # Punctuation and symbols
            r'\s+': 0,           # Whitespace (don't count)
        }
        
        pattern_tokens = 0
        for pattern, token_count in special_patterns.items():
            matches = len(re.findall(pattern, text))
            if pattern != r'\s+':  # Don't count whitespace
                pattern_tokens += matches * token_count
        
        # Use the most reasonable estimate (weighted average)
        estimates = [word_based_tokens, char_based_tokens, pattern_tokens]
        
        # Remove outliers (more than 2x difference from median)
        median_est = sorted(estimates)[1]
        filtered_estimates = [e for e in estimates if abs(e - median_est) <= median_est]
        
        if filtered_estimates:
            final_estimate = int(sum(filtered_estimates) / len(filtered_estimates))
        else:
            final_estimate = median_est
        
        # Ensure minimum of 1 token
        return max(1, final_estimate)
    
    def _calculate_quality_metrics(self, text: str, section_type: str) -> Dict[str, Any]:
        """
        Calculate quality metrics for the chunk
        
        Args:
            text: Chunk text
            section_type: Type of section
            
        Returns:
            Quality metrics dictionary
        """
        # Text quality metrics
        sentences = len(re.findall(r'[.!?]+', text))
        words = len(text.split())
        avg_words_per_sentence = words / max(1, sentences)
        
        # Content completeness
        has_numbers = bool(re.search(r'\d+', text))
        has_percentages = bool(re.search(r'\d+\.?\d*%', text))
        has_dates = bool(re.search(r'\d{4}|\w+\s+\d{1,2},?\s+\d{4}', text))
        
        # Section-specific quality indicators
        section_quality = self._get_section_quality_indicators(text, section_type)
        
        return {
            "sentence_count": sentences,
            "word_count": words,
            "avg_words_per_sentence": round(avg_words_per_sentence, 2),
            "has_numerical_data": has_numbers,
            "has_percentages": has_percentages,
            "has_dates": has_dates,
            "text_density": round(len(text) / max(1, words), 2),
            "section_quality": section_quality
        }
    
    def _get_section_quality_indicators(self, text: str, section_type: str) -> Dict[str, bool]:
        """Get section-specific quality indicators"""
        indicators = {}
        
        if section_type in ["expense ratio", "total expense ratio", "ter"]:
            indicators["has_percentage_value"] = bool(re.search(r'\d+\.?\d*%', text))
            indicators["has_ter_mention"] = bool(re.search(r'ter|total expense ratio', text, re.IGNORECASE))
        
        elif section_type in ["minimum investment", "minimum sip", "minimum application"]:
            indicators["has_amount"] = bool(re.search(r'rs\.?\s*\d+|^\d+', text, re.IGNORECASE))
            indicators["has_sip_mention"] = bool(re.search(r'sip|systematic', text, re.IGNORECASE))
        
        elif section_type in ["nav", "net asset value"]:
            indicators["has_nav_value"] = bool(re.search(r'nav|net asset value', text, re.IGNORECASE))
            indicators["has_date"] = bool(re.search(r'\d{4}|\w+\s+\d{1,2}', text))
        
        elif section_type in ["performance", "returns"]:
            indicators["has_return_values"] = bool(re.search(r'\d+\.?\d*%', text))
            indicators["has_time_periods"] = bool(re.search(r'1\s*year|3\s*year|5\s*year|since inception', text, re.IGNORECASE))
        
        elif section_type in ["top holdings", "portfolio"]:
            indicators["has_company_names"] = bool(re.search(r' ltd\.|limited|corporation|bank', text, re.IGNORECASE))
            indicators["has_percentages"] = bool(re.search(r'\d+\.?\d*%', text))
        
        return indicators
    
    def _validate_chunk_content(self, text: str, section_type: str) -> Dict[str, Any]:
        """
        Validate chunk content and return validation status
        
        Args:
            text: Chunk text
            section_type: Type of section
            
        Returns:
            Validation status dictionary
        """
        validation_errors = []
        validation_warnings = []
        
        # Basic validation
        if len(text) < self.config.min_chunk_size:
            validation_errors.append(f"Chunk too short: {len(text)} < {self.config.min_chunk_size}")
        
        if len(text) > self.config.max_chunk_size:
            validation_warnings.append(f"Chunk longer than recommended: {len(text)} > {self.config.max_chunk_size}")
        
        # Content validation
        if not text.strip():
            validation_errors.append("Chunk contains only whitespace")
        
        # Section-specific validation
        section_validation = self._validate_section_content(text, section_type)
        validation_errors.extend(section_validation["errors"])
        validation_warnings.extend(section_validation["warnings"])
        
        return {
            "is_valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "warnings": validation_warnings,
            "validation_score": max(0, 100 - (len(validation_errors) * 20) - (len(validation_warnings) * 5))
        }
    
    def _validate_section_content(self, text: str, section_type: str) -> Dict[str, List[str]]:
        """Validate section-specific content"""
        errors = []
        warnings = []
        
        if section_type in ["expense ratio", "total expense ratio", "ter"]:
            if not re.search(r'\d+\.?\d*%', text):
                warnings.append("No percentage value found in expense ratio section")
        
        elif section_type in ["minimum investment", "minimum sip", "minimum application"]:
            if not re.search(r'rs\.?\s*\d+|^\d+', text, re.IGNORECASE):
                warnings.append("No monetary amount found in minimum investment section")
        
        elif section_type in ["nav", "net asset value"]:
            if not re.search(r'nav|net asset value', text, re.IGNORECASE):
                errors.append("NAV section doesn't contain NAV terminology")
        
        elif section_type in ["performance", "returns"]:
            if not re.search(r'\d+\.?\d*%', text):
                warnings.append("No percentage returns found in performance section")
        
        return {"errors": errors, "warnings": warnings}
    
    def _calculate_quality_score(self, text: str, section_type: str) -> float:
        """
        Calculate overall quality score for the chunk
        
        Args:
            text: Chunk text
            section_type: Type of section
            
        Returns:
            Quality score (0-100)
        """
        score = 50.0  # Base score
        
        # Length appropriateness
        if self.config.min_chunk_size <= len(text) <= self.config.target_chunk_size:
            score += 20
        elif len(text) <= self.config.max_chunk_size:
            score += 10
        
        # Content richness
        if re.search(r'\d+', text):
            score += 10  # Has numbers
        if re.search(r'\d+\.?\d*%', text):
            score += 5   # Has percentages
        if re.search(r'\d{4}|\w+\s+\d{1,2}', text):
            score += 5   # Has dates
        
        # Sentence structure
        sentences = len(re.findall(r'[.!?]+', text))
        if sentences >= 1:
            score += 5
        if sentences >= 2:
            score += 5
        
        # Section-specific quality
        section_quality = self._get_section_quality_indicators(text, section_type)
        quality_indicators = sum(section_quality.values())
        score += min(10, quality_indicators * 2)
        
        return min(100.0, max(0.0, score))
    
    def _get_section_priority(self, section_type: str) -> int:
        """Get priority level for section type (lower = higher priority)"""
        priority_map = {
            "fund objective": 1, "investment objective": 1, "objective": 1,
            "expense ratio": 2, "total expense ratio": 2, "ter": 2,
            "minimum investment": 3, "minimum sip": 3, "minimum application": 3,
            "nav": 4, "net asset value": 4,
            "benchmark": 5, "benchmark index": 5,
            "riskometer": 6, "risk profile": 6,
            "performance": 7, "returns": 7,
            "top holdings": 8, "portfolio": 8,
            "asset allocation": 9, "portfolio allocation": 9,
            "how to download": 10, "download statement": 10,
            "general": 99
        }
        return priority_map.get(section_type.lower(), 50)
    
    def _get_section_category(self, section_type: str) -> str:
        """Get category for section type"""
        category_map = {
            "fund objective": "fund_info", "investment objective": "fund_info", "objective": "fund_info",
            "expense ratio": "financial", "total expense ratio": "financial", "ter": "financial",
            "minimum investment": "financial", "minimum sip": "financial", "minimum application": "financial",
            "nav": "financial", "net asset value": "financial",
            "benchmark": "performance", "benchmark index": "performance",
            "performance": "performance", "returns": "performance",
            "riskometer": "risk", "risk profile": "risk", "risk factors": "risk",
            "top holdings": "holdings", "portfolio": "holdings",
            "asset allocation": "allocation", "portfolio allocation": "allocation",
            "how to download": "process", "download statement": "process", "statement download": "process",
            "capital gains": "process", "taxation": "process",
            "fund manager": "management", "launch date": "management",
            "contact": "support", "support": "support", "customer care": "support",
            "general": "general"
        }
        return category_map.get(section_type.lower(), "general")
    
    def _get_special_case_config(self, special_case: str) -> Dict[str, Any]:
        """Get configuration details for special case handling"""
        config_map = {
            "table_chunking": {
                "max_size": self.config.table_max_chunk_size,
                "preservation_strategy": "single_chunk_when_possible"
            },
            "step_by_step_guide": {
                "overlap": self.config.guide_step_overlap,
                "preservation_strategy": "step_boundary_preservation"
            },
            "short_factoids": {
                "threshold": self.config.factoid_merge_threshold,
                "preservation_strategy": "merge_with_related"
            },
            "long_section": {
                "threshold": self.config.long_section_threshold,
                "window_size": self.config.sliding_window_size,
                "preservation_strategy": "sliding_window"
            }
        }
        return config_map.get(special_case, {})
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation)
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Rough estimation: 1 token ~ 4 characters for English
        return max(1, len(text) // 4)
    
    def _handle_special_cases(self, section_type: str, text: str) -> List[str]:
        """
        Handle special cases for different section types per Phase 1.3.2 requirements
        
        Args:
            section_type: Type of section
            text: Section text
            
        Returns:
            List of processed chunks
        """
        # Tables (expense ratio breakdown): Keep within single chunk if possible
        if section_type in ["expense ratio", "asset allocation", "top holdings", "portfolio allocation"]:
            return self._handle_table_chunking(text, section_type)
        
        # Step-by-step guides (download statements): Split with overlap to preserve steps
        elif section_type in ["how to download", "download statement", "statement download", "capital gains"]:
            return self._handle_step_by_step_guide(text, section_type)
        
        # Short factoids (minimum SIP amount): Merge with related content
        elif section_type in ["minimum investment", "minimum sip", "minimum application"]:
            return self._handle_short_factoids(text, section_type)
        
        # Long sections: Apply sliding window with overlap
        elif len(text) > self.config.long_section_threshold:
            return self._handle_long_section(text, section_type)
        
        # Default: standard chunking
        return self._split_fixed_size_with_overlap(text)
    
    def _handle_table_chunking(self, text: str, section_type: str) -> List[str]:
        """
        Handle table content - keep within single chunk if possible
        
        Args:
            text: Table content
            section_type: Type of section
            
        Returns:
            List of chunks
        """
        # Detect if content looks like a table (contains multiple lines with similar structure)
        lines = text.split('\n')
        table_indicators = ['%', 'cr', 'lakh', 'rs.', '-', '|', '1.', '2.', '3.']
        
        is_table = any(
            any(indicator.lower() in line.lower() for indicator in table_indicators)
            for line in lines if line.strip()
        )
        
        if is_table and len(text) <= self.config.table_max_chunk_size:
            logger.info(f"Keeping table content in single chunk: {section_type} ({len(text)} chars)")
            return [text]
        elif is_table and len(text) > self.config.table_max_chunk_size:
            logger.warning(f"Large table content ({len(text)} chars) will be split")
            # For large tables, split at logical boundaries
            return self._split_table_content(text)
        else:
            # Not clearly a table, use standard chunking
            return self._split_fixed_size_with_overlap(text)
    
    def _split_table_content(self, text: str) -> List[str]:
        """Split table content at logical boundaries"""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for line in lines:
            line_length = len(line)
            
            # If adding this line exceeds table_max_chunk_size and we have content, start new chunk
            if current_length + line_length > self.config.table_max_chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]  # Start new chunk with overlap
                current_length = line_length
            else:
                current_chunk.append(line)
                current_length += line_length
        
        # Add remaining content
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def _handle_step_by_step_guide(self, text: str, section_type: str) -> List[str]:
        """
        Handle step-by-step guides with enhanced overlap to preserve steps
        
        Args:
            text: Guide content
            section_type: Type of section
            
        Returns:
            List of chunks
        """
        logger.info(f"Processing step-by-step guide: {section_type}")
        
        # Detect step indicators
        step_patterns = [
            r'\b\d+\.\s+',      # "1. ", "2. ", etc.
            r'\bstep\s+\d+',     # "step 1", "step 2"
            r'\b[a-zA-Z]\)\s+',  # "a) ", "b) "
            r'\b-\s+',           # "- "
            r'\b\*\s+',          # "* "
        ]
        
        # Find step boundaries
        step_boundaries = []
        for pattern in step_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            step_boundaries.extend([match.start() for match in matches])
        
        step_boundaries = sorted(step_boundaries)
        
        if len(step_boundaries) <= 1:
            # No clear steps, use enhanced overlap chunking
            return self._split_with_enhanced_overlap(text, self.config.guide_step_overlap)
        
        # Create chunks based on steps with overlap
        chunks = []
        for i in range(len(step_boundaries)):
            start = step_boundaries[i]
            end = step_boundaries[i + 1] if i + 1 < len(step_boundaries) else len(text)
            
            chunk = text[start:end].strip()
            
            # Add overlap from previous step if available
            if i > 0 and len(chunks) > 0:
                overlap_start = max(0, start - self.config.guide_step_overlap)
                overlap_text = text[overlap_start:start].strip()
                chunk = overlap_text + '\n' + chunk if overlap_text else chunk
            
            if len(chunk) >= self.config.min_chunk_size:
                chunks.append(chunk)
        
        return chunks
    
    def _handle_short_factoids(self, text: str, section_type: str) -> List[str]:
        """
        Handle short factoids - merge with related content or mark for merging
        
        Args:
            text: Factoid content
            section_type: Type of section
            
        Returns:
            List of chunks
        """
        if len(text) >= self.config.factoid_merge_threshold:
            # Not a short factoid, use standard chunking
            return self._split_fixed_size_with_overlap(text)
        
        logger.info(f"Short factoid detected: {section_type} ({len(text)} chars)")
        
        # For very short content, try to merge with related information
        # Look for related keywords in the text
        related_keywords = {
            "minimum investment": ["sip", "lumpsum", "amount", "investment"],
            "minimum sip": ["systematic", "investment", "monthly", "amount"],
            "minimum application": ["lumpsum", "one-time", "investment", "amount"]
        }
        
        # Mark for potential merging (handled at document level)
        # For now, return as single chunk with special metadata
        return [text]
    
    def _handle_long_section(self, text: str, section_type: str) -> List[str]:
        """
        Handle long sections using sliding window approach
        
        Args:
            text: Long section content
            section_type: Type of section
            
        Returns:
            List of chunks
        """
        logger.info(f"Processing long section with sliding window: {section_type} ({len(text)} chars)")
        
        chunks = []
        window_size = self.config.sliding_window_size
        overlap = self.config.chunk_overlap
        
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + window_size, len(text))
            
            # Try to break at sentence boundary near end
            if end < len(text):
                sentence_boundaries = self._detect_sentence_boundaries(text[start:end + 50])
                if sentence_boundaries:
                    # Find last sentence boundary before end
                    for boundary in reversed(sentence_boundaries):
                        if boundary < window_size:
                            end = start + boundary
                            break
            
            chunk = text[start:end].strip()
            
            if len(chunk) >= self.config.min_chunk_size:
                chunks.append(chunk)
                chunk_index += 1
            
            # Move window with overlap
            start = max(start + 1, end - overlap)
        
        return chunks
    
    def _split_with_enhanced_overlap(self, text: str, overlap: int) -> List[str]:
        """
        Split text with enhanced overlap for special cases
        
        Args:
            text: Input text
            overlap: Enhanced overlap size
            
        Returns:
            List of chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.config.target_chunk_size, len(text))
            
            # Try to break at sentence boundary
            if end < len(text):
                sentence_boundaries = self._detect_sentence_boundaries(text[start:end + 50])
                if sentence_boundaries:
                    for boundary in reversed(sentence_boundaries):
                        if boundary < self.config.target_chunk_size:
                            end = start + boundary
                            break
            
            chunk = text[start:end].strip()
            
            if len(chunk) >= self.config.min_chunk_size:
                chunks.append(chunk)
            
            # Move with enhanced overlap
            start = max(start + 1, end - overlap)
        
        return chunks
    
    def chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk a single document using hybrid approach
        
        Args:
            document: Document dictionary with text content
            
        Returns:
            List of chunk dictionaries with metadata
        """
        chunks = []
        
        try:
            text = document.get('text', '')
            if not text or len(text.strip()) < self.config.min_chunk_size:
                logger.warning(f"Document too short or empty: {document.get('filename', 'unknown')}")
                return chunks
            
            # Step 1: Split by semantic sections
            sections = self._split_by_semantic_sections(text)
            
            logger.info(f"Document split into {len(sections)} semantic sections")
            
            # Step 2-4: Apply fixed-size chunking with overlap, break at sentences, preserve context
            for section_type, section_text in sections:
                # Handle special cases and track which method was used
                section_chunks = self._handle_special_cases(section_type, section_text)
                
                # Determine which special case was applied
                special_case = None
                if section_type in ["expense ratio", "asset allocation", "top holdings", "portfolio allocation"]:
                    special_case = "table_chunking"
                elif section_type in ["how to download", "download statement", "statement download", "capital gains"]:
                    special_case = "step_by_step_guide"
                elif section_type in ["minimum investment", "minimum sip", "minimum application"]:
                    if len(section_text) < self.config.factoid_merge_threshold:
                        special_case = "short_factoids"
                elif len(section_text) > self.config.long_section_threshold:
                    special_case = "long_section"
                
                # Create metadata for each chunk
                for i, chunk_text in enumerate(section_chunks):
                    if len(chunk_text.strip()) >= self.config.min_chunk_size:
                        metadata = self._create_chunk_metadata(
                            chunk_text.strip(), 
                            section_type, 
                            document, 
                            i, 
                            len(section_chunks),
                            special_case
                        )
                        chunks.append(metadata)
            
            logger.info(f"Created {len(chunks)} chunks from document")
            
        except Exception as e:
            logger.error(f"Error chunking document: {str(e)}")
        
        return chunks
    
    def chunk_documents_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunk multiple documents
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            List of all chunk dictionaries
        """
        all_chunks = []
        
        for i, document in enumerate(documents):
            try:
                doc_chunks = self.chunk_document(document)
                all_chunks.extend(doc_chunks)
                logger.info(f"Processed document {i+1}/{len(documents)}: {len(doc_chunks)} chunks")
            except Exception as e:
                logger.error(f"Failed to chunk document {i+1}: {str(e)}")
        
        return all_chunks
    
    def save_chunks_to_json(self, chunks: List[Dict[str, Any]], output_file: str) -> bool:
        """
        Save chunks to JSON file
        
        Args:
            chunks: List of chunk dictionaries
            output_file: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Create output structure
            output_data = {
                "metadata": {
                    "total_chunks": len(chunks),
                    "chunking_config": {
                        "target_chunk_size": self.config.target_chunk_size,
                        "chunk_overlap": self.config.chunk_overlap,
                        "min_chunk_size": self.config.min_chunk_size,
                        "max_chunk_size": self.config.max_chunk_size
                    },
                    "chunking_method": "hybrid",
                    "created_at": datetime.now().isoformat(),
                    "section_types_used": list(set(chunk["section_type"] for chunk in chunks))
                },
                "chunks": chunks
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(chunks)} chunks to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving chunks to {output_file}: {str(e)}")
            return False
    
    def create_chunked_documents_structure(self, input_dir: str, output_dir: str) -> bool:
        """
        Create chunked documents structure from normalized documents
        
        Args:
            input_dir: Directory containing normalized documents
            output_dir: Directory to save chunked documents
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Creating chunked documents from {input_dir}")
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Process all JSON files in input directory
            json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
            
            all_chunks = []
            
            for json_file in json_files:
                input_path = os.path.join(input_dir, json_file)
                
                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Extract documents from different JSON structures
                    documents = []
                    
                    if 'content' in data:
                        documents = data['content']
                    elif isinstance(data, list):
                        documents = data
                    else:
                        # Single document structure
                        documents = [data]
                    
                    # Chunk documents
                    doc_chunks = self.chunk_documents_batch(documents)
                    all_chunks.extend(doc_chunks)
                    
                    logger.info(f"Processed {json_file}: {len(doc_chunks)} chunks")
                    
                except Exception as e:
                    logger.error(f"Error processing {json_file}: {str(e)}")
            
            # Save all chunks to a single file
            output_file = os.path.join(output_dir, 'chunked_documents.json')
            success = self.save_chunks_to_json(all_chunks, output_file)
            
            if success:
                logger.info(f"Successfully created chunked documents: {len(all_chunks)} total chunks")
                return True
            else:
                logger.error("Failed to save chunked documents")
                return False
                
        except Exception as e:
            logger.error(f"Error creating chunked documents structure: {str(e)}")
            return False


def main():
    """Main function for testing the hybrid chunker"""
    try:
        # Initialize chunker with default config
        config = ChunkConfig()
        chunker = HybridChunker(config)
        
        # Test with sample document
        sample_doc = {
            "filename": "test_factsheet",
            "scheme": "ICICI Prudential Large Cap Fund Direct Growth",
            "content_type": "factsheet",
            "source_url": "https://www.icicipruamc.com/factsheet",
            "text": """
            Fund Objective: To generate long-term capital appreciation by investing in a diversified portfolio of large-cap companies. 
            Expense Ratio: 0.42% as of March 2024. 
            Exit Load: 1% if redeemed within 365 days, Nil thereafter. 
            Minimum Investment: SIP - 5000, Lumpsum - 5000. 
            Benchmark: Nifty 50 TRI. 
            Riskometer: High Risk. 
            Assets Under Management: 15234.56 crore as of March 2024. 
            Portfolio Allocation: Equity - 95.23%, Debt & Money Market - 4.77%. 
            Top Holdings: 1. Reliance Industries Ltd. - 8.45%, 2. HDFC Bank Ltd. - 7.23%. 
            Performance: 1 Year - 12.34%, 3 Year - 15.67%, 5 Year - 14.89%. 
            Fund Manager: Mr. S Naren. 
            Launch Date: January 1999.
            """
        }
        
        print("Testing hybrid chunking...")
        chunks = chunker.chunk_document(sample_doc)
        
        print(f"Created {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks):
            print(f"\nChunk {i+1}:")
            print(f"  Section: {chunk['section_type']}")
            print(f"  Length: {chunk['character_count']} chars")
            print(f"  Tokens: {chunk['token_count']}")
            print(f"  Preview: {chunk['text'][:100]}...")
        
        # Test with actual normalized documents
        input_dir = '../normalized_documents'
        output_dir = '../processed_data'
        
        if os.path.exists(input_dir):
            print(f"\nProcessing normalized documents from {input_dir}")
            success = chunker.create_chunked_documents_structure(input_dir, output_dir)
            
            if success:
                print(f"Chunked documents created in {output_dir}")
            else:
                print("Failed to create chunked documents")
        else:
            print(f"Input directory {input_dir} not found")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
