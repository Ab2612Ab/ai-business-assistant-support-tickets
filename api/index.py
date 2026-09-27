from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
import re

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(
    title="AI Business Assistant & Customer Support API",
    version="1.0.0",
    description="Python/FastAPI support ticketing and AI-assisted business operations demo.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

Status = Literal["open", "in_progress", "waiting_customer", "resolved", "closed"]
Priority = Literal["low", "medium", "high", "urgent"]
Channel = Literal["email", "chat", "web", "phone"]

tickets: dict[str, dict] = {}
messages: dict[str, list[dict]] = {}
business_context = {
    "company": "Emmanx Digital",
    "hours": "Monday-Friday, 9:00-17:00 UTC",
    "services": ["Website Development", "Website Redesign", "WordPress", "E-commerce", "Technical Support"],
    "sla": {"urgent": "4 hours", "high": "8 hours", "medium": "1 business day", "low": "3 business days"},
}

class TicketCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=120)
    customer_email: EmailStr
    subject: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=5, max_length=5000)
    priority: Priority = "medium"
    channel: Channel = "web"
    tags: list[str] = Field(default_factory=list)

class TicketUpdate(BaseModel):
    status: Status | None = None
    priority: Priority | None = None
    assignee: str | None = Field(default=None, max_length=120)
    tags: list[str] | None = None

class MessageCreate(BaseModel):
    author: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=1, max_length=5000)
    internal: bool = False

class AssistantRequest(BaseModel):
    message: str = Field(min_length=2, max_length=5000)
    customer_name: str | None = None
    ticket_id: str | None = None

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def classify(text: str) -> tuple[Priority, list[str]]:
    t = text.lower()
    urgent_words = ["down", "outage", "cannot login", "security", "hacked", "payment failed", "production"]
    high_words = ["broken", "error", "not working", "failed", "refund", "invoice"]
    tags = []
    for label, words in {
        "billing": ["payment", "invoice", "refund", "charge"],
        "technical": ["error", "bug", "broken", "login", "api", "website"],
        "sales": ["price", "quote", "plan", "purchase"],
        "account": ["account", "password", "login", "profile"],
    }.items():
        if any(w in t for w in words):
            tags.append(label)
    if any(w in t for w in urgent_words):
        return "urgent", tags
    if any(w in t for w in high_words):
        return "high", tags
    return "medium", tags

def assistant_answer(message: str) -> dict:
    text = message.lower()
    if any(x in text for x in ["hours", "open", "available"]):
        answer = f"Our support hours are {business_context['hours']}."
        intent = "business_hours"
    elif any(x in text for x in ["price", "cost", "quote", "pricing"]):
        answer = "I can help collect your requirements for a quote. Please share the service, desired features, and target launch date."
        intent = "sales_pricing"
    elif any(x in text for x in ["refund", "payment", "invoice", "charge"]):
        answer = "This looks like a billing request. I can route it to the billing team; please include the invoice or transaction reference if available."
        intent = "billing"
    elif any(x in text for x in ["login", "password", "account"]):
        answer = "This looks like an account-support request. Please describe the exact error and, if relevant, the page where it occurs. Do not send passwords or secrets."
        intent = "account_support"
    elif any(x in text for x in ["error", "bug", "broken", "not working", "down"]):
        answer = "I can help triage the technical issue. Please provide the error message, affected page or feature, and when the problem started."
        intent = "technical_support"
    else:
        answer = "Thanks for contacting support. I can help with sales, billing, account access, or technical issues. Tell me what you need and I’ll route it appropriately."
        intent = "general_support"
    priority, tags = classify(message)
    return {"reply": answer, "intent": intent, "suggested_priority": priority, "suggested_tags": tags, "requires_human": priority in ("urgent", "high")}

@app.get("/")
def root():
    return {"name": app.title, "version": app.version, "docs": "/docs", "health": "/health"}

@app.get("/health")
def health():
    return {"status": "ok", "tickets": len(tickets), "timestamp": now()}

@app.get("/business/context")
def get_context():
    return business_context

@app.post("/assistant")
def assistant(payload: AssistantRequest):
    result = assistant_answer(payload.message)
    if payload.ticket_id and payload.ticket_id in tickets:
        result["ticket_id"] = payload.ticket_id
    return result

@app.post("/tickets", status_code=201)
def create_ticket(payload: TicketCreate):
    priority = payload.priority
    auto_priority, auto_tags = classify(f"{payload.subject} {payload.description}")
    if priority == "medium" and auto_priority in ("urgent", "high"):
        priority = auto_priority
    ticket_id = f"TCK-{uuid4().hex[:10].upper()}"
    ticket = {
        "id": ticket_id,
        **payload.model_dump(),
        "priority": priority,
        "tags": sorted(set(payload.tags + auto_tags)),
        "status": "open",
        "assignee": None,
        "created_at": now(),
        "updated_at": now(),
    }
    tickets[ticket_id] = ticket
    messages[ticket_id] = [{
        "id": uuid4().hex,
        "author": payload.customer_name,
        "body": payload.description,
        "internal": False,
        "created_at": now(),
    }]
    return ticket

@app.get("/tickets")
def list_tickets(
    status: Status | None = None,
    priority: Priority | None = None,
    q: str | None = Query(default=None, max_length=100),
):
    result = list(tickets.values())
    if status:
        result = [x for x in result if x["status"] == status]
    if priority:
        result = [x for x in result if x["priority"] == priority]
    if q:
        needle = q.lower()
        result = [x for x in result if needle in (x["subject"] + " " + x["description"] + " " + x["customer_name"]).lower()]
    return {"count": len(result), "items": result}

@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    ticket = tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    return {**ticket, "messages": messages.get(ticket_id, [])}

@app.patch("/tickets/{ticket_id}")
def update_ticket(ticket_id: str, payload: TicketUpdate):
    ticket = tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    changes = payload.model_dump(exclude_none=True)
    ticket.update(changes)
    ticket["updated_at"] = now()
    return ticket

@app.post("/tickets/{ticket_id}/messages", status_code=201)
def add_message(ticket_id: str, payload: MessageCreate):
    if ticket_id not in tickets:
        raise HTTPException(404, "Ticket not found")
    item = {"id": uuid4().hex, **payload.model_dump(), "created_at": now()}
    messages.setdefault(ticket_id, []).append(item)
    tickets[ticket_id]["updated_at"] = now()
    return item

@app.post("/tickets/{ticket_id}/ai-draft")
def draft_reply(ticket_id: str):
    ticket = tickets.get(ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    result = assistant_answer(ticket["subject"] + " " + ticket["description"])
    return {
        "ticket_id": ticket_id,
        "draft": result["reply"],
        "intent": result["intent"],
        "suggested_priority": result["suggested_priority"],
        "suggested_tags": result["suggested_tags"],
        "human_review_recommended": result["requires_human"],
    }

@app.get("/dashboard")
def dashboard():
    items = list(tickets.values())
    by_status = {s: sum(x["status"] == s for x in items) for s in ["open", "in_progress", "waiting_customer", "resolved", "closed"]}
    by_priority = {p: sum(x["priority"] == p for x in items) for p in ["low", "medium", "high", "urgent"]}
    return {
        "total_tickets": len(items),
        "open_tickets": sum(x["status"] in ("open", "in_progress", "waiting_customer") for x in items),
        "resolved_or_closed": sum(x["status"] in ("resolved", "closed") for x in items),
        "by_status": by_status,
        "by_priority": by_priority,
        "urgent_open": sum(x["priority"] == "urgent" and x["status"] not in ("resolved", "closed") for x in items),
    }
