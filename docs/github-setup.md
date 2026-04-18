# GitHub Actions Setup Guide

## Overview
This guide explains how to set up GitHub Actions for the ICICI Prudential Mutual Fund RAG system.

## Required Secrets

### 1. Repository Secrets
Go to your GitHub repository Settings > Secrets and variables > Actions and add:

#### API Keys
- `OPENAI_API_KEY`: Your OpenAI API key (for embeddings and LLM)
- `ANTHROPIC_API_KEY`: Your Anthropic API key (optional, for Claude)

#### Deployment Secrets (if applicable)
- `VERCEL_TOKEN`: Vercel deployment token
- `AWS_ACCESS_KEY_ID`: AWS credentials (if deploying to AWS)
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `DOCKER_HUB_TOKEN`: Docker Hub token (if containerizing)

#### Notification Secrets
- `SLACK_WEBHOOK_URL`: Slack webhook for notifications
- `EMAIL_PASSWORD`: Email password for alerts (Gmail App Password)

### 2. Environment Variables
The workflows automatically use these environment variables:
- `PYTHON_VERSION`: '3.9'
- `NODE_VERSION`: '18'
- `CHROME_VERSION`: 'latest'

## Workflow Files Created

### 1. `.github/workflows/scraping.yml`
**Purpose**: Daily automated data scraping from Groww
**Schedule**: 9:15 AM Monday-Friday (market days)
**Triggers**:
- Scheduled runs
- Manual dispatch
- Pushes to phase1/ or config/ directories

**Features**:
- Chrome WebDriver setup
- Dependency caching
- Data validation
- Artifact upload
- Auto-commit changes

### 2. `.github/workflows/pipeline.yml`
**Purpose**: RAG pipeline orchestration (embeddings + vector DB)
**Schedule**: 9:30 AM Monday-Friday (after scraping)
**Triggers**:
- Scheduled runs
- Manual dispatch
- Pushes to phase2/, phase3/, or raw_data/

**Features**:
- Embedding generation with BGE model
- FAISS vector database updates
- Quality checks and validation
- LLM configuration testing
- Artifact management

### 3. `.github/workflows/deployment.yml`
**Purpose**: Production deployment pipeline
**Triggers**:
- Manual dispatch with environment selection
- Pushes to main branch
- Release publication

**Features**:
- Multi-environment deployment (staging/production)
- Build and test automation
- Security scanning
- Health checks
- Rollback capability

## Setup Instructions

### 1. Initialize Repository
```bash
git init
git add .
git commit -m "Initial commit with GitHub Actions workflows"
git branch -M main
git remote add origin https://github.com/yourusername/your-repo.git
git push -u origin main
```

### 2. Configure Secrets
1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Add each required secret from the list above

### 3. Test Workflows
```bash
# Test scraping workflow
gh workflow run scraping.yml

# Test pipeline workflow
gh workflow run pipeline.yml

# Test deployment workflow (staging)
gh workflow run deployment.yml -f environment=staging
```

### 4. Monitor Runs
- Go to Actions tab in your repository
- Monitor workflow runs
- Check logs for any issues
- Verify artifacts are uploaded correctly

## Workflow Dependencies

### Scraping Pipeline
```
scraping.yml (9:15 AM) 
  -> Generates raw_data/
  -> Uploads artifacts
```

### RAG Pipeline
```
pipeline.yml (9:30 AM)
  -> Downloads scraping artifacts
  -> Generates embeddings
  -> Updates vector database
  -> Runs quality checks
```

### Deployment Pipeline
```
deployment.yml (manual/release)
  -> Builds and tests
  -> Deploys to staging/production
  -> Runs health checks
```

## Troubleshooting

### Common Issues

1. **Chrome WebDriver Errors**
   - Ensure Chrome is installed in the runner
   - Check Chrome version compatibility

2. **Permission Errors**
   - Verify GITHUB_TOKEN has write permissions
   - Check repository settings for Actions permissions

3. **Secret Access**
   - Ensure secrets are properly configured
   - Check secret names match exactly

4. **Artifact Download Failures**
   - Verify previous workflow completed successfully
   - Check artifact retention periods

### Debug Mode
Add these steps to workflows for debugging:
```yaml
- name: Debug environment
  run: |
    echo "Current directory: $(pwd)"
    echo "Files: $(ls -la)"
    echo "Environment variables:"
    env | grep -E "^(GITHUB|PYTHON|NODE)"
```

## Best Practices

1. **Use Environment-Specific Secrets**
   - Separate staging and production secrets
   - Use different API keys for different environments

2. **Monitor Costs**
   - Set usage limits on API keys
   - Monitor workflow run frequency

3. **Security**
   - Regularly rotate API keys
   - Use least-privilege access
   - Enable dependency scanning

4. **Performance**
   - Use caching for dependencies
   - Optimize workflow run times
   - Monitor artifact sizes

## Next Steps

1. **Set up monitoring** for workflow failures
2. **Configure notifications** for important events
3. **Add integration tests** for critical components
4. **Set up backup workflows** for redundancy
5. **Document runbooks** for common issues
