# Groww RAG Bot — ICICI Prudential facts assistant

Facts-only chatbot for four ICICI Prudential Direct Growth schemes. Built for a Groww-style FAQ demo: answers NAV, SIP, expense ratio, fund size, and risk from published fund data, and does not give investment advice.

**Covered schemes**

1. ICICI Prudential Multi Asset Fund Direct Growth  
2. ICICI Prudential Large Cap Fund Direct Growth  
3. ICICI Prudential Nifty Next 50 Index Direct Growth  
4. ICICI Prudential Top 100 Fund Direct Growth  

This is not affiliated with Groww or ICICI Prudential. Mutual fund investments are subject to market risks.

## How production is split

Vercel cannot run Chrome or a 24/7 scheduler. The public demo is split like this:

| Piece | Where it runs | What the recruiter sees |
|---|---|---|
| Website + chatbot | **Vercel** (FastAPI) | Public URL, chat widget |
| Scraper | **GitHub Actions** (Chrome + Selenium) | Fresh metrics in `data/latest_fund_data.json` |
| Scheduler | **GitHub Actions cron** (9:15 AM IST, weekdays) | Automatic refresh, then Vercel redeploys |

The Streamlit RAG app (`phase5/app.py`) is the local research prototype. It needs FAISS, embedding models, and an LLM key, so it is **not** what Vercel hosts.

## Deploy for a job submission

### 1. Push this repo to GitHub `main`

Include `app.py`, `chat_engine.py`, `vercel.json`, `requirements-vercel.txt`, `web/`, `data/latest_fund_data.json`, and `.github/workflows/scraping.yml`.

### 2. Deploy the chatbot on Vercel

1. Open [vercel.com](https://vercel.com) and import `Jashwanth09/Groww-Ragbot`.
2. Root directory: repository root (not `web/`).
3. Deploy. Vercel should detect FastAPI from `app.py`.
4. Put the live URL in your application (example: `https://your-app.vercel.app`).

Local preview of the same stack:

```bash
python -m pip install -r requirements-vercel.txt uvicorn
python -m uvicorn app:app --reload --port 8010
```

Then open http://127.0.0.1:8010 and use the chat button.

### 3. Turn on the scraper + scheduler

1. In GitHub: **Settings → Actions → General** → allow Actions, and allow the workflow to read/write contents (or leave default write for `GITHUB_TOKEN` if permitted).
2. Open **Actions → Refresh live fund data → Run workflow**.
3. If it succeeds, `data/latest_fund_data.json` updates and Vercel redeploys. Weekday 9:15 AM IST runs are automatic.

If Groww HTML changes and scrape fails, the last good JSON stays in the repo and the chatbot still works.

### 4. What to submit

- Live demo: Vercel URL  
- Repo: https://github.com/Jashwanth09/Groww-Ragbot  
- Source list: `phase7/sources.csv`  
- Sample Q&A: `phase7/sample_qa.md`  
- Disclaimer: facts only, no advice (shown in the UI)

Try on the live site: “What is SIP?”, “Large Cap Fund NAV”, “Exit load for Multi Asset Fund?”
