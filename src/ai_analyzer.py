"""AI-powered deep analysis via MiMo API."""
from __future__ import annotations
import os
import httpx

from .analyzer import RiskReport

MIMO_API_BASE = "https://api.xiaomimimo.com/v1"


def get_api_key() -> str | None:
    return os.environ.get("MIMO_API_KEY")


def ai_analyze_risk(report: RiskReport) -> str | None:
    """Send risk report to MiMo API for deeper analysis."""
    api_key = get_api_key()
    if not api_key:
        return None

    factors_summary = "\n".join(
        f"- {f.name} ({f.grade}, score {f.score}): {f.details}"
        for f in report.factors
    )

    prompt = f"""You are a DeFi security expert. Analyze this protocol risk report and provide deeper insights.

Protocol: {report.protocol.name}
Category: {report.protocol.category}
Chain: {report.protocol.chain}
Overall Grade: {report.overall_grade} (score: {report.overall_score:.1f}/100)

Risk Factors:
{factors_summary}

TVL: ${report.tvl_data.get('current_tvl', 0):,.0f}
Audits: {', '.join(report.protocol.audits) if report.protocol.audits else 'None known'}
Exploits: {'; '.join(report.protocol.exploits) if report.protocol.exploits else 'None known'}

Provide:
1. Additional risk factors not covered above
2. Comparison to similar protocols in the same category
3. Specific recommendations for users considering this protocol
4. Red flags or positive signals to watch for
5. Suggested position sizing based on risk profile

Format as concise markdown."""

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{MIMO_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "MiMo-v2.5",
                    "messages": [
                        {"role": "system", "content": "You are a DeFi security expert."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI analysis failed: {e}"
