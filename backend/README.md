# Financial Agents Backend

AI-basierter Support Agent.

## Setup

### 1. PostgreSQL Datenbank einrichten

```bash
# Datenbank erstellen
createdb financial_agents

# Schema importieren
psql financial_agents < schema.sql
```

### 2. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Die `.env` Datei wird separat bereitgestellt.

### 4. Server starten

```bash
python api_server.py
```

Server läuft auf `http://localhost:8080`

### 5. Testen ob es läuft

```bash
# Health Check
curl http://localhost:8080/health

# Erwartete Antwort:
# {"status":"ok","version":"1.0.0"}
```

## Deployment

### Als Service (Systemd)

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

## Anforderungen

- Python 3.9+
- PostgreSQL 14+ (mit pgvector Extension)
- Internetzugang (für OpenAI API)
