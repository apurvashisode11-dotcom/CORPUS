"""Workforce Builder: business description -> profile -> hired roles."""
import json

from sqlalchemy import delete

from . import config, memory
from .bus import MessageBus
from .i18n import t
from .llm import call_llm
from .models import Agent
from .roles import ROLES

KW = {
 "sells_physical_goods": ["clothing", "clothes", "jacket", "shop", "store", "product", "garment", "handmade", "bakery", "कपड़े", "कपडे", "दुकान"],
 "sells_services": ["service", "freelance", "consult", "design", "agency", "coaching", "tutor"],
 "sells_online": ["instagram", "website", "online", "whatsapp", "facebook", "shopify", "इंस्टाग्राम", "इन्स्टाग्राम", "ऑनलाइन", "वेबसाइट"],
 "takes_payments": ["sell", "shop", "store", "order", "pay", "invoice", "client", "customer", "बेच", "विक्री", "विकत"],
 "runs_promotions": ["ads", "marketing", "promotion", "campaign", "launch", "instagram", "इंस्टाग्राम", "इन्स्टाग्राम"],
 "has_customers": ["sell", "customer", "order", "client", "shop", "store", "बेच", "विक्री", "विकत", "ग्राहक"],
}


def rule_profile(text: str) -> dict:
    low = text.lower()
    return {k: any(w in low for w in words) for k, words in KW.items()}


async def extract_profile(text: str) -> dict:
    profile = rule_profile(text)  # always available, works offline
    if config.LLM_PROVIDER != "mock":
        try:
            raw = await call_llm("Fill this JSON about the business with true/false only: " + json.dumps(list(profile)), text, json_mode=True)
            profile.update({k: bool(v) for k, v in json.loads(raw).items() if k in profile})
        except Exception:
            pass
    return profile


async def build_workforce(sessions, bus: MessageBus, description: str, lang: str = "en") -> dict:
    profile = await extract_profile(description)
    roles = [r for r, d in ROLES.items() if d["when"](profile)]
    async with sessions() as s:
        await s.execute(delete(Agent))
        for r in roles:
            s.add(Agent(role=r, manager_role=None if r == "manager" else "manager", goals=ROLES[r]["goals"]))
        await s.commit()
    if not await memory.recall(sessions, "campaign click rate"):
        await memory.save(sessions, "Previous campaign click rate was 4.2%", "fact")  # sample data for the demo
    await bus.audit("system", "system", t(lang, "built", n=len(roles)), {"roles": roles})
    return {"profile": profile, "agents": [agent_view(r) for r in roles]}


def agent_view(role: str) -> dict:
    d = ROLES[role]
    return {"role": role, "title": d["title"], "goals": d["goals"], "reason": d["reason"], "kpis": d["kpis"]}
