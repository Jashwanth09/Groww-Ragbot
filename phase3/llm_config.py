"""
LLM Configuration for Phase 3
Handles environment variables and API key management
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """Configuration for LLM integration"""
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    max_tokens: int = 300
    temperature: float = 0.1
    top_k: int = 5
    similarity_threshold: float = 0.4
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """Load configuration from environment variables"""
        # Load from .env file if exists
        if os.path.exists('.env'):
            from dotenv import load_dotenv
            load_dotenv()
        
        # Determine provider and model
        if os.getenv('OPENAI_API_KEY'):
            provider = "openai"
            model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            api_key = os.getenv('OPENAI_API_KEY')
        elif os.getenv('ANTHROPIC_API_KEY'):
            provider = "anthropic"
            model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-haiku')
            api_key = os.getenv('ANTHROPIC_API_KEY')
        else:
            provider = "local"
            model = os.getenv('LOCAL_LLM_MODEL_PATH', 'local')
            api_key = None
            logger.warning("No API key found. Using local LLM configuration.")
        
        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            max_tokens=int(os.getenv('RAG_MAX_TOKENS', 300)),
            temperature=float(os.getenv('RAG_TEMPERATURE', 0.1)),
            top_k=int(os.getenv('RAG_TOP_K', 5)),
            similarity_threshold=float(os.getenv('RAG_SIMILARITY_THRESHOLD', 0.4))
        )
    
    def validate(self) -> bool:
        """Validate configuration"""
        if self.provider == "openai" and not self.api_key:
            logger.error("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
            return False
        elif self.provider == "anthropic" and not self.api_key:
            logger.error("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable.")
            return False
        elif self.provider == "local":
            logger.info("Using local LLM configuration")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            "provider": self.provider,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
            "api_key_set": bool(self.api_key)
        }

def setup_logging():
    """Setup logging configuration"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', 'logs/llm_integration.log')
    
    # Create logs directory if not exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def main():
    """Test configuration loading"""
    setup_logging()
    
    config = LLMConfig.from_env()
    
    logger.info("LLM Configuration:")
    for key, value in config.to_dict().items():
        logger.info(f"  {key}: {value}")
    
    if config.validate():
        logger.info("Configuration is valid!")
    else:
        logger.error("Configuration validation failed!")

if __name__ == "__main__":
    main()
