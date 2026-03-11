# CareAgent OS — Autonomous Multi-Agent Healthcare Operations Platform

> **6 specialized AI agents working as a swarm to automate the $150B healthcare admin nightmare.**
> Built for the AI Agents Hackathon 2026 (Kiro x AI_Agents Community)

## The Problem

**30% of all US healthcare spending ($1.1 trillion) goes to administrative overhead.** Doctors spend 2 hours on paperwork for every 1 hour with patients. The result:

- **Prior authorizations** waste 35+ hours/week per practice and delay patient care
- **Manual triage** is slow, subjective, and misses deterioration patterns
- **Clinical documentation** takes 2+ hours daily away from patient care
- **Patient follow-ups** fall through the cracks — 50% of patients don't complete prescribed treatments
- **Insurance phone calls** average 45 minutes of hold time per authorization

## The Solution

**CareAgent OS** deploys a swarm of 6 autonomous AI agents that collaborate through shared memory to handle end-to-end healthcare operations — from the moment a patient calls to post-visit follow-ups and revenue analytics.

### The Agent Swarm

| # | Agent | What It Does Autonomously | Key Tech |
|---|-------|--------------------------|----------|
| 1 | **Voice Intake Agent** | Answers patient calls, collects symptoms via natural conversation, books appointments | Whisper STT + GPT-4o |
| 2 | **Triage Agent** | AI triage using Manchester Triage System + ESI, urgency classification, department routing | Rule engine + LLM hybrid |
| 3 | **Prior Auth Agent** | Detects auth requirements, generates clinical justification, calls insurance companies autonomously | Multi-payer rules + LLM |
| 4 | **Clinical Doc Agent** | Generates SOAP notes, ICD-10/CPT codes, discharge instructions, referral letters | GPT-4o structured output |
| 5 | **Patient Advocate Agent** | Post-visit follow-ups, medication reminders, health education via SMS/voice | Empathetic AI + scheduling |
| 6 | **Operations Agent** | Patient volume prediction, scheduling optimization, revenue forecasting, capacity management | Analytics engine + LLM |

### The Orchestrator (Secret Sauce)

A meta-agent coordinates all 6 agents using:
- **Shared memory blackboard** — agents read each other's context seamlessly
- **Automated handoffs** — triage results flow to documentation, prescriptions trigger prior auth
- **Human-in-the-loop escalation** — critical cases escalated with full reasoning chain
- **Multi-LLM routing** — GPT-4o for reasoning, GPT-4o-mini for fast tasks, open-source for PHI-sensitive work

## Architecture

```
Patient Call/Visit
       │
       ▼
┌──────────────────────────────────────────────────────┐
│                  ORCHESTRATOR                         │
│         (Routes, coordinates, escalates)              │
│                                                       │
│  ┌─────────┐  ┌─────────┐  ┌──────────────┐         │
│  │  Voice   │→│ Triage  │→│ Clinical Doc │         │
│  │ Intake   │  │  Agent  │  │    Agent     │         │
│  └─────────┘  └────┬────┘  └──────┬───────┘         │
│                     │              │                   │
│              ┌──────▼──────┐  ┌───▼────────┐         │
│              │ Prior Auth  │  │  Patient   │         │
│              │   Agent     │  │  Advocate  │         │
│              └─────────────┘  └────────────┘         │
│                                                       │
│              ┌─────────────────────────┐              │
│              │   Operations Agent      │              │
│              │ (Analytics & Forecasting)│              │
│              └─────────────────────────┘              │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │          SHARED MEMORY (Blackboard)              │ │
│  │  Patient context flows between all agents        │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │         MULTI-LLM ROUTER                         │ │
│  │  GPT-4o │ GPT-4o-mini │ Claude │ Open Source    │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
       │
       ▼
  Real-time Dashboard (Next.js)
```

## Demo

The live demo processes 3 patients through the full agent pipeline:

1. **Maria Santos** (62F) — Chest pain + SOB → CRITICAL triage → Emergency routing
2. **James Wilson** (8M) — High fever + sore throat → URGENT triage → Pediatrics
3. **Aisha Patel** (34F) — Back pain + leg numbness → URGENT + Prior auth for MRI

Each patient flows through: Voice Intake → Triage → Clinical Documentation → Prior Auth (if needed) → Patient Follow-up — all autonomously.

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend** | FastAPI + Python 3.12 | High-performance async API |
| **Frontend** | Next.js 14 + React + TailwindCSS | Modern dashboard with real-time updates |
| **AI/LLM** | OpenAI GPT-4o + GPT-4o-mini | Multi-LLM routing for optimal cost/quality |
| **Agent Framework** | Custom orchestrator + shared memory | Purpose-built for healthcare workflows |
| **Database** | SQLAlchemy + SQLite (async) | Production-ready with async support |
| **Real-time** | WebSockets | Live agent activity feed |
| **Deployment** | Docker + Docker Compose | One-command deployment |

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env

python main.py
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Dashboard: http://localhost:3000
```

### Docker

```bash
docker-compose up -d
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|---------|-------------|
| `POST` | `/api/demo` | Run full demo with 3 patients |
| `POST` | `/api/journey` | Run single patient through all agents |
| `GET` | `/api/status` | System status + all agent stats |
| `GET` | `/api/agents` | List all agents |
| `GET` | `/api/activity-feed` | Real-time agent activity |
| `POST` | `/api/intake/start` | Start voice intake conversation |
| `POST` | `/api/triage` | Full AI triage assessment |
| `POST` | `/api/prior-auth` | Submit prior authorization |
| `POST` | `/api/prior-auth/call-insurance` | Autonomous insurance call |
| `POST` | `/api/documentation/soap` | Generate SOAP notes |
| `POST` | `/api/patient/followup` | Generate patient follow-up |
| `GET` | `/api/operations/dashboard` | Operations analytics |
| `GET` | `/api/operations/predictions` | Patient volume forecast |
| `GET` | `/api/operations/revenue` | Revenue forecast |
| `GET` | `/api/operations/capacity` | Department capacity |
| `WS` | `/api/ws/activity` | WebSocket activity stream |

## Business Model

| Tier | Price | Features |
|------|-------|----------|
| **Starter** (Small clinics) | $299/mo | Voice Intake + Triage + Documentation |
| **Professional** (Mid-size) | $999/mo | All 6 agents + Analytics |
| **Enterprise** (Hospitals) | Custom | Custom agents + EHR integration + SLA |

- **TAM**: $150B US healthcare admin market
- **Revenue target**: 100 clinics × $999/mo = **$1.2M ARR** Year 1
- **Unit economics**: ~$50/mo compute cost per clinic → 95% gross margin

## Why CareAgent OS Wins

1. **Platform, not a feature** — judges from Microsoft/Google/Salesforce think in platforms
2. **Multi-agent orchestration** — the winning pattern from Microsoft AI Hackathon 2025
3. **Autonomous phone calls** — the #1 wow factor from OOP Healthcare Hackathon
4. **$150B problem** — 30% of healthcare spending is admin waste
5. **Multi-LLM routing** — demonstrates AI infrastructure sophistication
6. **Rules + AI hybrid** — safety-first triage (rules override AI for critical cases)
7. **Full-stack demo** — beautiful dashboard + working backend + real agent coordination

## Built By

**Karthik Ramadugu** — Software Engineer | Hackathon Winner (1st Place, Akash Open Agents 2026)

Built for the **AI Agents Hackathon 2026** (Kiro x AI_Agents Community, Mar 14-21, 2026)
