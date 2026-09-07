#!/usr/bin/env python3
"""
Test script for Phase 3.1: LLM Configuration
"""

from llm_config import LLMConfig
import os

def test_llm_config():
    print('=== PHASE 3.1 TEST: LLM Configuration ===')
    
    try:
        # Test default configuration
        print('\n1. Testing default configuration:')
        default_config = LLMConfig()
        print(f'   Default provider: {default_config.provider}')
        print(f'   Default model: {default_config.model}')
        print(f'   Max tokens: {default_config.max_tokens}')
        print(f'   Temperature: {default_config.temperature}')
        print('   Default config: PASSED')
        
        # Test environment-based configuration
        print('\n2. Testing environment-based configuration:')
        env_config = LLMConfig.from_env()
        print(f'   Detected provider: {env_config.provider}')
        print(f'   Selected model: {env_config.model}')
        print(f'   API key present: {"Yes" if env_config.api_key else "No"}')
        print('   Environment config: PASSED')
        
        # Test provider-specific configurations
        print('\n3. Testing provider configurations:')
        
        # Test OpenAI config
        if os.getenv('OPENAI_API_KEY'):
            print('   OpenAI API key found - testing OpenAI config')
            openai_config = LLMConfig(
                provider="openai",
                model="gpt-4o-mini",
                api_key=os.getenv('OPENAI_API_KEY')
            )
            print(f'   OpenAI provider: {openai_config.provider}')
            print(f'   OpenAI model: {openai_config.model}')
            print('   OpenAI config: PASSED')
        else:
            print('   OpenAI API key not found - skipping OpenAI test')
        
        # Test Groq config
        if os.getenv('GROQ_API_KEY'):
            print('   Groq API key found - testing Groq config')
            groq_config = LLMConfig(
                provider="groq",
                model="llama3-70b-8192",
                api_key=os.getenv('GROQ_API_KEY')
            )
            print(f'   Groq provider: {groq_config.provider}')
            print(f'   Groq model: {groq_config.model}')
            print('   Groq config: PASSED')
        else:
            print('   Groq API key not found - skipping Groq test')
        
        # Test Anthropic config
        if os.getenv('ANTHROPIC_API_KEY'):
            print('   Anthropic API key found - testing Anthropic config')
            anthropic_config = LLMConfig(
                provider="anthropic",
                model="claude-3-5-haiku",
                api_key=os.getenv('ANTHROPIC_API_KEY')
            )
            print(f'   Anthropic provider: {anthropic_config.provider}')
            print(f'   Anthropic model: {anthropic_config.model}')
            print('   Anthropic config: PASSED')
        else:
            print('   Anthropic API key not found - skipping Anthropic test')
        
        print('\n=== PHASE 3.1 TEST PASSED ===')
        return True
        
    except Exception as e:
        print(f'ERROR: LLM configuration test failed: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_llm_config()
    if success:
        print('\n=== PHASE 3.1 TEST COMPLETED SUCCESSFULLY ===')
    else:
        print('\n=== PHASE 3.1 TEST FAILED ===')
