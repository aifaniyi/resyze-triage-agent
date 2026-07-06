# resyze-triage-agent

AI-powered alert triage agent that investigates Prometheus/Grafana alerts using the Grafana MCP server and sends root cause analysis reports via email.

## Architecture

```
Prometheus Alert → Grafana → Webhook Contact Point → resyze-triage-agent
                                                          │
                                                          ├── Grafana MCP Server (query metrics, logs, dashboards)
                                                          │
                                                          └── NATS → resyze-mailer (send triage report email)
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | HTTP server port | `8090` |
| `GRAFANA_MCP_URL` | Grafana MCP server SSE endpoint | `http://grafana-mcp-server.resyze.svc.cluster.local:8080/sse` |
| `LLM_PROVIDER` | LLM provider (`google` or `openai`) | `google` |
| `LLM_MODEL` | Model name | `gemini-2.0-flash` |
| `LLM_API_KEY` | API key for the LLM provider | — |
| `NATS_URL` | NATS server URL | `nats://localhost:4222` |
| `NATS_MAILER_SUBJECT` | NATS subject for mailer | `email.events` |
| `ALERT_RECIPIENT_EMAIL` | Email to receive triage reports | — |

## Local Development

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in values
uvicorn src.main:app --reload --port 8090
```

## Deployment

The agent runs in the `resyze` namespace alongside the Grafana MCP server.

```bash
kubectl apply -f ../resyze-k8s/apps/grafana-mcp-server/
kubectl apply -f ../resyze-k8s/apps/resyze-triage-agent/
```

## Grafana Setup

1. Create a Grafana service account with Viewer role
2. Generate a service account token
3. Store it in the `grafana-mcp-secret` k8s secret
4. Apply the alerting provisioning config from `resyze-k8s/infrastructure/monitoring/grafana/alerting.yaml`
