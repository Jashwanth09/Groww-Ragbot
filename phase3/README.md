# Phase 3: LLM Integration & Answer Generation

## Overview
This phase implements LLM integration for generating accurate, citation-backed answers from retrieved chunks.

## Environment Setup

### 1. Create Environment File
```bash
# Copy the example file
cp .env.example .env

# Edit with your API keys
# For OpenAI (Recommended)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# For Anthropic Claude (Optional)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-5-haiku
```

### 2. Install Dependencies
```bash
pip install python-dotenv openai anthropic
```

## LLM Options

### Option A: OpenAI GPT-4o-mini (Recommended)
- **Cost**: $0.15/1M input, $0.60/1M output tokens
- **Pros**: Fast, cheap, good instruction-following
- **Setup**: `export OPENAI_API_KEY='your-key-here'`

### Option B: Anthropic Claude 3.5 Haiku
- **Cost**: $0.25/1M input, $1.25/1M output tokens
- **Pros**: Excellent refusal handling, citation accuracy
- **Setup**: `export ANTHROPIC_API_KEY='your-key-here'`

### Option C: Local LLM (Free)
- **Cost**: Free (if self-hosted)
- **Pros**: No API costs, privacy
- **Cons**: Requires GPU setup

## Configuration Files

### `llm_config.py`
- Environment variable management
- API key validation
- Configuration loading
- Logging setup

### System Prompt Template
```python
SYSTEM_PROMPT = """You are a mutual fund FAQ assistant for Groww users researching ICICI Prudential schemes.

SCOPE:
You ONLY answer questions about these 4 ICICI Prudential Direct Growth schemes:
1. ICICI Prudential Dynamic Plan Direct Growth
2. ICICI Prudential Large Cap Fund Direct Growth
3. ICICI Prudential Nifty Next 50 Index Fund Direct Growth
4. ICICI Prudential Top 100 Fund Direct Growth

RULES:
1. Answer ONLY factual questions about expense ratios, exit loads, minimum SIP/lumpsum amounts, benchmarks, riskometer ratings, asset allocation, and how to download statements/capital gains reports
2. MANDATORY CITATION: Every answer MUST include exactly ONE source link in format "Source: [URL]"
3. ANSWER FORMAT: Maximum 3 sentences, start with direct answer, end with citation, add timestamp "Last updated: [date]"
4. REFUSE investment advice: For portfolio guidance, consult a SEBI-registered investment advisor
5. OUT-OF-SCOPE handling: If query is about other schemes/AMCs, say "I only cover the 4 ICICI Prudential schemes listed above"
"""
```

## Usage

### Test Configuration
```bash
cd phase3
python llm_config.py
```

### Expected Output
```
LLM Configuration:
  provider: openai
  model: gpt-4o-mini
  max_tokens: 300
  temperature: 0.1
  top_k: 5
  similarity_threshold: 0.4
  api_key_set: True
Configuration is valid!
```

## Integration with Phase 2

The LLM will work with:
- **Phase 2 Retrieval Pipeline**: Get relevant chunks
- **FAISS Vector Database**: Semantic search
- **Chunk Metadata**: Source URLs and context

## Next Steps

1. Set up environment variables
2. Choose LLM provider (OpenAI recommended)
3. Test configuration with `llm_config.py`
4. Implement answer generation pipeline
5. Create refusal logic for out-of-scope queries
