# Phase 7.3: Deployment Guide

## Objective: Host publicly accessible prototype

### 7.3.1 Streamlit Cloud Deployment (Recommended)

#### Steps:

1. **Push code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin <your-github-repo>
   git push -u origin main
   ```

2. **Go to Streamlit Cloud**
   - Visit https://share.streamlit.io
   - Sign up/login with GitHub account

3. **Connect GitHub account**
   - Authorize Streamlit to access your repositories
   - Select the repository containing the code

4. **Select repository and app.py**
   - Choose your repository
   - Select `phase5/app.py` as the main file
   - Configure app name and URL

5. **Add secrets in Streamlit dashboard**
   - Go to Settings > Secrets
   - Add `OPENAI_API_KEY` with your actual API key
   - Add any other environment variables needed

6. **Deploy**
   - Click "Deploy" button
   - Wait for deployment to complete
   - Access your app at `https://your-app-name.streamlit.app`

#### Secrets Configuration:

Create `.streamlit/secrets.toml` (don't commit this file!):
```toml
OPENAI_API_KEY = "sk-..."
```

Access in code:
```python
import streamlit as st
import os

# Use secrets in production
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
else:
    openai.api_key = os.environ.get("OPENAI_API_KEY")
```

### 7.3.2 Alternative: Video Demo

If hosting fails, record a 3-min demo video covering:

#### Video Content:
1. **UI walkthrough (30 seconds)**
   - Show sample questions
   - Display scheme scope
   - Demonstrate disclaimer

2. **Factual query example (45 seconds)**
   - Ask: "What is the expense ratio of ICICI Prudential Large Cap Fund?"
   - Show answer with citation
   - Display source URL

3. **Advice refusal example (45 seconds)**
   - Ask: "Should I invest in this fund?"
   - Show refusal response
   - Display SEBI advisor referral

4. **Out-of-scope refusal example (45 seconds)**
   - Ask: "What about HDFC Large Cap Fund?"
   - Show scope reminder
   - Display refusal message

5. **Source list quick view (15 seconds)**
   - Show sources.csv file
   - Display data sources

#### Recording Tools:
- **Loom**: https://www.loom.com (Recommended for screen recording)
- **OBS Studio**: https://obsproject.com (Free, open-source)
- **QuickTime**: Built-in for Mac users
- **Windows Game Bar**: Built-in for Windows users (Win+G)

#### Upload Options:
- YouTube (unlisted or public)
- Google Drive (shareable link)
- Loom (hosted on Loom platform)

### 7.3.3 Local Development Setup

For local testing before deployment:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-key-here"

# Run Streamlit app
cd phase5
streamlit run app.py
```

### 7.3.4 Troubleshooting

#### Common Issues:

1. **API Key Not Found**
   - Ensure OPENAI_API_KEY is set in environment or secrets
   - Check .env file is in project root
   - Verify secrets.toml is configured in Streamlit Cloud

2. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python version (3.11+ required)
   - Verify project structure is correct

3. **Vector Store Loading Issues**
   - Ensure `chunked_documents.json` exists in phase2/
   - Check FAISS index files are present
   - Verify data processing pipeline ran successfully

4. **Streamlit Cloud Deployment Failures**
   - Check GitHub repository is public or properly configured
   - Verify all dependencies are in requirements.txt
   - Ensure app.py is in the correct location
   - Check logs in Streamlit Cloud dashboard

### 7.3.5 Performance Optimization

For better performance:

1. **Reduce startup time**
   - Cache embeddings during first run
   - Use smaller embedding model if acceptable
   - Optimize chunk size for faster retrieval

2. **Improve response time**
   - Use streaming responses for LLM
   - Implement result caching
   - Optimize FAISS index parameters

3. **Reduce costs**
   - Use smaller LLM model (GPT-4o-mini recommended)
   - Implement query caching
   - Monitor API usage and set limits

## Deliverables

- **Public Streamlit link**: https://your-app.streamlit.app OR
- **Demo video**: demo_video.mp4 (≤3 min)
- **Deployment documentation**: This file

## Status

**Deployment Options Ready**
- ✅ Streamlit Cloud deployment guide
- ✅ Video demo recording instructions
- ✅ Local development setup
- ✅ Troubleshooting guide
- ✅ Performance optimization tips
