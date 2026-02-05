# Financial Agents Backend - Support Agent

AI-basierter Support Agent für FAQ-basierte Kundenservice-Anfragen.

## Features

- **FAQ-basierte Antworten**: Semantic Search über Embeddings
- **Halluzinations-Prävention**: Nur Informationen aus der FAQ-Datenbank
- **Chat-History**: Kontext aus vorherigen Nachrichten
- **Ticket-System**: Eskalation zu menschlichem Support
- **Debug-Mode**: Detaillierte Informationen für Entwickler

## Setup

### 1. Dependencies installieren

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Variables setzen

```bash
cp .env.example .env
# Dann .env editieren und Werte eintragen
```

### 3. Server starten

```bash
python api_server.py
```

Server läuft auf `http://localhost:8080`

### 4. Testen ob es läuft

```bash
# Health Check
curl http://localhost:8080/health

# Chat testen
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hallo", "agent": "support"}'
```

## API Endpoints

| Endpoint | Method | Beschreibung |
|----------|--------|--------------|
| `/` | GET | API Info |
| `/health` | GET | Health Check |
| `/chat` | POST | Chat mit Support Agent |
| `/escalate` | POST | Support-Ticket erstellen |
| `/tickets` | GET | Alle Tickets abrufen |
| `/tickets/{id}` | GET | Einzelnes Ticket |
| `/feedback` | POST | Feedback speichern |

## Chat Request

```json
{
  "message": "Wie setze ich mein Passwort zurück?",
  "agent": "support",
  "chat_history": [],
  "debug": false
}
```

## Chat Response

```json
{
  "response": "Um dein Passwort zurückzusetzen...",
  "suggestions": ["Weitere Frage 1", "Weitere Frage 2"],
  "escalate": false,
  "debug_info": null
}
```

## Deployment

### Server

1. Repository klonen
2. Python 3.9+ installieren (falls nicht vorhanden)
3. Dependencies installieren: `pip install -r requirements.txt`
4. `.env` Datei mit Credentials anlegen
5. Server starten: `python api_server.py`

Der Server läuft standardmäßig auf Port 8080. Port kann via `PORT` Environment Variable geändert werden.

### Mit Systemd (Linux)

```ini
[Unit]
Description=Financial Agents API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
EnvironmentFile=/path/to/backend/.env
ExecStart=/path/to/venv/bin/python api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Mit Docker (optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "api_server.py"]
```

## Datenbank-Tabellen (Supabase)

### documents (FAQs)
```sql
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  source_url TEXT,
  embedding VECTOR(1536)
);
```

### support_tickets
```sql
CREATE TABLE support_tickets (
  id SERIAL PRIMARY KEY,
  user_message TEXT NOT NULL,
  chat_history JSONB,
  status TEXT DEFAULT 'open',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  resolved_at TIMESTAMPTZ
);
```

### agent_requests (Logging)
```sql
CREATE TABLE agent_requests (
  id SERIAL PRIMARY KEY,
  request_id TEXT,
  agent TEXT,
  user_message TEXT,
  response TEXT,
  processing_time_ms INTEGER,
  model TEXT,
  input_tokens INTEGER,
  output_tokens INTEGER,
  cost_usd DECIMAL,
  confidence DECIMAL,
  hallucination_risk TEXT,
  data_points_count INTEGER,
  debug_info JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### message_feedback
```sql
CREATE TABLE message_feedback (
  id SERIAL PRIMARY KEY,
  agent_slug TEXT,
  user_message TEXT,
  assistant_response TEXT,
  feedback_type TEXT,
  feedback_comment TEXT,
  session_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```
