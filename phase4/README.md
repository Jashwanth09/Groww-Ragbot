# Phase 4: API Development & Web Interface

## Overview
This phase implements the API layer and web interface for the ICICI Prudential Mutual Fund RAG system, enabling users to interact with the system through a user-friendly interface.

## Phase Structure

### Phase 4.1: API Development
**Objective**: Create REST API endpoints for the RAG system
- FastAPI backend for query processing
- Integration with Phase 2 retrieval pipeline
- Integration with Phase 3 LLM generation
- Error handling and validation
- Rate limiting and security

### Phase 4.2: Streamlit Web Interface
**Objective**: Build user-friendly web application
- Query input interface
- Answer display with citations
- Chat history
- Scheme information display
- Mobile-responsive design

### Phase 4.3: Deployment
**Objective**: Deploy to Streamlit Cloud
- Streamlit Cloud hosting
- Environment variable management
- Performance optimization
- Monitoring and logging

## Files Description

### API Layer (`api/`)
- **`main.py`** - FastAPI application entry point
- **`routers/`** - API route handlers
- **`models/`** - Pydantic models
- **`services/`** - Business logic services
- **`middleware/`** - Custom middleware

### Web Interface (`web/`)
- **`app.py`** - Streamlit application
- **`components/`** - UI components
- **`utils/`** - Helper functions
- **`config/`** - Configuration files

### Phase 4 Documentation
- **`README.md`** - This file
- **`api_documentation.md`** - API docs
- **`deployment_guide.md`** - Deployment instructions

## Current Status

### Completed ✅
- Directory structure created
- GitHub Actions workflows ready
- Phase 1-3 foundation complete

### In Progress 🔄
- API development
- Streamlit interface
- LLM integration completion

### Next Steps
1. Complete Phase 3 LLM integration
2. Build FastAPI endpoints
3. Create Streamlit interface
4. Deploy to Streamlit Cloud

## Dependencies

### API Dependencies
```bash
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
python-multipart>=0.0.6
httpx>=0.25.0
```

### Web Dependencies
```bash
streamlit>=1.28.0
streamlit-chat>=0.1.0
plotly>=5.17.0
pandas>=2.1.0
```

## API Endpoints Design

### Core Endpoints
```
POST /api/query
- Input: Query text
- Output: Answer with citations

GET /api/schemes
- Output: List of supported schemes

GET /api/health
- Output: System health status

POST /api/feedback
- Input: Query, answer, rating
- Output: Feedback acknowledgment
```

## Web Interface Design

### Main Features
1. **Query Input**: Text input for user questions
2. **Answer Display**: Formatted answers with citations
3. **Chat History**: Previous queries and answers
4. **Scheme Info**: Quick access to scheme details
5. **Help Section**: Usage instructions and scope

### UI Components
- Header with branding
- Query input box
- Answer display area
- Chat history sidebar
- Footer with links

## Integration Points

### With Phase 2 (Retrieval)
- FAISS vector database access
- Semantic search functionality
- Chunk metadata retrieval

### With Phase 3 (LLM)
- Answer generation pipeline
- Citation extraction
- Out-of-scope detection

### With Phase 1 (Data)
- Real-time data access
- Scheme information
- Latest NAV and returns

## Security Considerations

### Input Validation
- Query length limits
- Content filtering
- Rate limiting

### API Security
- API key authentication (optional)
- CORS configuration
- Request logging

### Data Privacy
- No PII storage
- Query logging (optional)
- Secure secret management

## Performance Optimization

### Caching
- Answer caching for common queries
- Vector database caching
- Static asset optimization

### Scalability
- Async API endpoints
- Efficient vector search
- Resource optimization

## Monitoring

### Metrics
- Query volume
- Response times
- Error rates
- User feedback

### Logging
- Query logs
- Error tracking
- Performance metrics

## Next Steps

1. **Complete Phase 3**: Finish LLM integration
2. **Build API**: Create FastAPI endpoints
3. **Develop UI**: Build Streamlit interface
4. **Test Integration**: End-to-end testing
5. **Deploy**: Launch on Streamlit Cloud
6. **Monitor**: Set up monitoring and logging
