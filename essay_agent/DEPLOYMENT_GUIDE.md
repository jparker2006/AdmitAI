# Essay Agent Deployment Guide

## Overview

This guide covers deploying the modern Essay Agent system (post-TASK-008 cleanup) to production environments. The system has been streamlined from a complex conversation management architecture to a clean ReAct agent system, reducing complexity by 92% while maintaining full functionality.

## System Requirements

### Hardware Requirements
- **CPU**: 2+ cores (4+ recommended for production)
- **Memory**: 4GB RAM minimum (8GB+ recommended)
- **Storage**: 1GB free space (5GB+ recommended with logging)
- **Network**: Stable internet connection for OpenAI API calls

### Software Requirements
- **Python**: 3.9+ (3.11+ recommended)
- **Operating System**: Linux, macOS, or Windows
- **Dependencies**: Listed in `requirements.txt`

## Pre-Deployment Checklist

### ✅ Environment Setup
- [ ] Python 3.9+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed from `requirements.txt`
- [ ] OpenAI API key obtained and configured
- [ ] Environment variables set (see Configuration section)

### ✅ System Validation
- [ ] All import tests pass: `python -c "import essay_agent; print('✅ Package ready')"`
- [ ] Tool registry loaded: `python -c "from essay_agent.tools import REGISTRY; print(f'{len(REGISTRY)} tools')"`
- [ ] ReAct agent available: `python -c "from essay_agent.agent.core.react_agent import EssayReActAgent; print('✅ ReAct ready')"`
- [ ] CLI functional: `essay-agent --help`

### ✅ Performance Validation
- [ ] Package import time < 2 seconds
- [ ] CLI startup time < 1 second
- [ ] Memory usage < 12MB baseline
- [ ] Demo runs successfully: `python -m essay_agent.demo --use-react`

## Installation Methods

### Method 1: Direct Installation (Recommended)

```bash
# 1. Clone repository
git clone <repository-url>
cd AdmitAI

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install package in development mode
pip install -e .

# 5. Verify installation
essay-agent --help
```

### Method 2: Production Package Installation

```bash
# 1. Install from package (when available)
pip install essay-agent

# 2. Verify installation
essay-agent --help
python -c "import essay_agent; print('Installation successful')"
```

### Method 3: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY essay_agent/ ./essay_agent/
COPY setup.py .

# Install package
RUN pip install -e .

# Set environment variables
ENV PYTHONPATH=/app
ENV ESSAY_AGENT_FAST_TEST=1

# Create non-root user
RUN useradd -m -u 1000 essayagent
USER essayagent

# Expose port (if web interface added)
EXPOSE 8000

# Default command
CMD ["essay-agent", "--help"]
```

```bash
# Build and run Docker container
docker build -t essay-agent .
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY essay-agent
```

## Configuration

### Environment Variables

#### Required Variables
```bash
# OpenAI API Configuration
export OPENAI_API_KEY="sk-your-openai-api-key-here"
```

#### Optional Variables
```bash
# Performance Tuning
export ESSAY_AGENT_FAST_TEST=1              # Skip sleeps during testing
export ESSAY_AGENT_DEBUG_WARNINGS=0         # Suppress LangChain warnings
export ESSAY_AGENT_MAX_RETRIES=3             # Tool execution retries
export ESSAY_AGENT_TIMEOUT=30                # Request timeout (seconds)

# Logging Configuration  
export ESSAY_AGENT_LOG_LEVEL=INFO           # DEBUG, INFO, WARNING, ERROR
export ESSAY_AGENT_LOG_FILE=essay_agent.log # Log file path
export ESSAY_AGENT_LOG_MAX_SIZE=10MB         # Log rotation size

# Memory Configuration
export ESSAY_AGENT_MEMORY_DIR=./memory_store # Memory storage directory
export ESSAY_AGENT_CACHE_SIZE=1000          # LRU cache size
export ESSAY_AGENT_VECTOR_DIM=1536          # Vector embedding dimensions

# Rate Limiting
export ESSAY_AGENT_RATE_LIMIT=60            # Requests per minute
export ESSAY_AGENT_BURST_LIMIT=10           # Burst requests
```

### Configuration File (Optional)

Create `essay_agent_config.yaml`:

```yaml
# Essay Agent Configuration
api:
  openai_key: ${OPENAI_API_KEY}
  model: "gpt-4"
  temperature: 0.1
  max_tokens: 4000
  
performance:
  max_retries: 3
  timeout: 30
  fast_test: true
  
logging:
  level: INFO
  file: essay_agent.log
  max_size: 10MB
  
memory:
  storage_dir: ./memory_store
  cache_size: 1000
  vector_dimensions: 1536
  
rate_limiting:
  requests_per_minute: 60
  burst_limit: 10
```

## Deployment Architectures

### 1. Single-Server Deployment

**Use Case**: Small teams, development, testing

```
┌─────────────────┐
│   Load Balancer │
└─────────┬───────┘
          │
┌─────────▼───────┐
│  Essay Agent    │
│  - ReAct Agent  │
│  - Tool Registry│
│  - Memory Store │
└─────────────────┘
```

**Specs**:
- 1 server (4 CPU, 8GB RAM)
- Local file storage
- Direct OpenAI API access

### 2. Multi-Server Deployment

**Use Case**: Production workloads, high availability

```
┌─────────────────┐
│   Load Balancer │
└─────┬─────┬─────┘
      │     │
┌─────▼─┐ ┌─▼─────┐
│Agent 1│ │Agent 2│
└───┬───┘ └───┬───┘
    │         │
┌───▼─────────▼───┐
│ Shared Memory   │
│ Store (Redis)   │
└─────────────────┘
```

**Specs**:
- 2+ servers (4 CPU, 8GB RAM each)
- Shared Redis for memory
- Load balancing

### 3. Microservices Deployment

**Use Case**: Large scale, containerized environments

```
┌──────────────────┐
│   API Gateway    │
└─────┬──────┬─────┘
      │      │
┌─────▼──┐ ┌─▼─────┐
│Agent   │ │Tools  │
│Service │ │Service│
└────┬───┘ └───┬───┘
     │         │
┌────▼─────────▼───┐
│ Memory Service   │
│ (PostgreSQL +    │
│  Vector DB)      │
└──────────────────┘
```

**Components**:
- Agent Service (ReAct reasoning)
- Tools Service (essay tools)
- Memory Service (persistence)
- API Gateway (routing)

## Production Optimization

### Performance Tuning

#### 1. Memory Optimization
```python
# In production configuration
MEMORY_CONFIG = {
    "cache_size": 5000,           # Increase cache
    "vector_batch_size": 100,     # Batch operations
    "cleanup_interval": 3600,     # Hourly cleanup
    "max_memory_usage": "1GB"     # Memory limits
}
```

#### 2. API Rate Limiting
```python
# Rate limiting configuration
RATE_LIMITS = {
    "openai_rpm": 60,            # Requests per minute
    "burst_allowance": 10,       # Burst requests
    "retry_backoff": [1, 2, 4],  # Exponential backoff
    "circuit_breaker": True      # Fail fast on errors
}
```

#### 3. Caching Strategy
```python
# Multi-level caching
CACHE_CONFIG = {
    "l1_cache": "memory",        # In-memory (fastest)
    "l2_cache": "redis",         # Shared cache
    "l3_cache": "disk",          # Persistent cache
    "ttl": 3600,                 # 1 hour TTL
}
```

### Monitoring & Observability

#### 1. Health Checks
```bash
# Basic health check endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime": 3600,
  "tools_loaded": 36,
  "memory_usage": "8.5MB"
}
```

#### 2. Metrics Collection
```python
# Key metrics to monitor
METRICS = [
    "request_count",
    "response_time_p95", 
    "error_rate",
    "tool_usage_frequency",
    "memory_utilization",
    "api_quota_usage"
]
```

#### 3. Logging Configuration
```python
# Production logging setup
LOGGING_CONFIG = {
    "version": 1,
    "handlers": {
        "file": {
            "class": "RotatingFileHandler",
            "filename": "essay_agent.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        },
        "console": {
            "class": "StreamHandler",
            "level": "INFO"
        }
    },
    "loggers": {
        "essay_agent": {
            "handlers": ["file", "console"],
            "level": "INFO"
        }
    }
}
```

## Security Considerations

### 1. API Key Management
```bash
# Use secret management systems
export OPENAI_API_KEY=$(vault kv get -field=api_key secret/openai)

# Rotate keys regularly
# Monitor API usage
# Set spending limits
```

### 2. Input Validation
```python
# All user inputs are validated
INPUT_VALIDATION = {
    "max_prompt_length": 5000,
    "allowed_characters": r"[a-zA-Z0-9\s\.,!?;:\-\(\)']",
    "sanitize_html": True,
    "rate_limit_per_user": 100  # requests per hour
}
```

### 3. Network Security
```bash
# Firewall rules
ufw allow 22/tcp     # SSH
ufw allow 80/tcp     # HTTP
ufw allow 443/tcp    # HTTPS
ufw deny 8000/tcp    # Block direct access to app

# SSL/TLS termination
# Use reverse proxy (nginx)
# Enable HTTPS only
```

## Backup & Recovery

### 1. Data Backup
```bash
# Memory store backup
tar -czf memory_backup_$(date +%Y%m%d).tar.gz memory_store/

# Configuration backup
cp essay_agent_config.yaml config_backup_$(date +%Y%m%d).yaml

# Automated daily backups
0 2 * * * /path/to/backup_script.sh
```

### 2. Disaster Recovery
```bash
# Recovery procedure
1. Restore from backup
2. Verify configuration
3. Test system functionality
4. Resume normal operations

# Recovery time objective: < 1 hour
# Recovery point objective: < 24 hours
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Symptom: ModuleNotFoundError
# Solution: Check Python path and virtual environment
export PYTHONPATH=$PYTHONPATH:/path/to/essay_agent
source venv/bin/activate
```

#### 2. OpenAI API Errors
```bash
# Symptom: API authentication failed
# Solution: Verify API key and quota
echo $OPENAI_API_KEY | head -c 20  # Check key format
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

#### 3. Memory Issues
```bash
# Symptom: High memory usage
# Solution: Restart service, check for memory leaks
ps aux | grep essay_agent  # Check memory usage
systemctl restart essay-agent
```

#### 4. Performance Issues
```bash
# Symptom: Slow response times
# Solution: Check API latency, increase cache
curl -w "@curl-format.txt" http://localhost:8000/health
redis-cli info memory  # Check cache usage
```

### Debug Mode
```bash
# Enable debug logging
export ESSAY_AGENT_DEBUG_WARNINGS=1
export ESSAY_AGENT_LOG_LEVEL=DEBUG

# Run with verbose output
essay-agent chat --debug --verbose
```

## Maintenance

### Regular Tasks
- [ ] **Daily**: Monitor logs and metrics
- [ ] **Weekly**: Check API usage and costs
- [ ] **Monthly**: Update dependencies
- [ ] **Quarterly**: Review performance metrics
- [ ] **Annually**: Audit security configuration

### Updates
```bash
# Update process
1. Backup current installation
2. Test updates in staging
3. Deploy during maintenance window
4. Verify functionality
5. Rollback if issues detected
```

## Support

### Documentation
- **Architecture**: `ARCHITECTURE_ANALYSIS.md`
- **Performance**: `PERFORMANCE_ANALYSIS.md`
- **Legacy**: `archive/README.md`

### Community
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: Wiki

---

**Deployment Guide Version**: 2.0.0  
**Last Updated**: July 15, 2025  
**Compatible With**: Essay Agent v2.0+ (Post-TASK-008) 