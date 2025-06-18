## Summary: LLMFiche Architecture (High-Level View)

### 1. **Data Lifecycle & Storage Strategy**

* **Ingestion**: `ficher` loads and preprocesses PDFs
* **Chunking**: Semantic, recursive splitting into \~300–500 token chunks
* **Storage**: Raw PDFs + chunked text stored locally; embeddings in Qdrant
* **Logs & history**: User queries, retrievals, and LLM responses logged in MongoDB (`historian`)
* **Hash-based document tracking** for re-ingestion and deduplication

---

### 2. **Embedding & Retrieval**

* **Embedding**: `text-embedding-3-small` (OpenAI) or local fallback (`bge-small`, etc.)
* **Chunk-level vectors** with metadata: doc ID, page, tags
* **Storage**: Qdrant used for dense vector storage with filtering payloads
* **Retrieval**: `agent` queries Qdrant directly, receives top-k chunks, and augments prompts with these

---

### 3. **Agent Orchestration Patterns**

* Uses **AutoGen** to modularly coordinate:

  * **RetrieverToolAgent**: queries Qdrant
  * **ResponderAgent**: composes answers
  * **HistorianAgent**: logs sessions
* Future expansion: session memory, reranking, tool chaining
* Agent remains stateless, uses tools for persistence and retrieval

---

### 4. **Inter-Component Communication**

* All components expose **FastAPI-based HTTP services**
* **Schemas shared** via Pydantic models in the `share` module
* **Docker Compose network** allows services to talk using container names
* Use `.env` files for config/secrets; internal traffic doesn't need auth

---

### 5. **Docker Compose & DevOps**

* One `docker-compose.yml` defines services, ports, volumes, networks
* Each service has its own Dockerfile (to be built later)
* `Makefile` used to streamline dev lifecycle
* Future: extend with `docker-compose.override.yml` for dev/prod separation

---

### 6. **Observability & Metrics**

* **Logging** with `loguru`, consistent across services
* **Metrics** via `prometheus_client`, expose `/metrics` on each API
* **Audit trail** via `historian`: logs input, context, output, latency, tokens used
* Future: Prometheus + Grafana dashboarding
* Note: **You want to revisit Prometheus later**

---

## Recommended Next Steps

To move from architecture to execution meaningfully and prepare for Codex-assisted development:

### Phase 1: Bootstrap the Monorepo

* [ ] Scaffold each `application/` subdirectory with minimal FastAPI apps
* [ ] Define shared Pydantic models in `share/schemas/`
* [ ] Add a working `docker-compose.yml` with `hello world` endpoints for each service
* [ ] Create `.env` with all environment variables used across components

### Phase 2: Implement Core Data Flow

* [ ] Build PDF ingestion + chunking pipeline in `ficher`
* [ ] Connect to Qdrant directly with a basic upsert/query API
* [ ] Add agent retrieval and response generation stub using OpenAI
* [ ] Start logging queries and responses to MongoDB in `historian`

### Phase 3: Observability Foundation

* [ ] Add `loguru` to all services with a consistent logger format
* [ ] Add `/metrics` endpoint with dummy counters
* [ ] Prepare a Prometheus + Grafana setup (can be staged in another Compose file)

### Phase 4: Codex Readiness

When you're ready to bring in Codex:

* [ ] Define task files (e.g. `agent/tasks.md`) with specs for each module
* [ ] Prepare minimal working skeletons to prompt Codex effectively
* [ ] Set up code-gen boundaries (e.g. where Codex generates handlers, not orchestration logic)
