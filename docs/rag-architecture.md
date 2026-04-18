Phase 1: Knowledge Base Preparation
Phase 1.1: Source Collection & Organization
Objective: Gather 15–25 public URLs covering factual information about the 4 ICICI Prudential schemes
Sub-phases:
1.1.1 Scheme-Specific Document Collection
For each of the 4 schemes, collect:

Scheme page on Groww (basic details, NAV, returns display page)
Automated daily scraping for latest data

Target URLs:
1. https://groww.in/mutual-funds/icici-prudential-dynamic-plan-direct-growth
2. https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth
3. https://groww.in/mutual-funds/icici-prudential-nifty-next-50-index-fund-direct-growth
4. https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth

Target: 4 primary URLs (automated daily updates)
Schemes:

ICICI Prudential Dynamic Plan Direct Growth
ICICI Prudential Large Cap Fund Direct Growth
ICICI Prudential Nifty Next 50 Index Fund Direct Growth
ICICI Prudential Top 100 Fund Direct Growth

1.1.2 AMC-Wide Documentation

ICICI Prudential MF charges and fees page (exit load structure, TER breakdown)
Investor services page (how to download account statements)
Capital gains statement guide (CAS download instructions)
Riskometer disclosure page (methodology, ratings explanation)
Benchmark index methodology (or link to NSE Indices for index funds)

Target: 5–7 URLs
1.1.3 Regulatory & Educational Resources

AMFI website (scheme search, NAV lookup)
SEBI investor education pages:

Understanding expense ratios
Exit loads explained
Direct vs Regular plans
How to read factsheets


NSE Indices (Nifty Next 50 methodology)

Target: 3–5 URLs
Deliverable: sources.csv with columns:
source_id, url, source_type, scheme_name, description, last_accessed

Phase 1.1.4: Automated Scheduler Service
Objective: Schedule daily data collection at 9:15 AM for latest fund information
Tools: APScheduler (Advanced Python Scheduler)

Scheduler Configuration:
pythonfrom apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

# Configure logging
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

def setup_scheduler():
    scheduler = BackgroundScheduler()
    
    # Schedule daily job at 9:15 AM
    scheduler.add_job(
        func=daily_data_collection,
        trigger=CronTrigger(hour=9, minute=15),  # 9:15 AM daily
        id='daily_fund_data_update',
        name='Daily ICICI Prudential Fund Data Update',
        replace_existing=True
    )
    
    scheduler.start()
    return scheduler

Daily Data Collection Process:
1. Trigger scraping service for all 4 URLs
2. Validate extracted data completeness
3. Update vector embeddings with new data
4. Log success/failure with timestamps
5. Send alerts on failures

Error Handling:
- Retry failed URLs up to 3 times with exponential backoff
- Log all scraping attempts with response codes
- Fallback to previous day's data if all retries fail
- Alert monitoring system on consecutive failures

Deliverable: scheduler_service.py with automated daily execution

Phase 1.1.5: Web Scraping Service
Objective: Extract structured data from Groww mutual fund pages
Tools: Selenium WebDriver (for dynamic content) + BeautifulSoup4

Scraping Implementation:
pythonfrom selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json

class GrowwScraper:
    def __init__(self):
        options = Options()
        options.add_argument('--headless')  # Run in background
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def scrape_scheme_page(self, url):
        """Scrape individual scheme page for key metrics"""
        try:
            self.driver.get(url)
            time.sleep(3)  # Wait for page load
            
            # Wait for key elements to load
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "fundName")))
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract key information
            scheme_data = {
                'scheme_name': self._extract_scheme_name(soup),
                'nav': self._extract_nav(soup),
                'expense_ratio': self._extract_expense_ratio(soup),
                'exit_load': self._extract_exit_load(soup),
                'minimum_sip': self._extract_minimum_sip(soup),
                'benchmark': self._extract_benchmark(soup),
                'riskometer': self._extract_riskometer(soup),
                'aum': self._extract_aum(soup),
                'returns_1yr': self._extract_returns(soup, '1Y'),
                'returns_3yr': self._extract_returns(soup, '3Y'),
                'returns_5yr': self._extract_returns(soup, '5Y'),
                'last_updated': datetime.now().isoformat(),
                'source_url': url
            }
            
            return scheme_data
            
        except Exception as e:
            logging.error(f"Failed to scrape {url}: {str(e)}")
            return None
        finally:
            time.sleep(2)  # Rate limiting
    
    def _extract_scheme_name(self, soup):
        """Extract scheme name from page"""
        try:
            return soup.find('h1', class_='fundName').get_text().strip()
        except:
            return "Unknown Scheme"
    
    def _extract_nav(self, soup):
        """Extract current NAV"""
        try:
            nav_element = soup.find('span', text=lambda x: 'NAV' in x if x else False)
            if nav_element:
                return nav_element.find_next('span').get_text().strip()
        except:
            pass
        return "N/A"
    
    def _extract_expense_ratio(self, soup):
        """Extract expense ratio"""
        try:
            # Look for expense ratio in key metrics
            er_element = soup.find('div', text=lambda x: 'Expense' in x if x else False)
            if er_element:
                return er_element.find_next('div').get_text().strip()
        except:
            pass
        return "N/A"
    
    def _extract_exit_load(self, soup):
        """Extract exit load information"""
        try:
            # Look for exit load in details section
            exit_load_text = soup.find(text=lambda x: 'exit load' in x.lower() if x else False)
            if exit_load_text:
                return exit_load_text.parent.get_text().strip()
        except:
            pass
        return "N/A"
    
    def _extract_minimum_sip(self, soup):
        """Extract minimum SIP amount"""
        try:
            sip_element = soup.find(text=lambda x: 'SIP' in x if x else False)
            if sip_element:
                return sip_element.find_next('span').get_text().strip()
        except:
            pass
        return "N/A"
    
    def _extract_benchmark(self, soup):
        """Extract benchmark index"""
        try:
            benchmark_element = soup.find(text=lambda x: 'Benchmark' in x if x else False)
            if benchmark_element:
                return benchmark_element.find_next('div').get_text().strip()
        except:
            pass
        return "N/A"
    
    def _extract_riskometer(self, soup):
        """Extract riskometer rating"""
        try:
            risk_element = soup.find(class_=lambda x: 'risk' in x.lower() if x else False)
            if risk_element:
                return risk_element.get_text().strip()
        except:
            pass
        return "N/A"
    
    def _extract_aum(self, soup):
        """Extract Assets Under Management"""
        try:
            aum_element = soup.find(text=lambda x: 'AUM' in x if x else False)
            if aum_element:
                return aum_element.find_next('span').get_text().strip()
        except:
            pass
        return "N/A"
    
    def _extract_returns(self, soup, period):
        """Extract returns for specific period"""
        try:
            returns_element = soup.find(text=lambda x: period in x if x else False)
            if returns_element:
                return returns_element.find_next('span').get_text().strip()
        except:
            pass
        return "N/A"

Daily Scraping Orchestration:
pythondef daily_data_collection():
    """Main function called by scheduler"""
    scraper = GrowwScraper()
    urls = [
        "https://groww.in/mutual-funds/icici-prudential-dynamic-plan-direct-growth",
        "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/icici-prudential-nifty-next-50-index-fund-direct-growth",
        "https://groww.in/mutual-funds/icici-prudential-top-100-fund-direct-growth"
    ]
    
    all_data = []
    failed_urls = []
    
    for url in urls:
        data = scraper.scrape_scheme_page(url)
        if data:
            all_data.append(data)
            logging.info(f"Successfully scraped: {url}")
        else:
            failed_urls.append(url)
            logging.error(f"Failed to scrape: {url}")
    
    # Save collected data
    if all_data:
        with open(f"raw_data/fund_data_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
            json.dump(all_data, f, indent=2)
        
        # Trigger reprocessing pipeline
        update_vector_database(all_data)
    
    # Clean up
    scraper.driver.quit()
    
    # Report failures
    if failed_urls:
        send_failure_alert(failed_urls)

Data Storage Structure:
raw_data/
├── fund_data_20240415.json
├── fund_data_20240416.json
└── fund_data_20240417.json

processed_data/
├── chunks_dynamic_plan.json
├── chunks_large_cap.json
├── chunks_nifty_next_50.json
└── chunks_top_100.json

Deliverable: scraping_service.py with complete data extraction pipeline

Phase 1.2: Document Extraction & Preprocessing
Objective: Convert all collected sources into clean, structured text suitable for embedding
1.2.1 PDF Processing
Tools: PyMuPDF (fitz) or pdfplumber
Process:

Download all PDFs (factsheets, KIM, SID)
Extract text page-by-page
Clean extracted text:

Remove headers/footers (page numbers, "ICICI Prudential AMC" watermarks)
Fix spacing issues (merged words, extra newlines)
Preserve table structure where possible (expense ratio tables, asset allocation)


Tag each extracted section with metadata:

python   {
     "text": "Expense Ratio: 0.42% (as of March 2024)",
     "source_id": "factsheet_largecap_mar2024",
     "scheme": "ICICI Prudential Large Cap Fund Direct Growth",
     "page": 2,
     "url": "https://..."
   }
1.2.2 Web Page Scraping
Tools: BeautifulSoup4 or Playwright (for dynamic content)
Process:

Scrape Groww scheme pages (HTML content)
Extract relevant sections:

Scheme details (NAV, minimum SIP, exit load)
Investment objective
Benchmark information


Scrape ICICI Pru investor service pages (statement download guides)
Clean HTML artifacts (remove navigation, ads, footers)

1.2.3 Text Normalization

Standardize scheme names (e.g., "ICICI Pru Large Cap" → "ICICI Prudential Large Cap Fund Direct Growth")
Normalize numerical formats (₹5,000 → 5000, 0.42% → 0.42)
Convert dates to ISO format (March 2024 → 2024-03)
Handle abbreviations consistently (TER, AUM, NAV, SIP)

Deliverable: raw_documents/ folder with:

{scheme_name}_factsheet.txt
{scheme_name}_kim.txt
{scheme_name}_sid.txt
amc_fees.txt
investor_services.txt
sebi_education.txt


Phase 1.3: Document Chunking Strategy
Objective: Split documents into semantically meaningful chunks for accurate retrieval
1.3.1 Chunking Approach Selection
Recommended: Hybrid chunking (semantic + fixed-size with overlap)
Rationale:

Combines semantic section boundaries with consistent sizing
Preserves context through overlapping chunks
Better retrieval accuracy with complete coverage
Optimal for both structured and unstructured documents

Implementation:
python# Hybrid chunking parameters
target_chunk_size = 400    # characters
chunk_overlap = 100        # 25% overlap
min_chunk_size = 50        # minimum viable chunk

# Semantic section markers (initial boundaries)
SECTION_MARKERS = [
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

# Hybrid process:
# 1. Split by semantic sections
# 2. Apply fixed-size chunking with overlap
# 3. Break at sentence boundaries
# 4. Preserve context through overlap
1.3.2 Chunk Size Configuration

Target chunk size: 400 characters (optimal for BGE embeddings)
Overlap: 100 characters (25% for context preservation)
Sentence boundaries: Natural breaks preferred
Metadata preservation: Source URL, scheme name, section type, overlap tracking

Special cases:

Tables (expense ratio breakdown): Keep within single chunk if possible
Step-by-step guides (download statements): Split with overlap to preserve steps
Short factoids (minimum SIP amount): Merge with related content
Long sections: Apply sliding window with overlap

1.3.3 Chunk Metadata Schema
python{
  "chunk_id": "largecap_expenseRatio_001",
  "text": "The Total Expense Ratio (TER) for ICICI Prudential Large Cap Fund Direct Growth is 0.42% as of March 2024...",
  "scheme": "ICICI Prudential Large Cap Fund Direct Growth",
  "section_type": "expense_ratio",
  "source_url": "https://www.icicipruamc.com/...",
  "source_type": "factsheet",
  "last_updated": "2024-03-31",
  "token_count": 387
}
Deliverable: chunked_documents.json (array of chunk objects)

Phase 2: Embedding & Vector Store Setup
Phase 2.1: Embedding Model Selection
Objective: Choose and configure embedding model for semantic search
2.1.1 Model Options Evaluation
Option A: BGE-small-en-v1.5 (Recommended)

Dimensions: 384
Cost: Completely free
Pros: State-of-the-art performance, no API costs, MIT license
Cons: Local computation required

Option B: OpenAI text-embedding-3-small

Dimensions: 1536
Cost: $0.02 / 1M tokens
Pros: High quality, reliable, fast
Cons: Requires API key, ongoing cost

Option C: Cohere embed-english-v3.0

Dimensions: 1024
Cost: Free tier available (1000 requests/month)
Pros: Good for factual retrieval, compression option
Cons: Rate limits on free tier

Recommended for prototype: BGE-small-en-v1.5 (best free performance)
2.1.2 Embedding Generation Process
pythonfrom sentence_transformers import SentenceTransformer

def embed_chunks(chunks, model="BAAI/bge-small-en-v1.5"):
    model = SentenceTransformer(model)
    texts = [chunk["text"] for chunk in chunks]
    
    # Generate embeddings in batches
    embeddings = model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True  # Important for BGE
    )
    
    # Create embedding objects
    embedding_objects = []
    for chunk, embedding in zip(chunks, embeddings):
        embedding_objects.append({
            "chunk_id": chunk["chunk_id"],
            "embedding": embedding.tolist(),
            "metadata": chunk
        })
    
    return embedding_objects
Batch processing:

Process in batches of 100 chunks
Add retry logic for API failures
Cache embeddings to avoid re-processing

Deliverable: embeddings.pkl (pickled array of embedding vectors + metadata)

Phase 2.2: Vector Database Setup
Objective: Store embeddings in queryable vector database
2.2.1 Vector Store Selection
Option A: FAISS (Local)

Pros: Free, fast, no external dependencies
Cons: No persistence by default (need to save/load index)
Best for: Local development, small corpus (<10K chunks)

Option B: Pinecone (Cloud)

Pros: Managed, auto-scaling, persistent
Cons: Free tier limited (1 index, 100K vectors)
Best for: Production deployment

Option C: Chroma (Local/Cloud)

Pros: Easy to use, built-in persistence
Cons: Less mature than FAISS/Pinecone
Best for: Quick prototyping

Recommended for prototype: FAISS (simple, free, sufficient for ~100 chunks)
2.2.2 Index Creation
pythonimport faiss
import numpy as np

# Create FAISS index
dimension = 384  # for BGE-small-en-v1.5
index = faiss.IndexFlatL2(dimension)

# Add embeddings
embedding_matrix = np.array([e["embedding"] for e in embeddings])
index.add(embedding_matrix)

# Save index
faiss.write_index(index, "faiss_index.bin")
2.2.3 Metadata Storage
Since FAISS only stores vectors, create parallel metadata store:
pythonimport json

metadata_store = {
    i: embeddings[i]["metadata"]
    for i in range(len(embeddings))
}

with open("metadata_store.json", "w") as f:
    json.dump(metadata_store, f, indent=2)
Deliverable:

faiss_index.bin (vector index)
metadata_store.json (chunk metadata lookup)


Phase 2.3: Retrieval Pipeline
Objective: Implement semantic search to fetch relevant chunks for user queries
2.3.1 Query Processing
pythondef process_query(query: str) -> dict:
    # 1. Generate query embedding
    query_embedding = openai.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    ).data[0].embedding
    
    # 2. Search FAISS index
    k = 5  # top 5 results
    distances, indices = index.search(
        np.array([query_embedding]), k
    )
    
    # 3. Fetch metadata for top results
    results = []
    for i, idx in enumerate(indices[0]):
        results.append({
            "chunk": metadata_store[idx],
            "score": float(distances[0][i])
        })
    
    return results
2.3.2 Re-ranking Strategy (Optional Enhancement)
For better precision, implement two-stage retrieval:
Stage 1: Semantic search (top 10 chunks via FAISS)
Stage 2: Re-rank using cross-encoder
pythonfrom sentence_transformers import CrossEncoder

reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank_results(query, results):
    pairs = [[query, r["chunk"]["text"]] for r in results]
    scores = reranker.predict(pairs)
    
    for i, result in enumerate(results):
        result["rerank_score"] = scores[i]
    
    return sorted(results, key=lambda x: x["rerank_score"], reverse=True)
2.3.3 Retrieval Quality Checks

Minimum similarity threshold: Reject results with distance > 0.8 (L2 norm)
Source diversity: If top 5 results all from same document, include next-best from different source
Scheme filtering: If query mentions specific scheme name, boost results from that scheme

Deliverable: retrieval.py module with retrieve(query: str) -> List[dict] function

Phase 3: LLM Integration & Answer Generation
Phase 3.1: LLM Selection & Configuration
Objective: Choose and configure LLM for answer generation with strict fact-only behavior
3.1.1 Model Options
Option A: GPT-4o-mini

Cost: $0.15/1M input tokens, $0.60/1M output tokens
Pros: Fast, cheap, good instruction-following
Cons: Requires OpenAI API key

Option B: Claude 3.5 Haiku

Cost: $0.25/1M input tokens, $1.25/1M output tokens
Pros: Excellent at refusals, citation accuracy
Cons: Slightly more expensive

Option C: Llama 3.1 8B (Local)

Cost: Free (if self-hosted)
Pros: No API costs, privacy
Cons: Needs GPU, lower quality

Recommended: GPT-4o-mini (best cost/performance for prototype)

Phase 3.2: Prompt Engineering
Objective: Design system prompt for accurate, concise, citation-backed answers
3.2.1 System Prompt Template
pythonSYSTEM_PROMPT = """You are a mutual fund FAQ assistant for Groww users researching ICICI Prudential schemes.

SCOPE:
You ONLY answer questions about these 4 ICICI Prudential Direct Growth schemes:
1. ICICI Prudential Multi Asset Fund
2. ICICI Prudential Large Cap Fund
3. ICICI Prudential Nifty Next 50 Index Fund
4. ICICI Prudential Large & Mid Cap Fund

RULES:
1. Answer ONLY factual questions about:
   - Expense ratios
   - Exit loads
   - Minimum SIP/lumpsum amounts
   - Benchmarks
   - Riskometer ratings
   - Asset allocation (for Multi Asset Fund)
   - How to download statements/capital gains reports

2. MANDATORY CITATION:
   - Every answer MUST include exactly ONE source link
   - Format: "Source: [URL]"
   - Use the most specific/recent source from retrieved context

3. ANSWER FORMAT:
   - Maximum 3 sentences
   - Start with direct answer
   - Add context if helpful
   - End with citation
   - Add timestamp: "Last updated: [date from source]"

4. REFUSE investment advice:
   - Questions like "Should I invest?", "Which is better?", "Will it give good returns?"
   - Response: "I provide facts only, not investment advice. For portfolio guidance, consult a SEBI-registered investment advisor. Learn more: https://investor.sebi.gov.in"
   - Do NOT attempt to answer these even partially

5. OUT-OF-SCOPE handling:
   - If query is about other schemes/AMCs: "I only cover the 4 ICICI Prudential schemes listed above."
   - If query is about account opening/transactions: "For account-related queries, visit Groww support or ICICI Prudential customer care."

6. TONE:
   - Professional but friendly
   - Concise and precise
   - No jargon unless in source material
   - If using abbreviations (TER, NAV), mention full form once

CRITICAL: If retrieved context doesn't contain the answer, say "I don't have that information in my current knowledge base. Please check the official ICICI Prudential factsheet or contact customer support."
"""
3.2.2 User Prompt Construction
pythondef build_user_prompt(query: str, retrieved_chunks: List[dict]) -> str:
    context = "\n\n".join([
        f"[Source: {chunk['source_url']}]\n{chunk['text']}"
        for chunk in retrieved_chunks[:3]  # top 3 chunks
    ])
    
    return f"""CONTEXT FROM KNOWLEDGE BASE:
{context}

USER QUESTION:
{query}

Provide a factual answer following all rules in the system prompt."""

Phase 3.3: Answer Generation Pipeline
Objective: Orchestrate retrieval + LLM call with quality checks
3.3.1 Main Generation Function
pythonimport openai

def generate_answer(query: str) -> dict:
    # Step 1: Retrieve relevant chunks
    retrieved_chunks = retrieve(query)
    
    # Step 2: Check if retrieval succeeded
    if not retrieved_chunks or retrieved_chunks[0]["score"] > 0.8:
        return {
            "answer": "I don't have that information in my current knowledge base. Please check the official ICICI Prudential factsheet or contact customer support.",
            "sources": [],
            "confidence": "low"
        }
    
    # Step 3: Build prompt
    user_prompt = build_user_prompt(query, retrieved_chunks)
    
    # Step 4: Call LLM
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,  # low temp for factual accuracy
        max_tokens=300
    )
    
    answer_text = response.choices[0].message.content
    
    # Step 5: Extract citation from answer
    cited_sources = extract_urls(answer_text)
    
    return {
        "answer": answer_text,
        "sources": cited_sources,
        "retrieved_chunks": retrieved_chunks[:3],
        "confidence": "high" if retrieved_chunks[0]["score"] < 0.5 else "medium"
    }
3.3.2 Citation Extraction & Validation
pythonimport re

def extract_urls(text: str) -> List[str]:
    """Extract URLs from answer text"""
    url_pattern = r'https?://[^\s\)]+'
    return re.findall(url_pattern, text)

def validate_citation(answer: str, retrieved_sources: List[str]) -> bool:
    """Ensure cited URL is from retrieved context"""
    cited_urls = extract_urls(answer)
    if not cited_urls:
        return False
    return any(url in retrieved_sources for url in cited_urls)
3.3.3 Answer Quality Checks
pythondef check_answer_quality(answer: str, query: str) -> dict:
    """Validate answer meets quality standards"""
    checks = {
        "has_citation": bool(extract_urls(answer)),
        "within_length": len(answer.split()) <= 100,  # ~3 sentences
        "not_advice": not any(phrase in answer.lower() for phrase in 
            ["you should", "i recommend", "better to", "good choice"]),
        "has_timestamp": "Last updated" in answer or "as of" in answer.lower()
    }
    
    return {
        "passed": all(checks.values()),
        "checks": checks
    }
Deliverable: answer_generator.py with generate_answer(query: str) -> dict function

Phase 4: Refusal Logic & Safety Layer
Phase 4.1: Query Classification
Objective: Detect and handle out-of-scope/advice-seeking queries BEFORE retrieval
4.1.1 Rule-Based Classifier
pythonADVICE_KEYWORDS = [
    "should i", "recommend", "better", "best", "good investment",
    "worth it", "buy or sell", "switch", "redeem", "which one",
    "portfolio", "allocate", "invest now", "right time"
]

OUT_OF_SCOPE_KEYWORDS = [
    "open account", "kyc", "aadhar", "pan", "otp", "password",
    "transaction failed", "redemption pending", "nav not updated"
]

def classify_query(query: str) -> str:
    """Returns: 'factual', 'advice', 'out_of_scope'"""
    query_lower = query.lower()
    
    if any(kw in query_lower for kw in ADVICE_KEYWORDS):
        return "advice"
    
    if any(kw in query_lower for kw in OUT_OF_SCOPE_KEYWORDS):
        return "out_of_scope"
    
    return "factual"
4.1.2 LLM-Based Classifier (Fallback)
For edge cases, use lightweight LLM call:
pythonCLASSIFICATION_PROMPT = """Classify this mutual fund query:

Query: {query}

Categories:
- factual: Asks for specific facts (expense ratio, exit load, minimum SIP, etc.)
- advice: Seeks investment recommendations, opinions, or decision-making guidance
- out_of_scope: Account issues, transactions, KYC, technical problems

Respond with ONLY the category name."""

def classify_with_llm(query: str) -> str:
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": CLASSIFICATION_PROMPT.format(query=query)}
        ],
        temperature=0,
        max_tokens=10
    )
    return response.choices[0].message.content.strip().lower()

Phase 4.2: Refusal Response Templates
Objective: Provide helpful, polite refusals with educational resources
4.2.1 Advice Refusal
pythonADVICE_REFUSAL = """I provide facts only, not investment advice.

For personalized portfolio guidance, please consult a SEBI-registered investment advisor.

📚 Learn more:
- SEBI Investor Awareness: https://investor.sebi.gov.in
- Find SEBI-registered advisors: https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognised=yes

Would you like factual information about any of the 4 ICICI Prudential schemes instead?"""
4.2.2 Out-of-Scope Refusal
pythonOUT_OF_SCOPE_REFUSAL = """I only answer factual questions about these 4 ICICI Prudential schemes:
1. Multi Asset Fund
2. Large Cap Fund
3. Nifty Next 50 Index Fund
4. Large & Mid Cap Fund

For account-related queries, please contact:
- Groww Support: https://groww.in/help
- ICICI Prudential Customer Care: 1860 266 7766

Can I help with facts about any of the above schemes?"""
4.2.3 Performance/Returns Refusal
pythonPERFORMANCE_REFUSAL = """I cannot compute or predict fund returns.

For official performance data, please check:
- Latest factsheet: [link to factsheet page]
- Groww fund page: [scheme-specific Groww URL]

Note: Past performance does not guarantee future results.

Can I help with other factual information about this scheme?"""

Phase 4.3: PII Detection & Blocking
Objective: Reject queries containing personal identifiable information
4.3.1 PII Patterns
pythonimport re

PII_PATTERNS = {
    "pan": r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
    "aadhaar": r'\b\d{4}\s?\d{4}\s?\d{4}\b',
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b[6-9]\d{9}\b',
    "account": r'\b\d{9,18}\b'  # typical bank account numbers
}

def detect_pii(query: str) -> List[str]:
    """Returns list of detected PII types"""
    detected = []
    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, query):
            detected.append(pii_type)
    return detected
4.3.2 PII Refusal
pythondef handle_pii_query(detected_pii: List[str]) -> str:
    pii_names = ", ".join(detected_pii).upper()
    return f"""⚠️ Security Notice

I cannot process queries containing personal information ({pii_names}).

Please remove sensitive details and ask your question again without:
- PAN/Aadhaar numbers
- Account numbers
- Email addresses
- Phone numbers
- OTPs or passwords

How can I help with factual information about ICICI Prudential schemes?"""
Deliverable: safety.py module with classification and refusal logic

Phase 5: Streamlit UI Development
Phase 5.1: UI Layout & Design
Objective: Build clean, mobile-friendly chat interface
5.1.1 App Structure
pythonimport streamlit as st

# Page config
st.set_page_config(
    page_title="ICICI Pru MF Facts Assistant",
    page_icon="🔍",
    layout="centered"
)

# Header
st.title("🔍 ICICI Prudential MF Facts Assistant")
st.caption("Powered by Groww | Facts-only, No investment advice")

# Disclaimer
st.info("""
💡 **What I can help with:**
- Expense ratios, exit loads, minimum SIP amounts
- Benchmarks, riskometer ratings
- How to download statements

❌ **What I cannot do:**
- Provide investment advice or recommendations
- Predict returns or compare performance
- Handle account/transaction issues
""")

# Scheme scope
with st.expander("📋 Covered Schemes"):
    st.markdown("""
    1. ICICI Prudential Multi Asset Fund Direct Growth
    2. ICICI Prudential Large Cap Fund Direct Growth
    3. ICICI Prudential Nifty Next 50 Index Direct Growth
    4. ICICI Prudential Large & Mid Cap Fund Direct Plan Growth
    """)
5.1.2 Sample Questions Section
pythonst.markdown("### 💬 Try asking:")

col1, col2 = st.columns(2)

with col1:
    if st.button("What is the expense ratio of ICICI Pru Large Cap Fund?"):
        st.session_state.sample_query = "What is the expense ratio of ICICI Pru Large Cap Fund?"
    
    if st.button("Exit load for Multi Asset Fund?"):
        st.session_state.sample_query = "Exit load for Multi Asset Fund?"

with col2:
    if st.button("Minimum SIP for Nifty Next 50 Index Fund?"):
        st.session_state.sample_query = "Minimum SIP for Nifty Next 50 Index Fund?"
    
    if st.button("How to download capital gains statement?"):
        st.session_state.sample_query = "How to download capital gains statement?"

Phase 5.2: Chat Interface Implementation
Objective: Build conversational UI with history
5.2.1 Session State Management
python# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "sample_query" not in st.session_state:
    st.session_state.sample_query = None
5.2.2 Message Display
python# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources if available
        if message["role"] == "assistant" and "sources" in message:
            if message["sources"]:
                with st.expander("📎 Sources"):
                    for source in message["sources"]:
                        st.markdown(f"- {source}")
5.2.3 Input Handling
python# Handle sample query clicks
if st.session_state.sample_query:
    user_query = st.session_state.sample_query
    st.session_state.sample_query = None  # Reset
else:
    user_query = st.chat_input("Ask about ICICI Prudential schemes...")

if user_query:
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_query
    })
    
    with st.chat_message("user"):
        st.markdown(user_query)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            response = generate_answer(user_query)
        
        st.markdown(response["answer"])
        
        # Show sources
        if response["sources"]:
            with st.expander("📎 Sources"):
                for source in response["sources"]:
                    st.markdown(f"- {source}")
    
    # Add assistant response to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response["answer"],
        "sources": response["sources"]
    })

Phase 5.3: Additional UI Features
5.3.1 Sidebar Information
pythonwith st.sidebar:
    st.markdown("### ℹ️ About")
    st.markdown("""
    This assistant provides **factual information only** about 4 ICICI Prudential Direct Growth schemes.
    
    **Last updated:** April 2024
    
    **Data sources:**
    - ICICI Prudential AMC official website
    - SEBI-mandated disclosures (KIM/SID)
    - Groww platform
    - AMFI/SEBI investor education
    """)
    
    st.markdown("---")
    
    st.markdown("### ⚠️ Disclaimer")
    st.markdown("""
    This tool is for informational purposes only and does not constitute investment advice.
    
    Mutual fund investments are subject to market risks. Please read all scheme-related documents carefully before investing.
    
    For personalized advice, consult a SEBI-registered investment advisor.
    """)
    
    st.markdown("---")
    
    # Feedback
    st.markdown("### 📧 Feedback")
    if st.button("Report an issue"):
        st.info("Contact: [your-email@example.com]")
5.3.2 Clear Chat Button
pythonif st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.messages = []
    st.rerun()
5.3.3 Debug Mode (Optional)
python# Only show in development
if st.sidebar.checkbox("🐛 Debug Mode", value=False):
    with st.sidebar.expander("Last Response Details"):
        if st.session_state.messages:
            last_response = st.session_state.messages[-1]
            st.json(last_response)
Deliverable: app.py (complete Streamlit application)

Phase 6: Testing & Quality Assurance
Phase 6.1: Test Case Development
Objective: Create comprehensive test suite covering all scenarios
6.1.1 Factual Query Test Cases
pythonFACTUAL_TESTS = [
    {
        "query": "What is the expense ratio of ICICI Prudential Large Cap Fund Direct Growth?",
        "expected_type": "factual_answer",
        "must_contain": ["expense ratio", "0.", "%"],
        "must_cite": True
    },
    {
        "query": "Exit load for ICICI Pru Multi Asset Fund?",
        "expected_type": "factual_answer",
        "must_contain": ["exit load", "%"],
        "must_cite": True
    },
    {
        "query": "Minimum SIP amount for Nifty Next 50 Index Fund?",
        "expected_type": "factual_answer",
        "must_contain": ["minimum", "SIP", "₹"],
        "must_cite": True
    },
    {
        "query": "What is the benchmark of Large & Mid Cap Fund?",
        "expected_type": "factual_answer",
        "must_contain": ["benchmark", "Nifty"],
        "must_cite": True
    },
    {
        "query": "How do I download my capital gains statement?",
        "expected_type": "factual_answer",
        "must_contain": ["download", "statement"],
        "must_cite": True
    }
]
6.1.2 Refusal Test Cases
pythonREFUSAL_TESTS = [
    {
        "query": "Should I invest in ICICI Pru Large Cap Fund?",
        "expected_type": "advice_refusal",
        "must_contain": ["not investment advice", "SEBI-registered"],
        "must_not_contain": ["yes", "no", "good", "recommend"]
    },
    {
        "query": "Which is better - Large Cap or Multi Asset?",
        "expected_type": "advice_refusal",
        "must_contain": ["facts only", "advisor"]
    },
    {
        "query": "Will this fund give 15% returns?",
        "expected_type": "performance_refusal",
        "must_contain": ["cannot predict", "past performance"]
    },
    {
        "query": "My transaction failed, help!",
        "expected_type": "out_of_scope_refusal",
        "must_contain": ["Groww Support", "customer care"]
    },
    {
        "query": "My PAN is ABCDE1234F, can I invest?",
        "expected_type": "pii_refusal",
        "must_contain": ["Security Notice", "personal information"]
    }
]
6.1.3 Edge Case Tests
pythonEDGE_CASE_TESTS = [
    {
        "query": "What about HDFC Large Cap Fund?",
        "expected_type": "out_of_scope_refusal",
        "must_contain": ["only cover", "4 ICICI Prudential"]
    },
    {
        "query": "Tell me everything about ICICI Pru Large Cap",
        "expected_type": "factual_answer",
        "note": "Should give concise summary, not dump all data"
    },
    {
        "query": "expense ratio",
        "expected_type": "clarification",
        "must_contain": ["which scheme"]
    }
]

Phase 6.2: Automated Testing Script
Objective: Run test suite and generate report
6.2.1 Test Runner
pythonimport json
from typing import List, Dict

def run_tests(test_cases: List[Dict]) -> Dict:
    """Run test suite and return results"""
    results = {
        "total": len(test_cases),
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    for i, test in enumerate(test_cases):
        print(f"Running test {i+1}/{len(test_cases)}: {test['query'][:50]}...")
        
        # Generate answer
        response = generate_answer(test["query"])
        answer = response["answer"].lower()
        
        # Check conditions
        passed = True
        failures = []
        
        # Must contain check
        if "must_contain" in test:
            for phrase in test["must_contain"]:
                if phrase.lower() not in answer:
                    passed = False
                    failures.append(f"Missing phrase: {phrase}")
        
        # Must NOT contain check
        if "must_not_contain" in test:
            for phrase in test["must_not_contain"]:
                if phrase.lower() in answer:
                    passed = False
                    failures.append(f"Contains forbidden phrase: {phrase}")
        
        # Citation check
        if test.get("must_cite") and not response["sources"]:
            passed = False
            failures.append("Missing citation")
        
        # Record result
        test_result = {
            "query": test["query"],
            "expected_type": test["expected_type"],
            "passed": passed,
            "failures": failures,
            "answer": response["answer"]
        }
        
        results["details"].append(test_result)
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
    
    return results

# Run all test suites
all_tests = FACTUAL_TESTS + REFUSAL_TESTS + EDGE_CASE_TESTS
test_results = run_tests(all_tests)

# Save results
with open("test_results.json", "w") as f:
    json.dump(test_results, f, indent=2)

print(f"\n{'='*50}")
print(f"Test Results: {test_results['passed']}/{test_results['total']} passed")
print(f"{'='*50}")

Phase 6.3: Manual QA Checklist
Objective: Human verification of critical functionality
6.3.1 Core Functionality Checks

 Factual queries return accurate answers within 3 sentences
 Every factual answer includes exactly 1 source URL
 Source URLs are from approved list (ICICI Pru, Groww, SEBI, AMFI)
 Answers include "Last updated" timestamp from source
 Scheme names are spelled correctly and consistently

6.3.2 Safety & Refusal Checks

 Investment advice queries are politely refused
 Refusals include SEBI advisor referral link
 PII in queries triggers security notice
 Out-of-scope schemes trigger scope reminder
 Account/transaction queries redirect to support

6.3.3 UI/UX Checks

 Sample questions work when clicked
 Chat history persists across questions
 Sources expand/collapse cleanly
 Mobile-responsive (test on phone)
 No broken links in citations
 Clear chat button works

6.3.4 Edge Case Checks

 Empty query handling
 Very long queries (>500 words)
 Queries in mixed Hindi-English
 Rapid-fire queries (rate limiting if needed)
 Multiple questions in one query

Deliverable: test_results.json and manual QA checklist (PDF/MD)

Phase 7: Documentation & Deployment
Phase 7.1: README Documentation
Objective: Comprehensive setup and usage guide
7.1.1 README Structure
markdown# ICICI Prudential MF Facts Assistant (Groww)

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
git clone 
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

### 4. Run Application
```bash
streamlit run app.py
```

## 📂 Project Structure
icici-mf-faq-assistant/
├── app.py                  # Streamlit UI
├── retrieval.py            # FAISS search logic
├── answer_generator.py     # LLM integration
├── safety.py               # Refusal & PII detection
├── data/
│   ├── sources.csv         # List of 20 source URLs
│   ├── chunked_documents.json
│   ├── faiss_index.bin
│   └── metadata_store.json
├── tests/
│   ├── test_cases.py
│   └── test_results.json
├── requirements.txt
└── README.md

## 🧪 Testing

Run automated tests:
```bash
python tests/test_cases.py
```

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

Phase 7.2: Source List Documentation
Objective: CSV file with all 20 source URLs
7.2.1 CSV Format
csvsource_id,url,source_type,scheme_name,description,last_accessed
factsheet_largecap_mar2024,https://www.icicipruamc.com/downloads/factsheet/large-cap-fund-mar2024.pdf,factsheet,ICICI Prudential Large Cap Fund Direct Growth,Monthly factsheet with portfolio and performance,2024-04-15
kim_largecap,https://www.icicipruamc.com/downloads/kim/large-cap-fund.pdf,kim,ICICI Prudential Large Cap Fund Direct Growth,Key Information Memorandum,2024-04-15
sid_largecap,https://www.icicipruamc.com/downloads/sid/large-cap-fund.pdf,sid,ICICI Prudential Large Cap Fund Direct Growth,Scheme Information Document,2024-04-15
...
Deliverable: sources.csv with 15–25 rows

Phase 7.3: Deployment
Objective: Host publicly accessible prototype
7.3.1 Streamlit Cloud Deployment (Recommended)
Steps:

Push code to GitHub (public or private repo)
Go to https://share.streamlit.io
Connect GitHub account
Select repository and app.py
Add secrets (OpenAI API key) in Streamlit dashboard
Deploy

Secrets configuration:
toml# .streamlit/secrets.toml (don't commit this!)
OPENAI_API_KEY = "sk-..."
Access in code:
pythonimport streamlit as st
openai.api_key = st.secrets["OPENAI_API_KEY"]
7.3.2 Alternative: Video Demo
If hosting fails, record 3-min demo video covering:

 UI walkthrough (sample questions, scope)
 Factual query example (with citation)
 Advice refusal example
 Out-of-scope refusal example
 Source list quick view

Tools: Loom, OBS Studio, or QuickTime screen recording
Deliverable: Public Streamlit link OR demo video (YouTube/Google Drive)

Phase 8: Final Deliverables Assembly
Phase 8.1: Deliverables Checklist
Required for submission:

 Working prototype

Link: https://your-app.streamlit.app OR
Video: demo_video.mp4 (≤3 min)


 Source list

File: sources.csv (15–25 URLs)
Columns: source_id, url, source_type, scheme_name, description, last_accessed


 README

File: README.md
Sections: Scope, Tech Stack, Setup, Structure, Testing, Limitations, Sample Q&A, Disclaimer


 Sample Q&A

File: sample_qa.md
5–10 real queries with assistant answers + citations
Include both factual and refusal examples


 Disclaimer snippet

Text shown in UI
Copy from sidebar or footer of app




Phase 8.2: Sample Q&A Document
File: sample_qa.md
markdown# Sample Q&A - ICICI Prudential MF Facts Assistant

## Factual Queries

### Q1: What is the expense ratio of ICICI Prudential Large Cap Fund Direct Growth?

**Answer:**  
The Total Expense Ratio (TER) for ICICI Prudential Large Cap Fund Direct Growth is 0.42% as of March 2024. This is significantly lower than the regular plan due to the absence of distribution commissions.  
Source: https://www.icicipruamc.com/downloads/factsheet/large-cap-fund-mar2024.pdf  
Last updated: March 31, 2024

---

### Q2: What is the exit load for ICICI Prudential Multi Asset Fund?

**Answer:**  
The exit load is 1% if redeemed within 1 year from the date of allotment. No exit load is charged for redemptions after 1 year.  
Source: https://www.icicipruamc.com/investor-services/charges-and-fees  
Last updated: April 2024

---

### Q3: Minimum SIP amount for ICICI Prudential Nifty Next 50 Index Fund?

**Answer:**  
The minimum SIP amount is ₹100 per installment. You can start with as low as ₹100 per month.  
Source: https://www.icicipruamc.com/downloads/kim/nifty-next-50-index-fund.pdf  
Last updated: April 2024

---

### Q4: What is the benchmark of ICICI Prudential Large & Mid Cap Fund?

**Answer:**  
The benchmark index is Nifty Large Midcap 250 TRI (Total Return Index). The fund's performance is measured against this index.  
Source: https://www.icicipruamc.com/downloads/factsheet/large-midcap-fund-mar2024.pdf  
Last updated: March 31, 2024

---

### Q5: How do I download my capital gains statement?

**Answer:**  
You can download your capital gains statement from the Groww app/website under "Reports" or request it via email from ICICI Prudential investor services. The Consolidated Account Statement (CAS) also includes capital gains details.  
Source: https://www.icicipruamc.com/investor-services/download-statements  
Last updated: April 2024

---

## Refusal Examples

### Q6: Should I invest in ICICI Prudential Large Cap Fund?

**Answer:**  
I provide facts only, not investment advice. For personalized portfolio guidance, please consult a SEBI-registered investment advisor.

📚 Learn more:  
- SEBI Investor Awareness: https://investor.sebi.gov.in  
- Find SEBI-registered advisors: https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognised=yes

Would you like factual information about any of the 4 ICICI Prudential schemes instead?

---

### Q7: Which is better - Large Cap Fund or Multi Asset Fund?

**Answer:**  
I provide facts only, not investment advice. For personalized portfolio guidance, please consult a SEBI-registered investment advisor.

📚 Learn more:  
- SEBI Investor Awareness: https://investor.sebi.gov.in  
- Find SEBI-registered advisors: https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognised=yes

Would you like factual information about any of the 4 ICICI Prudential schemes instead?

---

### Q8: My redemption is pending for 3 days. Help!

**Answer:**  
I only answer factual questions about these 4 ICICI Prudential schemes:
1. Multi Asset Fund
2. Large Cap Fund
3. Nifty Next 50 Index Fund
4. Large & Mid Cap Fund

For account-related queries, please contact:  
- Groww Support: https://groww.in/help  
- ICICI Prudential Customer Care: 1860 266 7766

Can I help with facts about any of the above schemes?

---

### Q9: What are the tax implications of redeeming this fund?

**Answer:**  
I cannot provide tax advice. Tax treatment depends on holding period, fund category, and your individual tax situation.

For tax guidance:  
- Consult a chartered accountant or tax advisor  
- SEBI Investor Education: https://investor.sebi.gov.in/tax-and-mutual-funds

Can I help with other factual information about the scheme?

---

### Q10: My PAN is ABCDE1234F. Can I invest?

**Answer:**  
⚠️ Security Notice

I cannot process queries containing personal information (PAN).

Please remove sensitive details and ask your question again without:  
- PAN/Aadhaar numbers  
- Account numbers  
- Email addresses  
- Phone numbers  
- OTPs or passwords

How can I help with factual information about ICICI Prudential schemes?
Deliverable: sample_qa.md with 10 real Q&A examples