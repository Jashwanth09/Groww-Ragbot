# Streamlit Cloud Deployment Guide

## Overview
This guide explains how to deploy the ICICI Prudential Mutual Fund RAG system to Streamlit Cloud.

## Prerequisites

1. **GitHub Repository**
   - Push all code to a GitHub repository (public or private)
   - Ensure `web/app.py` is in the root or web directory

2. **API Keys**
   - OpenAI API key (recommended) OR Anthropic API key
   - Valid and active subscription

3. **Streamlit Account**
   - Free Streamlit Cloud account
   - Connected to GitHub

## Step-by-Step Deployment

### 1. Prepare Your Repository

#### File Structure
```
your-repo/
├── web/
│   └── app.py                 # Main Streamlit app
├── phase3/
│   ├── llm_config.py
│   └── answer_generator.py
├── phase2/
│   ├── simple_retrieval_pipeline.py
│   ├── embeddings.pkl
│   ├── faiss_index.bin
│   └── metadata_store.json
├── requirements.txt           # Python dependencies
├── .streamlit/
│   └── secrets.toml.example   # Example configuration
└── README.md
```

#### Update requirements.txt
Add Streamlit dependencies:
```txt
streamlit>=1.28.0
openai>=1.0.0
anthropic>=0.8.0
python-dotenv>=1.0.0
faiss-cpu>=1.7.0
sentence-transformers>=2.2.0
numpy>=1.24.0
```

### 2. Push to GitHub

```bash
git add .
git commit -m "Add Streamlit web interface"
git push origin main
```

### 3. Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**
   - Visit https://share.streamlit.io
   - Sign in with your GitHub account

2. **Create New App**
   - Click "New app" or "Deploy an app"
   - Select your GitHub repository
   - Choose the branch (usually `main`)
   - Select the main file path: `web/app.py`
   - Click "Deploy"

3. **Configure Secrets**
   - Go to your app settings on Streamlit Cloud
   - Click "Secrets" or "Advanced settings"
   - Add your API keys:

```toml
# For OpenAI (Recommended)
OPENAI_API_KEY = "sk-your-actual-openai-key"

# For Anthropic (Alternative)
# ANTHROPIC_API_KEY = "sk-ant-your-actual-anthropic-key"

# RAG Configuration
RAG_MAX_TOKENS = 300
RAG_TEMPERATURE = 0.1
RAG_TOP_K = 5
RAG_SIMILARITY_THRESHOLD = 0.4
```

### 4. Verify Deployment

1. **Check the App**
   - Visit your Streamlit app URL
   - Verify the interface loads correctly
   - Test with a sample query

2. **Test Functionality**
   - Try: "What is the expense ratio of ICICI Prudential Large Cap Fund?"
   - Verify answers include citations
   - Check out-of-scope query handling

## Troubleshooting

### Common Issues

#### 1. Module Import Errors
```
ModuleNotFoundError: No module named 'phase3'
```
**Solution**: Ensure `sys.path.append()` is correctly set in `app.py`

#### 2. API Key Issues
```
OpenAI API key not found
```
**Solution**: 
- Check secrets are correctly added in Streamlit Cloud
- Verify API key is valid and active
- Restart the app after adding secrets

#### 3. Large File Issues
```
File too large for deployment
```
**Solution**: 
- Exclude large data files from deployment
- Use GitHub Actions to process data separately
- Store embeddings in cloud storage if needed

#### 4. Performance Issues
**Slow response times**:
- Optimize embeddings size
- Reduce `RAG_TOP_K` value
- Use faster LLM model (gpt-4o-mini)

### Debug Mode

Add this to `app.py` for debugging:
```python
import streamlit as st

if st.secrets.get("DEBUG_MODE", False):
    st.write("Debug info:")
    st.write(st.secrets)
    st.write(os.environ)
```

## Advanced Configuration

### Custom Domain
1. Go to Streamlit Cloud app settings
2. Add custom domain (requires paid plan)
3. Configure DNS settings

### Environment Variables
Add additional environment variables in secrets:
```toml
# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "logs/app.log"

# Performance
MAX_CONCURRENT_REQUESTS = 10
REQUEST_TIMEOUT = 30

# Features
ENABLE_CHAT_HISTORY = true
ENABLE_ANALYTICS = false
```

### Multi-Environment Setup
Create separate apps for:
- **Staging**: `staging-app.yourname.streamlit.app`
- **Production**: `your-app.yourname.streamlit.app`

## Monitoring and Analytics

### Streamlit Metrics
- Visit your app dashboard
- Monitor usage statistics
- Check error logs

### Custom Analytics
Add analytics to `app.py`:
```python
import requests

def track_event(event_name, properties):
    if st.secrets.get("ANALYTICS_ENABLED", False):
        # Send to your analytics service
        pass
```

## Security Considerations

### API Key Security
- Never commit API keys to Git
- Use Streamlit secrets (not environment variables)
- Rotate API keys regularly
- Monitor API usage

### Data Privacy
- No PII is stored in the app
- Queries are logged (optional)
- Embeddings are pre-processed

### Rate Limiting
Add rate limiting in `app.py`:
```python
from datetime import datetime, timedelta

def check_rate_limit():
    # Implement rate limiting logic
    pass
```

## Performance Optimization

### Caching
```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_embeddings():
    # Load embeddings with caching
    pass
```

### Lazy Loading
```python
def get_answer_generator():
    if 'answer_generator' not in st.session_state:
        st.session_state.answer_generator = AnswerGenerator()
    return st.session_state.answer_generator
```

## Backup and Recovery

### Data Backup
- Embeddings are version-controlled in Git
- Configuration stored in secrets
- Chat history is session-based (not persistent)

### Recovery Steps
1. Restore embeddings from Git
2. Reconfigure secrets
3. Redeploy from main branch

## Cost Management

### OpenAI Costs
- gpt-4o-mini: ~$0.15/1M input tokens
- Monitor usage in OpenAI dashboard
- Set usage limits and alerts

### Streamlit Costs
- Free tier: Limited resources
- Paid tier: More resources and features

### Optimization Tips
- Use efficient prompts
- Limit response length
- Cache common queries
- Monitor token usage

## Next Steps

1. **Monitor Performance**: Track response times and user satisfaction
2. **Collect Feedback**: Add user feedback mechanism
3. **Add Features**: Scheme comparison, portfolio analysis
4. **Scale Up**: Move to dedicated hosting if needed
5. **Documentation**: Create user guide and API docs

## Support

- **Streamlit Documentation**: https://docs.streamlit.io
- **OpenAI API Docs**: https://platform.openai.com/docs
- **GitHub Issues**: Report bugs in your repository
- **Community**: Join Streamlit and OpenAI communities
