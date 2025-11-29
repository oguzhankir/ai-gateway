# AI Gateway with PII Detection

**Academic Project** - Text Mining Course  
**Institution**: Istanbul Technical University (ITU)  
**Department**: Big Data & Business Analytics  
**Student**: Oğuzhan Kır  
**Course**: Text Mining

---

## 📋 Project Overview

This project is a **course assignment** for the Text Mining course at ITU's Big Data & Business Analytics program. The primary focus is **PII (Personally Identifiable Information) Detection** using text mining techniques, implemented within a comprehensive AI Gateway framework.

### ⚠️ Important Note

This is an **academic project** developed as a course assignment. While it includes many features of a production AI Gateway, it is implemented at a **basic/intermediate level** for educational purposes. A production-grade AI Gateway would require significantly more features, advanced security measures, comprehensive testing, scalability optimizations, and enterprise-level reliability.

**Many features are implemented in a simplified manner** to demonstrate concepts and meet course requirements. See the [Limitations & Future Work](#limitations--future-work) section for details on what would be needed for production deployment.

---

## 🎯 Primary Objective: PII Detection (Text Mining Focus)

The core assignment requirement is **PII detection in text** using text mining methodologies. This project implements:

- **Multi-language PII Detection** (Turkish & English)
- **Hybrid Detection Approach**: Regex patterns + NLP Named Entity Recognition (NER)
- **Real-time PII Masking/Unmasking** for secure processing
- **Guardrails System** to prevent PII leakage in LLM outputs
- **Comprehensive PII Entity Types**: TCKN, Phone Numbers, Email, IBAN, Credit Cards, Addresses, etc.

### Text Mining Techniques Used

1. **Pattern-Based Detection (Regex)**
   - Turkish phone number patterns: `05XX XXX XX XX`, `+90 5XX XXX XX XX`
   - Email validation: RFC-compliant regex
   - TCKN (Turkish ID) validation: 11-digit with checksum
   - IBAN validation: Country-specific formats with checksum
   - Credit card detection: Luhn algorithm validation

2. **NLP-Based Detection (Named Entity Recognition)**
   - **spaCy Models**: 
     - `tr_core_news_lg` for Turkish text
     - `en_core_web_lg` for English text
   - Entity types: PERSON, ORGANIZATION, LOCATION, DATE, MONEY
   - Confidence scoring for detected entities

3. **Hybrid Approach**
   - Fast mode: Regex-only (low latency)
   - Detailed mode: Regex + NLP (higher accuracy)
   - Confidence-based filtering
   - Entity merging and deduplication

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Request                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Gateway                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Authentication & Rate Limiting                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                        │                                     │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  PII Detection (Text Mining)                         │  │
│  │  • Regex Patterns                                     │  │
│  │  • spaCy NER (Turkish/English)                       │  │
│  │  • Confidence Scoring                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                        │                                     │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Guardrails Check                                     │  │
│  │  • PII Validation                                     │  │
│  │  • Content Filtering                                  │  │
│  │  • Threshold Checks                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                        │                                     │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  PII Masking (Redis Session Store)                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                        │                                     │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Semantic Cache Lookup                               │  │
│  │  • Vector Embeddings (OpenAI/Gemini)                │  │
│  │  • Cosine Similarity Search                          │  │
│  │  • Threshold: 0.85                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                        │                                     │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Budget Check                                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                        │                                     │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LLM Provider (OpenAI / Gemini)                     │  │
│  │  • Fallback Mechanism                                │  │
│  │  • A/B Testing Support                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                        │                                     │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Output PII Detection & Guardrails                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                        │                                     │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  PII Unmasking                                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                        │                                     │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Audit Logging (PostgreSQL/TimescaleDB)              │  │
│  │  • Request Logs                                      │  │
│  │  • Guardrail Violations                              │  │
│  │  • Analytics Data                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                        │                                     │
│                        ▼                                     │
│                    Response                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Technical Deep Dive

### 1. PII Detection Methodology

#### Pattern-Based Detection (Regex)

**Turkish Phone Numbers**:
```python
# Patterns: 05XX XXX XX XX, +90 5XX XXX XX XX, 5XX XXX XX XX
pattern = r'(\+?90\s?)?(0?5\d{2})\s?(\d{3})\s?(\d{2})\s?(\d{2})'
```

**TCKN (Turkish ID Number)**:
- 11 digits
- First digit cannot be 0
- Checksum validation using weighted sum

**IBAN**:
- Country code (2 letters)
- Check digits (2 digits)
- Account identifier (up to 30 alphanumeric)
- Mod-97 validation

**Credit Cards**:
- Luhn algorithm validation
- Pattern matching for major card types (Visa, Mastercard, Amex)

#### NLP-Based Detection (spaCy NER)

**Model Loading**:
```python
# Lazy loading with fallback
try:
    nlp_tr = spacy.load("tr_core_news_lg")
    nlp_en = spacy.load("en_core_web_lg")
except OSError:
    # Fallback to regex-only mode
    logger.warning("spaCy models not found, using regex-only detection")
```

**Entity Types Detected**:
- `PERSON`: Names of people
- `ORG`: Organizations
- `GPE`: Geopolitical entities (countries, cities)
- `LOC`: Locations
- `DATE`: Dates and times
- `MONEY`: Monetary values

**Confidence Scoring**:
- Regex matches: Confidence = 1.0 (exact match)
- NLP entities: Confidence from spaCy model (0.0 - 1.0)
- Threshold filtering: Only entities above 0.5 confidence

### 2. Semantic Caching

**Architecture**:
- **Storage**: Redis Hash (key-value pairs)
- **Vector Storage**: Binary format (numpy arrays)
- **Similarity Metric**: Cosine similarity
- **Threshold**: 0.85 (configurable)

**Process Flow**:
```
1. Generate embedding for query text (OpenAI/Gemini embeddings)
2. Scan Redis cache entries
3. Decode stored vectors
4. Calculate cosine similarity for each cached entry
5. Return best match if similarity >= threshold
6. Cache new responses with TTL (default: 3600s)
```

**Embedding Models**:
- Default: `text-embedding-3-small` (OpenAI)
- Dimension: 1536
- Alternative: Gemini `embedding-001`

**Limitations (Basic Implementation)**:
- Linear scan through all cache entries (O(n))
- No vector indexing (e.g., HNSW, FAISS)
- Single-threaded similarity calculation
- No cache eviction policy beyond TTL

**Production Requirements**:
- Vector database (Pinecone, Weaviate, Qdrant)
- Approximate Nearest Neighbor (ANN) search
- Hierarchical clustering
- Cache warming strategies
- Distributed caching

### 3. Guardrails System

**Rule Types**:
1. **Threshold Rules**: Max tokens, max cost
2. **PII Rules**: Block specific PII types in output
3. **Content Rules**: Regex-based content filtering

**Implementation**:
- Rule engine with configurable severity levels
- Action types: `block`, `log`, `alert`
- Violation logging to database
- Webhook notifications

**Basic Implementation**:
- Simple rule matching
- No ML-based content classification
- Basic regex patterns
- No context-aware filtering

### 4. Multi-Provider LLM Support

**Providers**:
- OpenAI (GPT-4, GPT-4o-mini, GPT-3.5-turbo)
- Google Gemini (gemini-2.5-flash-lite, gemini-pro)

**Features**:
- Provider abstraction layer
- Automatic fallback on failure
- A/B testing support
- Cost tracking per provider/model

**Basic Implementation**:
- Simple fallback chain
- No intelligent routing
- No load balancing
- No provider health monitoring

---

## 📊 Database Schema

### TimescaleDB Hypertable (Request Logs)

```sql
CREATE TABLE request_logs (
    id UUID,
    user_id UUID REFERENCES users(id),
    request_timestamp TIMESTAMP NOT NULL,
    provider VARCHAR(50),
    model VARCHAR(100),
    messages JSONB,
    completion TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    cost_usd FLOAT,
    duration_ms INTEGER,
    cache_hit BOOLEAN,
    pii_detected BOOLEAN,
    pii_entities JSONB,
    guardrail_violations JSONB,
    status VARCHAR(50),
    error_message TEXT,
    PRIMARY KEY (id, request_timestamp)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('request_logs', 'request_timestamp');
```

### Guardrail Logs

```sql
CREATE TABLE guardrail_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    request_id UUID,
    rule_name VARCHAR(100),
    severity VARCHAR(20),
    action VARCHAR(20),
    details JSONB,
    timestamp TIMESTAMP
);
```

---

## 🚀 Features

### Core Features (Text Mining Focus)

- ✅ **Multi-language PII Detection** (Turkish & English)
- ✅ **Hybrid Detection** (Regex + NLP)
- ✅ **Real-time Masking/Unmasking**
- ✅ **Guardrails for PII Protection**
- ✅ **Comprehensive Entity Types**

### Additional Features (AI Gateway)

- ✅ **Multi-Provider LLM Support** (OpenAI, Gemini)
- ✅ **Semantic Caching** (Vector similarity)
- ✅ **Rate Limiting** (Per-user tiers)
- ✅ **Budget Management** (Spending limits)
- ✅ **Analytics Dashboard** (Real-time metrics)
- ✅ **Streaming Support** (SSE)
- ✅ **Webhook Integration**
- ✅ **A/B Testing** (Provider routing)

---

## 🔒 Security & API Key Management

### ✅ API Keys Are NOT Exposed

**Environment Variables**:
- All API keys stored in `.env` file (gitignored)
- Never committed to repository
- Docker Compose reads from `.env` at runtime
- Frontend uses `NEXT_PUBLIC_*` prefix (build-time only)

**Security Measures**:
- API keys hashed with bcrypt before storage
- Admin API key in environment variables only
- No hardcoded keys in source code
- `.env.example` provided as template (no real keys)
- Default values in code are placeholders only (e.g., `dev-key-change-in-production`)

**Verification**:
```bash
# Check .gitignore includes .env
grep -r "\.env" .gitignore

# Verify no real API keys in codebase (should only show .env files which are gitignored)
grep -r "sk-proj\|AIzaSy" --exclude-dir=node_modules --exclude="*.md" --exclude="*.log" .
```

**See [SECURITY.md](SECURITY.md) for detailed security information.**

---

## 📦 Installation & Setup

### Prerequisites

- Docker and Docker Compose
- OpenAI API Key
- Google Gemini API Key

### Quick Start

1. **Clone repository**
   ```bash
   git clone <repository-url>
   ```

2. **Create `.env` file** (gitignored)
   ```bash
   cat > .env << EOF
   OPENAI_API_KEY=sk-your-key-here
   GEMINI_API_KEY=your-key-here
   SECRET_KEY=your-secret-key
   ADMIN_API_KEY=your-admin-key
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_gateway
   REDIS_URL=redis://localhost:6379/0
   EOF
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Access application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## 🧪 Testing

### Test Script

```bash
# Run comprehensive test suite
./test_providers.sh

# Tests include:
# - Basic messages (semantic cache)
# - PII detection (various types)
# - Guardrail violations
# - Provider fallback
```

### Manual PII Detection Test

```bash
curl -X POST http://localhost:8000/v1/detect-pii \
  -H "Authorization: Bearer <api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Benim telefon numaram 0532 123 45 67 ve email adresim test@example.com",
    "mode": "detailed"
  }'
```

---

## 📁 Project Structure

```
ai-gateway/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI endpoints
│   │   ├── core/             # Security, rate limiting, metrics
│   │   ├── providers/        # LLM provider implementations
│   │   ├── embeddings/       # Embedding providers
│   │   ├── pii/              # PII detection & masking (TEXT MINING CORE)
│   │   │   ├── detector.py  # Main detection logic
│   │   │   ├── patterns.py   # Regex patterns
│   │   │   ├── nlp_models.py # spaCy model loading
│   │   │   └── masker.py     # Masking/unmasking
│   │   ├── guardrails/       # Guardrails system
│   │   ├── cache/            # Semantic cache
│   │   ├── db/               # Database models & repositories
│   │   └── services/         # Business logic
│   ├── config/               # Configuration files
│   ├── scripts/              # Initialization scripts
│   └── alembic/              # Database migrations
├── frontend/
│   └── src/
│       ├── app/              # Next.js pages
│       ├── components/       # React components
│       └── hooks/            # Custom hooks
└── nginx/                    # Reverse proxy config
```

---

## ⚠️ Limitations & Future Work

### Current Limitations (Basic Implementation)

**PII Detection**:
- ❌ Limited to Turkish and English (no other languages)
- ❌ Basic regex patterns (may miss edge cases)
- ❌ No ML-based PII classification
- ❌ No context-aware detection
- ❌ No PII redaction in images/documents

**Semantic Cache**:
- ❌ Linear scan (O(n) complexity)
- ❌ No vector indexing
- ❌ Single-threaded similarity calculation
- ❌ No cache eviction policies
- ❌ No distributed caching

**Guardrails**:
- ❌ Basic rule matching
- ❌ No ML-based content classification
- ❌ Simple regex patterns
- ❌ No context-aware filtering

**Security**:
- ❌ Basic authentication (API keys only)
- ❌ No OAuth2/OIDC support
- ❌ No role-based access control (RBAC)
- ❌ No request signing/verification
- ❌ No DDoS protection

**Scalability**:
- ❌ Single-instance deployment
- ❌ No horizontal scaling
- ❌ No load balancing
- ❌ No auto-scaling
- ❌ Basic connection pooling

**Monitoring**:
- ❌ Basic Prometheus metrics
- ❌ No distributed tracing
- ❌ No APM integration
- ❌ Limited alerting

### Production Requirements (Not Implemented)

**Enterprise Features**:
- Multi-region deployment
- High availability (HA) setup
- Disaster recovery
- Blue-green deployments
- Canary releases
- Feature flags

**Advanced Security**:
- WAF (Web Application Firewall)
- DDoS protection
- Request signing
- IP whitelisting
- Advanced threat detection
- Compliance (GDPR, HIPAA, SOC2)

**Performance**:
- CDN integration
- Edge caching
- Request batching
- Connection pooling optimization
- Database read replicas
- Caching layers (multiple tiers)

**Observability**:
- Distributed tracing (Jaeger, Zipkin)
- APM (Application Performance Monitoring)
- Log aggregation (ELK, Loki)
- Advanced alerting (PagerDuty, Opsgenie)
- SLA monitoring

**Advanced Features**:
- Multi-tenant support
- Custom model fine-tuning
- Prompt templates
- Prompt versioning
- Cost optimization algorithms
- Intelligent routing
- Model performance comparison

---

## 📚 Academic Context

### Course: Text Mining

This project demonstrates text mining techniques in a real-world application:

1. **Text Preprocessing**: Tokenization, normalization
2. **Pattern Recognition**: Regex-based entity extraction
3. **Named Entity Recognition**: NLP-based entity detection
4. **Text Classification**: PII vs non-PII classification
5. **Information Extraction**: Structured data from unstructured text

### Learning Outcomes

- Understanding of PII detection methodologies
- Hybrid approach combining rule-based and ML-based techniques
- Real-world application of NLP libraries (spaCy)
- Text mining pipeline design
- Evaluation metrics for text mining systems


## 👤 Author

**Oğuzhan Kır**  
Istanbul Technical University  
Big Data & Business Analytics  
Text Mining Course Project