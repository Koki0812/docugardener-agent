# DocuAlign AI - Architecture Documentation

> 詳細なシステムアーキテクチャと技術設計

---

## 📐 System Architecture Overview

```mermaid
graph TB
    subgraph "User Interface"
        User[👤 User]
        Dashboard[🖥️ Streamlit Dashboard<br/>Admin View + User View]
    end
    
    subgraph "Cloud Run Container"
        WebApp[Streamlit App<br/>Port 8501]
        Webhook[Flask Webhook<br/>Port 8080]
    end
    
    subgraph "Agentic Pipeline"
        Agent[🤖 LangGraph Agent]
        FetchNode[Fetch Documents]
        SearchNode[Search Related Docs]
        CompareTextNode[Compare Text<br/>Semantic Analysis]
        CompareImageNode[Compare Images<br/>Visual Freshness]
        SaveNode[Save to Firestore]
    end
    
    subgraph "Google Cloud Services"
        Gemini[✨ Vertex AI<br/>Gemini 1.5 Pro]
        GCS[📦 Cloud Storage<br/>Document Store]
        Firestore[🗄️ Firestore<br/>Results DB]
        Drive[📁 Google Drive<br/>Source Documents]
        SecretMgr[🔐 Secret Manager<br/>Credentials]
        Eventarc[⚡ Eventarc<br/>GCS Triggers]
    end
    
    User -->|Access| Dashboard
    Dashboard -->|Trigger Scan| Agent
    Dashboard -->|Admin Actions| WebApp
    Eventarc -->|File Upload Event| Webhook
    Webhook -->|Trigger| Agent
    
    Agent --> FetchNode
    FetchNode -->|Fetch| Drive
    FetchNode --> SearchNode
    SearchNode --> CompareTextNode
    CompareTextNode -->|AI Request| Gemini
    CompareTextNode --> CompareImageNode
    CompareImageNode -->|AI Request| Gemini
    CompareImageNode --> SaveNode
    SaveNode -->|Store| Firestore
    
    Agent -->|Upload Files| GCS
    Dashboard -->|Load Results| Firestore
    Dashboard -->|Preview Files| GCS
    WebApp -->|Load Secrets| SecretMgr
    
    style User fill:#E8F5E9
    style Dashboard fill:#E3F2FD
    style Agent fill:#FFF3E0
    style Gemini fill:#FCE4EC
    style Firestore fill:#F3E5F5
```

---

## 🔄 Data Flow Sequence

### 1. Document Scan Workflow

```mermaid
sequenceDiagram
    actor User
    participant Dashboard
    participant Agent
    participant Drive
    participant Gemini
    participant Firestore
    
    User->>Dashboard: Click "スキャン実行"
    Dashboard->>Agent: Trigger pipeline
    
    Note over Agent: LangGraph StateGraph execution
    
    Agent->>Drive: Fetch latest documents
    Drive-->>Agent: Document list
    
    loop For each document
        Agent->>Drive: Download content
        Drive-->>Agent: Document text + images
        
        Agent->>Gemini: Compare with related docs
        Gemini-->>Agent: Contradiction list
        
        Agent->>Gemini: Analyze images
        Gemini-->>Agent: Visual decay list
    end
    
    Agent->>Firestore: Save scan results
    Firestore-->>Agent: Success
    
    Agent-->>Dashboard: Pipeline complete
    Dashboard->>Firestore: Load latest results
    Firestore-->>Dashboard: Scan history
    Dashboard-->>User: Display issues
```

### 2. Human-in-the-Loop Approval

```mermaid
sequenceDiagram
    actor Admin
    participant Dashboard
    participant Firestore
    participant Docs[Google Docs API]
    
    Dashboard->>Firestore: Load pending issues
    Firestore-->>Dashboard: Issue list
    Dashboard-->>Admin: Display for review
    
    Admin->>Dashboard: Approve / Deny
    
    alt Approved
        Dashboard->>Firestore: Mark as approved
        Dashboard->>Docs: Apply fix (future)
        Docs-->>Dashboard: Success
    else Denied
        Dashboard->>Firestore: Mark as denied
    end
    
    Dashboard-->>Admin: Update UI
```

---

## 🧩 Component Architecture

### LangGraph Pipeline Nodes

```mermaid
graph LR
    Start((Start)) --> Init[Initialize State]
    Init --> Fetch[fetch_source_docs]
    Fetch --> Search[search_related_docs]
    Search --> CompareText[compare_text_node]
    CompareText --> CompareImg[compare_images_node]
    CompareImg --> Save[save_results_node]
    Save --> End((End))
    
    style Start fill:#4CAF50
    style End fill:#F44336
    style CompareText fill:#FF9800
    style CompareImg fill:#FF9800
```

**Node Descriptions**:

| Node | Purpose | AI Integration |
|------|---------|----------------|
| `fetch_source_docs` | Google Drive から最新ドキュメントを取得 | - |
| `search_related_docs` | 関連する旧バージョンを検索 | Vertex AI Agent Builder |
| `compare_text_node` | テキストの意味的矛盾を検出 | Gemini 1.5 Pro (2M Context) |
| `compare_images_node` | スクリーンショットの鮮度をチェック | Gemini Multimodal (Vision) |
| `save_results_node` | 結果を Firestore に保存 | - |

---

## 🗄️ Data Model

### Firestore Schema

```
scan_results (Collection)
├── {scan_id} (Document)
│   ├── scan_id: string
│   ├── file_name: string
│   ├── triggered_at: timestamp
│   ├── status: "completed" | "failed"
│   ├── contradictions: array<Contradiction>
│   │   ├── category: string
│   │   ├── severity: "critical" | "warning" | "info"
│   │   ├── old_text: string
│   │   ├── new_text: string
│   │   ├── message: string
│   │   ├── suggestion: string
│   │   └── old_doc: string
│   ├── visual_decays: array<VisualDecay>
│   │   ├── category: string
│   │   ├── severity: "critical" | "warning"
│   │   ├── description: string
│   │   ├── suggestion: string
│   │   └── type: "screenshot_outdated" | "ui_change"
│   └── related_docs: array<string>
```

### Session State (Streamlit)

```python
st.session_state = {
    "agent_logs": [],
    "agent_results": dict,
    "scan_history": list[dict],
    "review_status": {
        "{scan_id}_issue_{index}": "approved" | "denied" | "pending"
    },
    "review_reasons": {
        "{scan_id}_issue_{index}": string
    }
}
```

---

## 🔐 Security Architecture

```mermaid
graph TB
    subgraph "Secrets Management"
        EnvLocal[.env File<br/>Local Dev]
        SecretMgr[Secret Manager<br/>Production]
    end
    
    subgraph "Application"
        Settings[config/settings.py<br/>get_secret()]
    end
    
    subgraph "Services"
        Drive[Drive Service]
        Vertex[Vertex AI Service]
        Firestore[Firestore Service]
    end
    
    EnvLocal -.->|ENV != production| Settings
    SecretMgr -->|ENV == production| Settings
    Settings --> Drive
    Settings --> Vertex
    Settings --> Firestore
    
    style SecretMgr fill:#4CAF50
    style EnvLocal fill:#FF9800
```

**Security Best Practices**:
- ✅ Secret Manager for production credentials
- ✅ Environment variable fallback for local development
- ✅ No secrets in source code or Docker images
- ✅ IAM roles for service-to-service authentication
- ⬜ (Future) VPC connector for private networking

---

## 🚀 Deployment Architecture

```mermaid
graph TB
    subgraph "CI/CD Pipeline"
        GitHub[GitHub Repository]
        Actions[GitHub Actions]
        Build[Cloud Build]
    end
    
    subgraph "Cloud Run"
        Service[docugardener Service]
        Container[Docker Container<br/>Streamlit + Flask]
    end
    
    subgraph "Networking"
        LB[Load Balancer]
        IAP[Identity-Aware Proxy<br/>Future]
    end
    
    GitHub -->|Push to main| Actions
    Actions -->|Trigger| Build
    Build -->|Build & Push| GCR[Container Registry]
    GCR -->|Deploy| Service
    Service --> Container
    
    Internet[Internet] --> LB
    LB --> Service
    
    style Service fill:#4285F4
    style Container fill:#34A853
```

**Deployment Configuration**:
- **Platform**: Cloud Run (fully managed)
- **Region**: `asia-northeast1`
- **Scaling**: 0 to 10 instances (auto-scaling)
- **Memory**: 2GB
- **CPU**: 2 vCPU
- **Concurrency**: 80 requests per instance
- **Timeout**: 300 seconds

---

## 📊 Infrastructure Costs (Estimated)

| Service | Usage | Estimated Monthly Cost |
|---------|-------|------------------------|
| Cloud Run | ~1000 requests/month | $0.50 |
| Firestore | ~10K reads, 1K writes | $0.20 |
| Cloud Storage | 10GB, 100 operations | $0.30 |
| Vertex AI (Gemini) | ~100K tokens/month | $5.00 |
| Secret Manager | 3 secrets, 100 accesses | $0.10 |
| **Total** | | **~$6.10/month** |

> **Note**: Costs may vary based on actual usage. Hackathon projects within free tier limits may incur $0 cost.

---

## 🔮 Future Architecture Enhancements

```mermaid
graph TB
    subgraph "Phase 2 Enhancements"
        RAG[RAG System<br/>Vertex AI Vector Search]
        PubSub[Real-time Notifications<br/>Cloud Pub/Sub]
        Tasks[Async Processing<br/>Cloud Tasks]
        BigQuery[Analytics<br/>BigQuery]
    end
    
    subgraph "Phase 3 Enterprise"
        VPC[VPC Connector<br/>Private Networking]
        CDN[Cloud CDN<br/>Static Assets]
        Monitoring[Cloud Monitoring<br/>+ Alerting]
        SSO[Workspace SSO<br/>Enterprise Auth]
    end
    
    style RAG fill:#FFF9C4
    style PubSub fill:#FFF9C4
    style VPC fill:#E1F5FE
    style SSO fill:#E1F5FE
```

**Planned Features**:
1. **RAG Integration**: Learn from past approvals/denials
2. **Real-time Notifications**: Slack/Email alerts on new issues
3. **Batch Processing**: Cloud Tasks for large document sets
4. **Advanced Analytics**: BigQuery for trend analysis
5. **Enterprise SSO**: Google Workspace integration

---

## 📚 Technology Stack Details

### Backend
- **Language**: Python 3.11
- **Agent Framework**: LangGraph 0.0.40+
- **AI SDK**: LangChain-Google-VertexAI 0.0.6+

### Frontend
- **Framework**: Streamlit 1.31.0+
- **Styling**: Custom CSS (Apple-inspired design)

### Infrastructure
- **Container**: Docker (multi-stage build)
- **Runtime**: Cloud Run (Python 3.11-slim)
- **Entrypoint**: Shell script (`entrypoint.sh`) running Streamlit + Flask concurrently

### APIs & Services
- **AI**: Vertex AI Gemini 1.5 Pro
- **Storage**: Google Cloud Storage + Firestore
- **Search**: Vertex AI Agent Builder (Discovery Engine)
- **Auth**: Google Drive API + OAuth 2.0

---

## 🛠️ Development Workflow

```mermaid
graph LR
    Dev[Local Development] -->|Push| GitHub
    GitHub -->|Webhook| Actions[GitHub Actions]
    Actions -->|Build| CloudBuild[Cloud Build]
    CloudBuild -->|Deploy| CloudRun[Cloud Run]
    CloudRun -->|Live| Production[Production URL]
    
    Dev -.->|Test Locally| LocalStreamlit[localhost:8501]
    
    style Dev fill:#E8F5E9
    style Production fill:#C8E6C9
```

1. **Local Development**: `streamlit run app.py`
2. **Commit & Push**: Git push to `main` branch
3. **CI/CD**: GitHub Actions triggers Cloud Build
4. **Build**: Docker container built & pushed to GCR
5. **Deploy**: Cloud Run automatically deploys new version
6. **Live**: Service available at production URL

---

## 🔗 Related Documentation

- [Secret Manager Setup](./secret_manager_setup.md)
- [Deployment Procedure](./deployment_procedure.md)
- [Troubleshooting Guide](./troubleshooting.md)
