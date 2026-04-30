import asyncio
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="My Personal Assistant")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChatRequest(BaseModel):
    message: str


class UploadedAsset(BaseModel):
    id: str
    filename: str
    content_type: str = "application/octet-stream"
    bytes: int
    uploaded_at: str



class UserProfile(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    target_roles: list[str] = []
    skills: list[str] = []
    experience_summary: str = ""
    retail_business_name: str = ""
    retail_business_summary: str = ""


class ResumeOptimizationRequest(BaseModel):
    job_title: str
    company: str = ""
    job_description: str


class CoverLetterRequest(BaseModel):
    job_title: str
    company: str
    job_description: str
    tone: Literal["professional", "warm", "confident"] = "professional"


class JobSearchRequest(BaseModel):
    job_description: str
    max_matches: int = Field(default=5, ge=1, le=10)


class RetailTask(BaseModel):
    id: str
    area: Literal["inventory", "marketing", "customer_service", "finance", "operations"]
    title: str
    detail: str = ""
    due_at: datetime | None = None
    status: Literal["open", "in_progress", "done"] = "open"
    created_at: datetime = Field(default_factory=utc_now)


class LearningFeedback(BaseModel):
    message: str = Field(min_length=1)
    score: Literal[1, 2, 3, 4, 5]


class ActionItem(BaseModel):
    id: str
    source: Literal["email", "text", "calendar", "job"]
    who: str = ""
    what: str
    due_at: datetime | None = None
    priority: int = Field(default=3, ge=1, le=5)
    effort_minutes: int = Field(default=30, ge=5)
    follow_up_required: bool = False
    status: Literal["open", "scheduled", "done", "waiting", "archived"] = "open"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=utc_now)


class ScheduleRule(BaseModel):
    no_meetings_before_hour: int = Field(default=10, ge=0, le=23)
    preferred_focus_days: list[Literal["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]] = ["Tue", "Thu"]


class JobApplication(BaseModel):
    id: str
    company: str
    role: str
    applied_date: datetime
    status: Literal["applied", "screen", "interview", "offer", "rejected"] = "applied"
    recruiter: str | None = None
    next_step: str | None = None
    follow_up_due: datetime | None = None


class MessageThread(BaseModel):
    id: str
    channel: Literal["email", "sms", "slack", "whatsapp"]
    counterpart: str
    last_outbound_at: datetime
    last_reply_at: datetime | None = None


class EmailConnectionRequest(BaseModel):
    provider: Literal["gmail", "microsoft"]
    account_email: str


class EmailConnection(BaseModel):
    id: str
    provider: Literal["gmail", "microsoft"]
    account_email: str
    connected_at: datetime
    status: Literal["connected", "disconnected"] = "connected"


class EmailMessage(BaseModel):
    id: str
    connection_id: str
    from_name: str
    from_email: str
    subject: str
    snippet: str
    received_at: datetime = Field(default_factory=utc_now)
    is_unread: bool = True
    needs_reply: bool = False
    labels: list[str] = []


class EmailIngestRequest(BaseModel):
    connection_id: str
    from_name: str = ""
    from_email: str
    subject: str
    snippet: str
    received_at: datetime | None = None
    is_unread: bool = True
    needs_reply: bool = False
    labels: list[str] = []


STATE: dict[str, object] = {
    "rules": ScheduleRule(),
    "items": [],
    "jobs": [],
    "threads": [],
    "email_connections": [],
    "emails": [],
    "autopilot": {"enabled": False, "interval_seconds": 300, "last_run_at": None, "last_brief": None},
    "profile": UserProfile(),
    "resume": {"filename": None, "content": "", "uploaded_at": None},
    "retail_tasks": [],
    "learning": {
        "feedback_events": 0,
        "avg_feedback_score": 0.0,
        "high_signal_topics": {},
        "low_signal_topics": {},
        "interaction_topics": {},
        "response_style_votes": {"concise": 0, "balanced": 0, "detailed": 0},
        "confidence_bias": 0.0,
    },
    "uploaded_assets": [],
}
AUTOPILOT_TASK: asyncio.Task | None = None


@app.get("/")
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/download/windows")
def download_windows_installer() -> FileResponse:
    installer_path = Path(__file__).parent / "Output" / "PersonalAssistantInstaller.exe"
    if not installer_path.exists():
        raise HTTPException(status_code=404, detail="Windows installer is not available yet.")
    return FileResponse(installer_path, filename="PersonalAssistantInstaller.exe", media_type="application/octet-stream")


def build_smart_context_summary() -> str:
    items = STATE["items"]
    jobs = STATE["jobs"]
    threads = STATE["threads"]
    email_connections = STATE["email_connections"]
    learning = STATE["learning"]
    profile = STATE["profile"]
    resume = STATE["resume"]
    retail_tasks = STATE["retail_tasks"]
    emails = STATE["emails"]
    assert isinstance(items, list) and isinstance(jobs, list) and isinstance(threads, list) and isinstance(email_connections, list) and isinstance(emails, list)
    assert isinstance(learning, dict) and isinstance(profile, UserProfile) and isinstance(resume, dict) and isinstance(retail_tasks, list)

    connected_providers = sorted({c.provider for c in email_connections if c.status == "connected"})
    if connected_providers:
        provider_text = ", ".join(connected_providers)
        inbox_note = f"Connected inboxes: {provider_text}. Prioritize inbox follow-ups and summarize likely urgent messages first."
    else:
        inbox_note = "No email account connected. Suggest connecting Gmail or Microsoft for inbox-aware planning."

    high_signal_topics = learning.get("high_signal_topics", {})
    low_signal_topics = learning.get("low_signal_topics", {})
    interaction_topics = learning.get("interaction_topics", {})
    response_style_votes = learning.get("response_style_votes", {})
    confidence_bias = float(learning.get("confidence_bias", 0.0))
    assert (
        isinstance(high_signal_topics, dict)
        and isinstance(low_signal_topics, dict)
        and isinstance(interaction_topics, dict)
        and isinstance(response_style_votes, dict)
    )
    preferred_topics = ", ".join(sorted(high_signal_topics, key=high_signal_topics.get, reverse=True)[:5]) or "none yet"
    avoid_topics = ", ".join(sorted(low_signal_topics, key=low_signal_topics.get, reverse=True)[:5]) or "none yet"
    active_topics = ", ".join(sorted(interaction_topics, key=interaction_topics.get, reverse=True)[:5]) or "none yet"
    preferred_style = max(response_style_votes, key=response_style_votes.get) if response_style_votes else "balanced"
    confidence_mode = "proactive" if confidence_bias >= 0 else "cautious"

    user_identity = profile.full_name or "the user"
    target_roles = ", ".join(profile.target_roles[:5]) or "not specified"
    retail_name = profile.retail_business_name or "retail business"
    resume_ready = "available" if resume.get("content") else "not uploaded"

    unread_count = len([m for m in emails if m.is_unread])
    reply_count = len([m for m in emails if m.needs_reply])

    return (
        f"You are a proactive personal assistant. {inbox_note} "
        f"Current inbox status -> unread emails: {unread_count}, emails needing a reply: {reply_count}. "
        f"Current counts -> open action items: {len(items)}, active job applications: {len(jobs)}, tracked threads: {len(threads)}. "
        f"Preferred user topics based on feedback: {preferred_topics}. Topics to avoid over-indexing: {avoid_topics}. "
        f"Active conversation topics: {active_topics}. Preferred response style: {preferred_style}. Confidence mode: {confidence_mode}. "
        "When asked for planning, prioritize near-term deadlines, then follow-up risk, then effort optimization. "
        "Mirror the preferred style, reason in steps, and explicitly call out assumptions when uncertain. "
        f"Support career workflows: learn user background, optimize resume for specific job posts, write tailored cover letters, and suggest best-fit jobs. "
        f"Support business workflows for {retail_name}: inventory, marketing, operations, customer service, and finance triage. "
        f"User: {user_identity}; target roles: {target_roles}; resume status: {resume_ready}; retail task count: {len(retail_tasks)}."
    )


def extract_topics(message: str) -> list[str]:
    words = [word.strip(".,!?;:()[]{}\"'").lower() for word in message.split()]
    filtered = [w for w in words if len(w) >= 4 and w.isalpha()]
    return list(dict.fromkeys(filtered[:8]))


def infer_response_style(message: str) -> str:
    lower = message.lower()
    if any(token in lower for token in ["quick", "brief", "short", "tldr", "concise"]):
        return "concise"
    if any(token in lower for token in ["deep", "detail", "thorough", "explain", "step-by-step"]):
        return "detailed"
    return "balanced"


def update_interaction_learning(message: str) -> None:
    learning = STATE["learning"]
    assert isinstance(learning, dict)
    interaction_topics = learning.setdefault("interaction_topics", {})
    style_votes = learning.setdefault("response_style_votes", {"concise": 0, "balanced": 0, "detailed": 0})
    assert isinstance(interaction_topics, dict) and isinstance(style_votes, dict)

    for topic, weight in list(interaction_topics.items()):
        interaction_topics[topic] = round(max(float(weight) * 0.92, 0.1), 3)

    for topic in extract_topics(message):
        interaction_topics[topic] = round(float(interaction_topics.get(topic, 0.0)) + 1.0, 3)

    style = infer_response_style(message)
    style_votes[style] = int(style_votes.get(style, 0)) + 1


@app.post("/api/learning/feedback")
def record_learning_feedback(payload: LearningFeedback) -> dict:
    learning = STATE["learning"]
    assert isinstance(learning, dict)
    total_events = int(learning.get("feedback_events", 0))
    avg_score = float(learning.get("avg_feedback_score", 0.0))
    total_score = avg_score * total_events + payload.score
    total_events += 1
    learning["feedback_events"] = total_events
    learning["avg_feedback_score"] = round(total_score / total_events, 3)

    high_signal_topics = learning.setdefault("high_signal_topics", {})
    low_signal_topics = learning.setdefault("low_signal_topics", {})
    assert isinstance(high_signal_topics, dict) and isinstance(low_signal_topics, dict)

    for topic in extract_topics(payload.message):
        if payload.score >= 4:
            high_signal_topics[topic] = int(high_signal_topics.get(topic, 0)) + 1
        elif payload.score <= 2:
            low_signal_topics[topic] = int(low_signal_topics.get(topic, 0)) + 1
    confidence_bias = float(learning.get("confidence_bias", 0.0))
    confidence_bias += 0.1 if payload.score >= 4 else -0.12 if payload.score <= 2 else 0.0
    learning["confidence_bias"] = round(max(min(confidence_bias, 2.0), -2.0), 3)

    return {"ok": True, "learning": learning}


@app.get("/api/learning/profile")
def learning_profile() -> dict:
    learning = STATE["learning"]
    assert isinstance(learning, dict)
    return learning


@app.get("/api/profile")
def get_profile() -> UserProfile:
    profile = STATE["profile"]
    assert isinstance(profile, UserProfile)
    return profile


@app.post("/api/profile")
def upsert_profile(payload: UserProfile) -> UserProfile:
    STATE["profile"] = payload
    return payload


@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)) -> dict:
    raw = await file.read()
    text = raw.decode("utf-8", errors="ignore")
    STATE["resume"] = {"filename": file.filename, "content": text[:120000], "uploaded_at": utc_now().isoformat()}
    return {"ok": True, "filename": file.filename, "characters": len(text)}


@app.get("/api/resume")
def get_resume() -> dict:
    resume = STATE["resume"]
    assert isinstance(resume, dict)
    return resume


def require_client() -> OpenAI:
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY") or "local"

    if not os.getenv("OPENAI_API_KEY") and not base_url:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not configured. Set OPENAI_API_KEY for hosted providers, or OPENAI_BASE_URL for local OpenAI-compatible endpoints (for example Ollama).",
        )

    client_kwargs: dict[str, str] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    return OpenAI(**client_kwargs)


@app.post("/api/resume/optimize")
def optimize_resume(payload: ResumeOptimizationRequest) -> dict:
    resume = STATE["resume"]
    profile = STATE["profile"]
    assert isinstance(resume, dict) and isinstance(profile, UserProfile)
    resume_text = str(resume.get("content") or profile.experience_summary)
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Upload a resume or set profile experience_summary first.")

    client = require_client()
    prompt = (
        "Rewrite and optimize this resume for the target role. Return JSON with keys summary, bullet_updates, keyword_gaps.\n"
        f"Role: {payload.job_title}\nCompany: {payload.company}\nJob description:\n{payload.job_description}\n\n"
        f"Current resume:\n{resume_text}"
    )
    response = client.responses.create(model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), input=prompt)
    return {"optimized": response.output_text}


@app.post("/api/cover-letter")
def generate_cover_letter(payload: CoverLetterRequest) -> dict:
    resume = STATE["resume"]
    profile = STATE["profile"]
    assert isinstance(resume, dict) and isinstance(profile, UserProfile)
    client = require_client()
    source = str(resume.get("content") or profile.experience_summary)
    prompt = (
        f"Write a one-page {payload.tone} cover letter for {payload.company} / {payload.job_title}. "
        "Use concrete achievements and keep it concise.\n"
        f"Job description:\n{payload.job_description}\n\nCandidate background:\n{source}"
    )
    response = client.responses.create(model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), input=prompt)
    return {"cover_letter": response.output_text}


@app.post("/api/jobs/match")
def match_jobs(payload: JobSearchRequest) -> dict:
    profile = STATE["profile"]
    resume = STATE["resume"]
    assert isinstance(profile, UserProfile) and isinstance(resume, dict)
    baseline = resume.get("content") or profile.experience_summary
    if not baseline:
        raise HTTPException(status_code=400, detail="Need resume or profile experience to compute match.")

    keywords = {w.lower() for w in extract_topics(str(baseline))}
    jd_tokens = extract_topics(payload.job_description)
    overlap = [t for t in jd_tokens if t.lower() in keywords]
    score = round(min(100, (len(overlap) / max(len(jd_tokens), 1)) * 100), 1)
    suggestions = [
        f"Prioritize roles mentioning: {', '.join(overlap[:8]) or 'core strengths from your resume'}",
        "Filter for roles aligned to your target role list and seniority.",
        "Use cover letter + optimized bullet points before applying.",
    ]
    return {"match_score": score, "matched_keywords": overlap[: payload.max_matches], "suggestions": suggestions}


@app.post("/api/retail/tasks")
def create_retail_task(payload: RetailTask) -> RetailTask:
    tasks = STATE["retail_tasks"]
    assert isinstance(tasks, list)
    tasks.append(payload)
    return payload


@app.get("/api/retail/tasks")
def list_retail_tasks() -> list[RetailTask]:
    tasks = STATE["retail_tasks"]
    assert isinstance(tasks, list)
    return tasks


@app.post("/api/chat")
def chat(payload: ChatRequest) -> dict:
    update_interaction_learning(payload.message)
    client = require_client()
    try:
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=[
                {"role": "system", "content": build_smart_context_summary()},
                {"role": "user", "content": payload.message},
            ],
        )
        text = response.output_text
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Assistant error: {exc}") from exc

    return {"reply": text}


@app.post("/api/chat/files")
async def chat_with_files(message: str = Form(...), files: list[UploadFile] = File(...)) -> dict:
    update_interaction_learning(message)
    client = require_client()
    uploaded_assets = STATE["uploaded_assets"]
    assert isinstance(uploaded_assets, list)

    if not files:
        raise HTTPException(status_code=400, detail="Please attach at least one file.")

    user_content: list[dict] = [{"type": "input_text", "text": message}]
    ingested_files: list[UploadedAsset] = []

    for upload in files:
        data = await upload.read()
        if not data:
            continue
        try:
            uploaded = client.files.create(file=(upload.filename or "upload.bin", data), purpose="user_data")
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Could not process file {upload.filename}: {exc}") from exc

        user_content.append({"type": "input_file", "file_id": uploaded.id})
        asset = UploadedAsset(
            id=uploaded.id,
            filename=upload.filename or "upload.bin",
            content_type=upload.content_type or "application/octet-stream",
            bytes=len(data),
            uploaded_at=utc_now().isoformat(),
        )
        ingested_files.append(asset)
        uploaded_assets.append(asset)

    if len(ingested_files) == 0:
        raise HTTPException(status_code=400, detail="No readable file data found in attachments.")

    try:
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=[
                {"role": "system", "content": build_smart_context_summary()},
                {"role": "user", "content": user_content},
            ],
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Assistant error: {exc}") from exc

    return {
        "reply": response.output_text,
        "files": [asset.model_dump() for asset in ingested_files],
    }


@app.post("/api/email/connect")
def connect_email(payload: EmailConnectionRequest) -> EmailConnection:
    email_connections = STATE["email_connections"]
    assert isinstance(email_connections, list)

    existing = next(
        (
            conn
            for conn in email_connections
            if conn.account_email.lower() == payload.account_email.lower() and conn.provider == payload.provider
        ),
        None,
    )
    if existing:
        existing.status = "connected"
        return existing

    connection = EmailConnection(
        id=f"conn_{uuid4().hex[:10]}",
        provider=payload.provider,
        account_email=payload.account_email,
        connected_at=utc_now(),
    )
    email_connections.append(connection)
    return connection


@app.post("/api/email/disconnect/{connection_id}")
def disconnect_email(connection_id: str) -> dict:
    email_connections = STATE["email_connections"]
    assert isinstance(email_connections, list)

    for connection in email_connections:
        if connection.id == connection_id:
            connection.status = "disconnected"
            return {"ok": True, "connection": connection}
    raise HTTPException(status_code=404, detail="Connection not found.")


@app.get("/api/email/connections")
def list_email_connections() -> dict:
    email_connections = STATE["email_connections"]
    assert isinstance(email_connections, list)
    return {"connections": email_connections}


@app.post("/api/email/messages")
def ingest_email_message(payload: EmailIngestRequest) -> EmailMessage:
    email_connections = STATE["email_connections"]
    emails = STATE["emails"]
    assert isinstance(email_connections, list) and isinstance(emails, list)
    connection = next((conn for conn in email_connections if conn.id == payload.connection_id and conn.status == "connected"), None)
    if not connection:
        raise HTTPException(status_code=404, detail="Connected email account not found for this connection_id.")

    message = EmailMessage(
        id=f"mail_{uuid4().hex[:12]}",
        connection_id=payload.connection_id,
        from_name=payload.from_name,
        from_email=payload.from_email,
        subject=payload.subject,
        snippet=payload.snippet,
        received_at=payload.received_at or utc_now(),
        is_unread=payload.is_unread,
        needs_reply=payload.needs_reply,
        labels=payload.labels,
    )
    emails.append(message)
    return message


@app.get("/api/email/messages")
def list_email_messages(connection_id: str | None = None, unread_only: bool = False) -> dict:
    emails = STATE["emails"]
    assert isinstance(emails, list)
    filtered = emails
    if connection_id:
        filtered = [email for email in filtered if email.connection_id == connection_id]
    if unread_only:
        filtered = [email for email in filtered if email.is_unread]
    ordered = sorted(filtered, key=lambda m: m.received_at, reverse=True)
    return {"messages": ordered}


async def autopilot_loop() -> None:
    while True:
        autopilot = STATE["autopilot"]
        assert isinstance(autopilot, dict)
        if not autopilot["enabled"]:
            return
        autopilot["last_run_at"] = utc_now().isoformat()
        autopilot["last_brief"] = morning_brief()
        await asyncio.sleep(int(autopilot["interval_seconds"]))


@app.post("/api/autopilot/start")
def start_autopilot(interval_seconds: int = 300) -> dict:
    global AUTOPILOT_TASK
    if interval_seconds < 30:
        raise HTTPException(status_code=400, detail="interval_seconds must be at least 30.")

    autopilot = STATE["autopilot"]
    assert isinstance(autopilot, dict)
    autopilot["enabled"] = True
    autopilot["interval_seconds"] = interval_seconds

    if AUTOPILOT_TASK is None or AUTOPILOT_TASK.done():
        AUTOPILOT_TASK = asyncio.create_task(autopilot_loop())

    return {"ok": True, "autopilot": autopilot}


@app.post("/api/autopilot/stop")
def stop_autopilot() -> dict:
    autopilot = STATE["autopilot"]
    assert isinstance(autopilot, dict)
    autopilot["enabled"] = False
    return {"ok": True, "autopilot": autopilot}


@app.get("/api/autopilot/status")
def autopilot_status() -> dict:
    autopilot = STATE["autopilot"]
    assert isinstance(autopilot, dict)
    return autopilot


@app.get("/api/assistant/health")
def assistant_health() -> dict:
    return {
        "ok": True,
        "modules": [
            "inbox_triage",
            "task_manager",
            "calendar_scheduler",
            "follow_up_intelligence",
            "job_tracker",
            "personalization",
            "adaptive_learning",
            "autopilot",
            "email_connectors",
            "email_reading",
        ],
    }


@app.post('/api/items')
def create_item(item: ActionItem) -> ActionItem:
    items = STATE['items']; assert isinstance(items, list); items.append(item); return item


@app.get('/api/items')
def list_items() -> dict:
    items = STATE['items']; assert isinstance(items, list)
    return {'items': items, 'today_must_do': prioritize_items(items, 'today'), 'this_week_scheduled': prioritize_items(items, 'week'), 'backlog': prioritize_items(items, 'backlog')}


@app.post('/api/jobs')
def create_job(job: JobApplication) -> JobApplication:
    jobs = STATE['jobs']; assert isinstance(jobs, list); jobs.append(job); return job


@app.get('/api/jobs')
def list_jobs() -> list[JobApplication]:
    jobs = STATE['jobs']; assert isinstance(jobs, list); return jobs


@app.post('/api/threads')
def create_thread(thread: MessageThread) -> MessageThread:
    threads = STATE['threads']; assert isinstance(threads, list); threads.append(thread); return thread


@app.get('/api/followups')
def followups() -> dict:
    now = utc_now(); threads = STATE['threads']; assert isinstance(threads, list); suggestions = []
    for thread in threads:
        gap = now - thread.last_outbound_at
        if thread.last_reply_at and thread.last_reply_at > thread.last_outbound_at: continue
        action = 'follow up today' if gap >= timedelta(days=7) else 'follow up this week' if gap >= timedelta(days=2) else 'watch'
        suggestions.append({'thread_id': thread.id, 'counterpart': thread.counterpart, 'action': action, 'draft': f'Hi {thread.counterpart}, checking in on my last note—any updates?'})
    return {'suggestions': suggestions}


@app.get('/api/brief')
def morning_brief() -> dict:
    items = STATE['items']; threads = STATE['threads']; jobs = STATE['jobs']; email_connections = STATE['email_connections']; emails = STATE['emails']
    assert isinstance(items, list) and isinstance(threads, list) and isinstance(jobs, list) and isinstance(email_connections, list) and isinstance(emails, list)
    connected_accounts = [c.account_email for c in email_connections if c.status == 'connected']
    unread_count = len([m for m in emails if m.is_unread])
    needs_reply_count = len([m for m in emails if m.needs_reply])
    return {'generated_at': utc_now().isoformat(), 'top_3_outcomes': [i.what for i in prioritize_items(items, 'today')[:3]], 'focus_blocks': suggest_focus_blocks(), 'followups_due': [s for s in followups()['suggestions'] if s['action'] != 'watch'], 'job_actions': [j for j in jobs if j.follow_up_due and j.follow_up_due <= utc_now() + timedelta(days=2)], 'connected_email_accounts': connected_accounts, 'inbox_summary': {'unread': unread_count, 'needs_reply': needs_reply_count}}


def prioritize_items(items: list[ActionItem], bucket: Literal['today', 'week', 'backlog']) -> list[ActionItem]:
    now = utc_now()

    def score(item: ActionItem) -> float:
        urgency = 5
        if item.due_at:
            hours = max((item.due_at - now).total_seconds() / 3600, 0); urgency = 10 if hours < 24 else 7 if hours < 72 else 4
        return urgency + item.priority * 2 + (2 if item.effort_minutes <= 30 else 0) + (2 if item.follow_up_required else 0) + item.confidence

    ranked = sorted([i for i in items if i.status in {'open', 'scheduled', 'waiting'}], key=score, reverse=True)
    if bucket == 'today': return [i for i in ranked if i.due_at and i.due_at <= now + timedelta(days=1)] or ranked[:3]
    if bucket == 'week': return [i for i in ranked if i.due_at and i.due_at <= now + timedelta(days=7)]
    return [i for i in ranked if not i.due_at or i.due_at > now + timedelta(days=7)]


def suggest_focus_blocks() -> list[dict[str, str]]:
    rules = STATE['rules']; assert isinstance(rules, ScheduleRule); base = utc_now().replace(minute=0, second=0, microsecond=0); blocks = []
    for i in range(3):
        start = base + timedelta(days=i, hours=rules.no_meetings_before_hour - base.hour)
        blocks.append({'start': start.isoformat(), 'end': (start + timedelta(minutes=90)).isoformat(), 'type': 'deep_work'})
    return blocks
