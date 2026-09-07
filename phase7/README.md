# ICICI Prudential MF Facts Assistant (Groww)

Fact-only FAQ chatbot for 4 ICICI Prudential Direct Growth schemes. Built with RAG + GPT-4o-mini.

## 🎯 Scope

**Covered Schemes:**
1. ICICI Prudential Multi Asset Fund Direct Growth
2. ICICI Prudential Large Cap Fund Direct Growth
3. ICICI Prudential Nifty Next 50 Index Direct Growth
4. ICICI Prudential Large & Mid Cap Fund Direct Plan Growth

**What it answers:**
- Expense ratios, exit loads, minimum SIP amounts
- Benchmarks, riskometer ratings
- Asset allocation (Multi Asset Fund)
- How to download statements/capital gains reports

**What it refuses:**
- Investment advice (buy/sell recommendations)
- Return predictions or performance comparisons
- Account/transaction support
- Queries with PII (PAN, Aadhaar, etc.)

## 🛠️ Tech Stack

- **Embeddings:** BGE `BAAI/bge-small-en-v1.5` (Free)
- **Vector Store:** FAISS
- **LLM:** GPT-4o-mini
- **UI:** Streamlit
- **Python:** 3.11+

## 📦 Setup

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd icici-mf-faq-assistant
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set API Key
```bash
export OPENAI_API_KEY="your-key-here"
```

Or create `.env` file:
```
OPENAI_API_KEY=your-key-here
```

### 4. Run Application
```bash
cd phase5
streamlit run app.py
```

## 📂 Project Structure

```
icici-mf-faq-assistant/
├── phase1/                 # Knowledge Base Preparation
│   ├── scraping_service/   # Web scraping from Groww
│   ├── text_normalizer.py  # Text normalization
│   └── hybrid_chunking.py  # Document chunking
├── phase2/                 # Embedding & Vector Store
│   ├── retrieval_pipeline.py # FAISS search logic
│   └── vector_store_manager.py # Vector store management
├── phase3/                 # LLM Integration
│   ├── answer_generator.py # LLM integration
│   └── llm_config.py       # LLM configuration
├── phase4/                 # Safety Layer
│   ├── safety.py           # Refusal & PII detection
│   └── enhanced_answer_generator.py # Phase 3+4 integration
├── phase5/                 # Streamlit UI
│   ├── app.py              # Streamlit application
│   └── README.md           # Phase 5 documentation
├── phase6/                 # Testing & QA
│   ├── test_cases.py       # Automated test suite
│   └── qa_checklist.md     # Manual QA checklist
├── phase7/                 # Documentation & Deployment
│   ├── README.md           # Main documentation
│   ├── sources.csv         # Source URL list
│   └── deployment.md       # Deployment guide
├── raw_documents/          # Scraped raw data
├── normalized_documents/   # Normalized text
├── processed_data/         # Chunked documents
└── requirements.txt        # Python dependencies
```

## 🧪 Testing

### Run Automated Tests
```bash
cd phase6
python test_cases.py
```

### Manual QA
- Follow the checklist in `phase6/qa_checklist.md`
- Test UI functionality in Streamlit
- Verify safety and refusal responses

## ⚠️ Known Limitations

- **Data freshness:** Sources from April 2024; may not reflect latest changes
- **Scheme scope:** Only 4 schemes; queries about other ICICI Pru funds will be refused
- **No real-time NAV:** Links to official pages for current NAV
- **English only:** Does not handle Hindi queries well

## 📊 Sample Q&A

**Q:** What is the expense ratio of ICICI Prudential Large Cap Fund Direct Growth?  
**A:** The Total Expense Ratio (TER) is 0.42% as of March 2024. Source: https://www.icicipruamc.com/... Last updated: March 31, 2024

**Q:** Should I invest in this fund?  
**A:** I provide facts only, not investment advice. For portfolio guidance, consult a SEBI-registered investment advisor. Learn more: https://investor.sebi.gov.in

## 🔒 Disclaimer

This tool is for informational purposes only and does not constitute investment advice. Mutual fund investments are subject to market risks. Please read all scheme-related documents carefully before investing.

## 📧 Contact

For issues or feedback: [your-email@example.com]

## 🚀 Deployment

### Streamlit Cloud Deployment
1. Push code to GitHub
2. Go to https://share.streamlit.io
3. Connect GitHub account
4. Select repository and app.py
5. Add secrets (OpenAI API key)
6. Deploy

### Alternative: Video Demo
If hosting fails, record 3-min demo video covering:
- UI walkthrough (sample questions, scope)
- Factual query example (with citation)
- Advice refusal example
- Out-of-scope refusal example
- Source list quick view

## 📋 Source Data

The system uses data from 4 ICICI Prudential schemes scraped from:
- ICICI Prudential AMC official website
- Groww platform
- SEBI-mandated disclosures (KIM/SID)
- AMFI/SEBI investor education

See `sources.csv` for complete source URL list.
