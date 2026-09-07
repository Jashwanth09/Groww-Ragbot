"""
Phase 1.2.3: Text Normalization
Converts collected sources into clean, structured text suitable for embedding
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'text_normalizer.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TextNormalizer:
    """Normalizes text content for embedding generation"""
    
    def __init__(self):
        """Initialize the text normalizer"""
        self.scheme_name_mappings = self._initialize_scheme_mappings()
        self.abbreviation_mappings = self._initialize_abbreviation_mappings()
        self.date_patterns = self._initialize_date_patterns()
        
    def _initialize_scheme_mappings(self) -> Dict[str, str]:
        """Initialize scheme name standardization mappings"""
        return {
            # Variations of ICICI Prudential Large Cap Fund
            "icici pru large cap fund": "ICICI Prudential Large Cap Fund Direct Growth",
            "icici prudential large cap fund": "ICICI Prudential Large Cap Fund Direct Growth",
            
            # Variations of ICICI Prudential Dynamic Plan
            "icici pru dynamic plan": "ICICI Prudential Dynamic Plan Direct Growth",
            "icici prudential dynamic plan": "ICICI Prudential Dynamic Plan Direct Growth",
            
            # Variations of ICICI Prudential Nifty Next 50 Index Fund
            "icici pru nifty next 50 index fund": "ICICI Prudential Nifty Next 50 Index Fund Direct Growth",
            "icici prudential nifty next 50 index fund": "ICICI Prudential Nifty Next 50 Index Fund Direct Growth",
            
            # Variations of ICICI Prudential Top 100 Fund
            "icici pru top 100 fund": "ICICI Prudential Top 100 Fund Direct Growth",
            "icici prudential top 100 fund": "ICICI Prudential Top 100 Fund Direct Growth"
        }
    
    def _initialize_abbreviation_mappings(self) -> Dict[str, str]:
        """Initialize abbreviation handling mappings"""
        return {
            "TER": "Total Expense Ratio",
            "AUM": "Assets Under Management",
            "NAV": "Net Asset Value",
            "SIP": "Systematic Investment Plan",
            "KIM": "Key Information Memorandum",
            "SID": "Scheme Information Document",
            "TRI": "Total Return Index",
            "Crisil": "CRISIL",
            "Moody's": "Moody's",
            "AMFI": "Association of Mutual Funds in India",
            "SEBI": "Securities and Exchange Board of India",
            "PMS": "Portfolio Management Service",
            "AIF": "Alternative Investment Fund",
            "NFO": "New Fund Offer",
            "SWP": "Systematic Withdrawal Plan",
            "STP": "Systematic Transfer Plan"
        }
    
    def _initialize_date_patterns(self) -> List[Dict[str, str]]:
        """Initialize date conversion patterns"""
        return [
            {"pattern": r"(\w+)\s+(\d{4})", "format": "month_year"},  # March 2024
            {"pattern": r"(\d{1,2})/(\d{1,2})/(\d{4})", "format": "dd_mm_yyyy"},  # 15/03/2024
            {"pattern": r"(\d{4})-(\d{1,2})-(\d{1,2})", "format": "yyyy_mm_dd"},  # 2024-03-15
            {"pattern": r"(\d{1,2})-(\w+)-(\d{4})", "format": "dd_month_yyyy"},  # 15-March-2024
            {"pattern": r"(\w+)\s+(\d{1,2}),?\s+(\d{4})", "format": "month_dd_yyyy"}  # March 15, 2024
        ]
    
    def normalize_scheme_name(self, text: str) -> str:
        """
        Standardize scheme names
        
        Args:
            text: Input text containing scheme names
            
        Returns:
            Text with standardized scheme names
        """
        normalized_text = text.lower()
        
        # Apply scheme name mappings (sort by length to avoid partial matches)
        sorted_mappings = sorted(self.scheme_name_mappings.items(), key=lambda x: len(x[0]), reverse=True)
        
        for variation, standard_name in sorted_mappings:
            # Use word boundaries to avoid partial matches
            pattern = rf'\b{re.escape(variation)}\b'
            if re.search(pattern, normalized_text):
                normalized_text = re.sub(pattern, standard_name.lower(), normalized_text, flags=re.IGNORECASE)
        
        return normalized_text
    
    def normalize_numerical_formats(self, text: str) -> str:
        """
        Normalize numerical formats
        
        Args:
            text: Input text with numerical formats
            
        Returns:
            Text with normalized numerical formats
        """
        # Convert currency formats (remove commas, currency symbols)
        # Pattern: Rs. 5,000 or 5,000 or $5,000 or 5,000.00
        currency_patterns = [
            r"Rs?\s*([\d,]+\.?\d*)",
            r"\$([\d,]+\.?\d*)",
            r"([\d,]+\.?\d*)\s*(?:Rs?|INR|USD)?"
        ]
        
        for pattern in currency_patterns:
            text = re.sub(pattern, lambda m: m.group(1).replace(',', ''), text)
        
        # Handle percentage formats (0.42% -> 0.42)
        text = re.sub(r"([\d.]+)%", r"\1", text)
        
        # Handle crore/lakh/thousand formats
        text = re.sub(r"([\d.]+)\s*Cr", r"\1 crore", text, flags=re.IGNORECASE)
        text = re.sub(r"([\d.]+)\s*Lakh", r"\1 lakh", text, flags=re.IGNORECASE)
        text = re.sub(r"([\d.]+)\s*Thousand", r"\1 thousand", text, flags=re.IGNORECASE)
        
        return text
    
    def normalize_dates(self, text: str) -> str:
        """
        Convert dates to ISO format
        
        Args:
            text: Input text with various date formats
            
        Returns:
            Text with ISO format dates
        """
        month_mapping = {
            "january": "01", "february": "02", "march": "03", "april": "04",
            "may": "05", "june": "06", "july": "07", "august": "08",
            "september": "09", "october": "10", "november": "11", "december": "12",
            "jan": "01", "feb": "02", "mar": "03", "apr": "04",
            "may": "05", "jun": "06", "jul": "07", "aug": "08",
            "sep": "09", "oct": "10", "nov": "11", "dec": "12"
        }
        
        # Pattern: March 2024 -> 2024-03
        def convert_month_year(match):
            month = match.group(1).lower()
            year = match.group(2)
            month_num = month_mapping.get(month, month)
            return f"{year}-{month_num}"
        
        text = re.sub(r"\b(\w+)\s+(\d{4})\b", convert_month_year, text, flags=re.IGNORECASE)
        
        # Pattern: dd/mm/yyyy -> yyyy-mm-dd
        def convert_dd_mm_yyyy(match):
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = match.group(3)
            return f"{year}-{month}-{day}"
        
        text = re.sub(r"(\d{1,2})/(\d{1,2})/(\d{4})", convert_dd_mm_yyyy, text)
        
        # Pattern: dd-Month-yyyy -> yyyy-mm-dd
        def convert_dd_month_yyyy(match):
            day = match.group(1).zfill(2)
            month = match.group(2).lower()
            year = match.group(3)
            month_num = month_mapping.get(month, month)
            return f"{year}-{month_num}-{day}"
        
        text = re.sub(r"(\d{1,2})-(\w+)-(\d{4})", convert_dd_month_yyyy, text, flags=re.IGNORECASE)
        
        return text
    
    def handle_abbreviations(self, text: str) -> str:
        """
        Handle abbreviations consistently
        
        Args:
            text: Input text with abbreviations
            
        Returns:
            Text with expanded abbreviations (first occurrence only)
        """
        # Keep track of expanded abbreviations to avoid repetition
        expanded = set()
        
        def expand_abbreviation(match):
            abbr = match.group(0)
            if abbr.upper() in self.abbreviation_mappings and abbr.upper() not in expanded:
                expanded.add(abbr.upper())
                return f"{self.abbreviation_mappings[abbr.upper()]} ({abbr})"
            return match.group(0)
        
        # Find and expand abbreviations
        for abbr, full_form in self.abbreviation_mappings.items():
            pattern = rf"\b{re.escape(abbr)}\b"
            text = re.sub(pattern, expand_abbreviation, text, flags=re.IGNORECASE)
        
        return text
    
    def normalize_text(self, text: str) -> str:
        """
        Apply all normalization steps to text
        
        Args:
            text: Input text to normalize
            
        Returns:
            Fully normalized text
        """
        try:
            # Step 1: Normalize scheme names
            normalized = self.normalize_scheme_name(text)
            
            # Step 2: Normalize numerical formats
            normalized = self.normalize_numerical_formats(normalized)
            
            # Step 3: Normalize dates
            normalized = self.normalize_dates(normalized)
            
            # Step 4: Handle abbreviations
            normalized = self.handle_abbreviations(normalized)
            
            # Step 5: Clean up extra whitespace
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing text: {str(e)}")
            return text  # Return original text if normalization fails
    
    def normalize_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a single document
        
        Args:
            document: Document dictionary with text content
            
        Returns:
            Normalized document
        """
        try:
            normalized_doc = document.copy()
            
            if 'text' in document:
                normalized_doc['text'] = self.normalize_text(document['text'])
                normalized_doc['normalized'] = True
                normalized_doc['normalized_at'] = datetime.now().isoformat()
            
            if 'scheme' in document:
                normalized_doc['scheme'] = self.normalize_scheme_name(document['scheme'])
            
            return normalized_doc
            
        except Exception as e:
            logger.error(f"Error normalizing document: {str(e)}")
            return document
    
    def normalize_documents_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize a batch of documents
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            List of normalized documents
        """
        normalized_documents = []
        
        for i, doc in enumerate(documents):
            try:
                normalized_doc = self.normalize_document(doc)
                normalized_documents.append(normalized_doc)
                logger.info(f"Normalized document {i+1}/{len(documents)}")
            except Exception as e:
                logger.error(f"Failed to normalize document {i+1}: {str(e)}")
                normalized_documents.append(doc)  # Keep original on failure
        
        return normalized_documents
    
    def normalize_json_file(self, input_file: str, output_file: str) -> bool:
        """
        Normalize a JSON file containing documents
        
        Args:
            input_file: Path to input JSON file
            output_file: Path to output normalized JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Loading documents from {input_file}")
            
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if 'content' in data:
                # Structure like raw_documents files
                documents = data['content']
            elif isinstance(data, list):
                # Direct list of documents
                documents = data
            else:
                # Single document
                documents = [data]
            
            # Normalize documents
            normalized_documents = self.normalize_documents_batch(documents)
            
            # Update the structure
            if 'content' in data:
                data['content'] = normalized_documents
                data['normalized'] = True
                data['normalized_at'] = datetime.now().isoformat()
            elif isinstance(data, list):
                data = normalized_documents
            else:
                data = normalized_documents[0] if normalized_documents else data
            
            # Save normalized data
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Normalized documents saved to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error normalizing JSON file {input_file}: {str(e)}")
            return False
    
    def create_normalized_documents_structure(self, input_dir: str, output_dir: str) -> bool:
        """
        Create normalized documents structure as per architecture
        
        Args:
            input_dir: Directory containing raw documents
            output_dir: Directory to save normalized documents
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Creating normalized documents structure from {input_dir}")
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Process all JSON files in input directory
            json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
            
            for json_file in json_files:
                input_path = os.path.join(input_dir, json_file)
                output_path = os.path.join(output_dir, json_file)
                
                success = self.normalize_json_file(input_path, output_path)
                
                if success:
                    logger.info(f"Successfully normalized {json_file}")
                else:
                    logger.error(f"Failed to normalize {json_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating normalized documents structure: {str(e)}")
            return False


def main():
    """Main function for testing the text normalizer"""
    try:
        normalizer = TextNormalizer()
        
        # Test with sample text
        sample_text = """
        ICICI Pru Large Cap Fund has expense ratio of 0.42% as of March 2024.
        Minimum SIP is Rs. 5,000 and AUM is Rs. 15,234.56 Cr.
        NAV updated on 15/03/2024. TER includes all costs.
        """
        
        print("Original Text:")
        print(sample_text)
        print("\nNormalized Text:")
        print(normalizer.normalize_text(sample_text))
        
        # Test with actual documents
        input_dir = '../raw_documents'
        output_dir = '../normalized_documents'
        
        if os.path.exists(input_dir):
            success = normalizer.create_normalized_documents_structure(input_dir, output_dir)
            if success:
                print(f"\nNormalized documents created in {output_dir}")
            else:
                print("\nFailed to create normalized documents")
        else:
            print(f"\nInput directory {input_dir} not found")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
