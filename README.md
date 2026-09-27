# 🤖 AI Business Assistant & Customer Support Ticket System

A practical **Python + FastAPI** backend that combines an AI-style business assistant with a customer support ticketing workflow.

## What this demonstrates

- Python backend engineering
- FastAPI REST API design
- Customer support ticket lifecycle
- Automatic ticket priority classification
- Intent detection for common support requests
- Suggested tags and routing signals
- AI-assisted reply drafting
- Ticket conversations and internal messages
- Support dashboard metrics
- Search and filtering
- Customer/business context
- Pydantic validation and email validation
- OpenAPI/Swagger documentation
- CORS
- Automated tests
- Vercel serverless configuration

## Core workflow

1. A customer submits a support request.
2. The API classifies likely intent and priority.
3. A ticket is created with suggested tags.
4. Support staff can assign, update, search, and reply to the ticket.
5. The assistant can draft a response for human review.
6. Dashboard endpoints provide operational support metrics.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | / | API information |
| GET | /health | Health check |
| GET | /business/context | Business context |
| POST | /assistant | AI-style assistant response |
| POST | /tickets | Create a support ticket |
| GET | /tickets | Search/filter tickets |
| GET | /tickets/{ticket_id} | Ticket + conversation |
| PATCH | /tickets/{ticket_id} | Update status/priority/assignee |
| POST | /tickets/{ticket_id}/messages | Add conversation message |
| POST | /tickets/{ticket_id}/ai-draft | Draft a support reply |
| GET | /dashboard | Ticket metrics |
| GET | /docs | Swagger UI |

## Example assistant request

```json
{
  "message": "My checkout is broken and customers cannot pay."
}
```

Example response includes:
- detected intent
- suggested priority
- suggested tags
- assistant reply
- human-review signal

## Example ticket

```json
{
  "customer_name": "Jane Doe",
  "customer_email": "jane@example.com",
  "subject": "Website is broken",
  "description": "The checkout page is not working.",
  "priority": "high",
  "channel": "web"
}
```

## Production architecture

This repository intentionally uses in-memory storage so it runs without external infrastructure. A production version can add:

- PostgreSQL/Supabase persistence
- authenticated staff accounts and role-based access
- Redis/background jobs
- real LLM provider integration
- knowledge-base/RAG retrieval
- email and live-chat integrations
- SLA timers and escalation workflows
- file attachments
- audit logs
- customer portal
- analytics and CSAT
- webhook/event processing
- rate limiting and abuse protection

## AI safety and reliability

The demo's assistant is deterministic and does not pretend that a rule-based response is a verified LLM answer. High/urgent issues are marked for human review. Sensitive information such as passwords or secrets should never be requested.

## Developer

Built by **Taiwo Emmanuel — Web Designer & Full-Stack Developer**.

GitHub project: https://github.com/Ab2612Ab/Emmanx/tree/main/ai-business-assistant-support-tickets
