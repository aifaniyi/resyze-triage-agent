
# Resyze Alert Triage Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   KUBERNETES CLUSTER                                     │
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           NAMESPACE: monitoring                                      │ │
│  │                                                                                      │ │
│  │  ┌──────────────┐       ┌──────────────┐       ┌──────────────┐                     │ │
│  │  │  Prometheus  │──────▶│   Grafana    │       │     Loki     │                     │ │
│  │  │              │       │              │       │              │                     │ │
│  │  │ - scrapes    │       │ - dashboards │       │ - log store  │                     │ │
│  │  │   /metrics   │       │ - alert UI   │       │              │                     │ │
│  │  │ - evaluates  │       │              │       │              │                     │ │
│  │  │   rules      │       │              │       │              │                     │ │
│  │  └──────┬───────┘       └──────┬───────┘       └──────────────┘                     │ │
│  │         │                      │                       ▲                             │ │
│  │         │ fires alert          │                       │                             │ │
│  │         ▼                      │                       │                             │ │
│  │  ┌──────────────┐              │                       │                             │ │
│  │  │ AlertManager │──────────────┘                       │                             │ │
│  │  │              │  (contact point: webhook)            │                             │ │
│  │  └──────┬───────┘                                      │                             │ │
│  │         │                                              │                             │ │
│  └─────────┼──────────────────────────────────────────────┼─────────────────────────────┘ │
│            │ POST /webhook/alert                          │ logs via promtail             │
│            ▼                                              │                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                            NAMESPACE: resyze                                         │ │
│  │                                                                                      │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐             │ │
│  │  │                    TRIAGE FLOW                                       │             │ │
│  │  │                                                                      │             │ │
│  │  │  ┌────────────────────┐        ┌────────────────────┐               │             │ │
│  │  │  │ resyze-triage-agent│───────▶│ grafana-mcp-server │               │             │ │
│  │  │  │                    │  MCP   │                    │               │             │ │
│  │  │  │ - receives alert   │  SSE   │ - queries metrics  │               │             │ │
│  │  │  │ - runs LLM agent   │◀───────│ - queries logs     │               │             │ │
│  │  │  │ - produces report  │        │ - queries dashboards│              │             │ │
│  │  │  └────────┬───────────┘        └────────────────────┘               │             │ │
│  │  │           │                                                          │             │ │
│  │  └───────────┼──────────────────────────────────────────────────────────┘             │ │
│  │              │ NATS publish                                                           │ │
│  │              │ (email.events)                                                         │ │
│  │              ▼                                                                        │ │
│  │  ┌──────────────────┐                                                                │ │
│  │  │       NATS       │                                                                │ │
│  │  └────────┬─────────┘                                                                │ │
│  │           │                                                                           │ │
│  │           ▼                                                                           │ │
│  │  ┌──────────────────┐         ┌──────────────────┐     ┌──────────────────┐          │ │
│  │  │  resyze-mailer   │         │    resyze-api    │     │ resyze-analytics │          │ │
│  │  │                  │         │                  │     │                  │          │ │
│  │  │ - sends triage   │         │ - /metrics ──────┼─────┼──▶ Prometheus    │          │ │
│  │  │   report email   │         │ - JSON logs ─────┼─────┼──▶ Loki         │          │ │
│  │  │                  │         │                  │     │                  │          │ │
│  │  └──────────────────┘         └──────────────────┘     └──────────────────┘          │ │
│  │                                                                                      │ │
│  └──────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘


## Flow Summary

1. Prometheus scrapes /metrics from resyze-api, resyze-analytics, resyze-mailer (via ServiceMonitors)
2. PrometheusRules evaluate alert conditions (error rates, latency, service down, etc.)
3. When an alert fires → AlertManager → Grafana webhook contact point
4. Grafana POSTs alert payload to resyze-triage-agent /webhook/alert
5. Triage agent invokes LLM (Gemini/OpenAI) with Grafana MCP tools
6. Grafana MCP server queries Prometheus metrics + Loki logs + dashboards on behalf of the agent
7. Agent produces root cause analysis report
8. Report is published to NATS (email.events subject)
9. resyze-mailer consumes the message and sends the triage report via email
```
