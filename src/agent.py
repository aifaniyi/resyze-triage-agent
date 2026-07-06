import json
import logging

from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.config import settings

logger = logging.getLogger(__name__)

TRIAGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an SRE triage agent for the Resyze platform.
When an alert fires, you investigate the root cause using Grafana dashboards, Prometheus metrics, and Loki logs.

Your investigation process:
1. Identify the affected service from the alert labels
2. Query relevant metrics around the alert time window
3. Check logs for errors in the affected service
4. Look at related services for cascading failures
5. Produce a concise root cause analysis with:
   - What happened
   - Why it happened (root cause)
   - Impact assessment
   - Recommended remediation steps

Be specific — include metric values, log snippets, and timestamps in your analysis.
"""),
    ("human", """Investigate this alert:

Alert: {alert_name}
Severity: {severity}
Service: {service}
Description: {description}
Started At: {starts_at}
Labels: {labels}
"""),
    ("placeholder", "{agent_scratchpad}"),
])


def _get_llm():
    if settings.llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.llm_api_key,
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
        )


async def investigate_alert(alert: dict) -> str:
    """Run the triage agent to investigate an alert using Grafana MCP tools."""
    mcp_client = MultiServerMCPClient(
        {
            "grafana": {
                "url": settings.grafana_mcp_url,
                "transport": "sse",
                "headers": {"Authorization": f"Bearer {settings.grafana_mcp_api_key}"},
            }
        }
    )
    tools = await mcp_client.get_tools()
    llm = _get_llm()

    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})

    prompt = TRIAGE_PROMPT.format_messages(
        alert_name=labels.get("alertname", "unknown"),
        severity=labels.get("severity", "unknown"),
        service=labels.get("service", "unknown"),
        description=annotations.get("description", "No description"),
        starts_at=alert.get("startsAt", "unknown"),
        labels=json.dumps(labels),
        agent_scratchpad=[],
    )

    agent = create_react_agent(llm, tools)
    result = await agent.ainvoke({"messages": prompt})

    return result["messages"][-1].content
