-- Financial Agents Database Schema
-- PostgreSQL

-- Extension für Vector-Embeddings (für FAQ Semantic Search)
CREATE EXTENSION IF NOT EXISTS vector;

-- FAQs mit Embeddings für Semantic Search
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    source_url TEXT,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Support Tickets
CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    user_message TEXT NOT NULL,
    chat_history JSONB,
    status TEXT DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- Request Logging für Monitoring
CREATE TABLE IF NOT EXISTS agent_requests (
    id SERIAL PRIMARY KEY,
    request_id TEXT,
    agent TEXT,
    user_message TEXT,
    response TEXT,
    processing_time_ms INTEGER,
    model TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10,6),
    confidence DECIMAL(3,2),
    hallucination_risk TEXT,
    data_points_count INTEGER,
    debug_info JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User Feedback
CREATE TABLE IF NOT EXISTS message_feedback (
    id SERIAL PRIMARY KEY,
    agent_slug TEXT,
    user_message TEXT,
    assistant_response TEXT,
    feedback_type TEXT,
    feedback_comment TEXT,
    session_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index für schnellere Suche
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_agent_requests_agent ON agent_requests(agent);
CREATE INDEX IF NOT EXISTS idx_agent_requests_created ON agent_requests(created_at);
