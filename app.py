import asyncio
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
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


STATE: dict[str, object] = {
    "rules": ScheduleRule(),
    "items": [],
    "jobs": [],
    "threads": [],
    "autopilot": {"enabled": False, "interval_seconds": 300, "last_run_at": None, "last_brief": None},
}
AUTOPILOT_TASK: asyncio.Task | None = None


@app.get("/")
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.post("/api/chat")
def chat(payload: ChatRequest) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")

    client = OpenAI(api_key=api_key)
    try:
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=payload.message,
        )
        text = response.output_text
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Assistant error: {exc}") from exc

    return {"reply": text}


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
            "autopilot",
        ],
    }

# rest unchanged
@app.post('/api/items')
def create_item(item: ActionItem) -> ActionItem:
    items = STATE['items']; assert isinstance(items, list); items.append(item); return item

@app.get('/api/items')
def list_items() -> dict:
    items = STATE['items']; assert isinstance(items, list)
    return {'items': items, 'today_must_do': prioritize_items(items,'today'),'this_week_scheduled': prioritize_items(items,'week'),'backlog': prioritize_items(items,'backlog')}

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
    now = utc_now(); threads = STATE['threads']; assert isinstance(threads, list); suggestions=[]
    for thread in threads:
        gap = now-thread.last_outbound_at
        if thread.last_reply_at and thread.last_reply_at > thread.last_outbound_at: continue
        action = 'follow up today' if gap>=timedelta(days=7) else 'follow up this week' if gap>=timedelta(days=2) else 'watch'
        suggestions.append({'thread_id':thread.id,'counterpart':thread.counterpart,'action':action,'draft':f'Hi {thread.counterpart}, checking in on my last note—any updates?'})
    return {'suggestions':suggestions}

@app.get('/api/brief')
def morning_brief() -> dict:
    items=STATE['items']; threads=STATE['threads']; jobs=STATE['jobs']; assert isinstance(items,list) and isinstance(threads,list) and isinstance(jobs,list)
    return {'generated_at': utc_now().isoformat(), 'top_3_outcomes':[i.what for i in prioritize_items(items,'today')[:3]],'focus_blocks':suggest_focus_blocks(),'followups_due':[s for s in followups()['suggestions'] if s['action']!='watch'],'job_actions':[j for j in jobs if j.follow_up_due and j.follow_up_due<=utc_now()+timedelta(days=2)]}

def prioritize_items(items: list[ActionItem], bucket: Literal['today','week','backlog']) -> list[ActionItem]:
    now=utc_now()
    def score(item: ActionItem) -> float:
        urgency=5
        if item.due_at:
            hours=max((item.due_at-now).total_seconds()/3600,0); urgency=10 if hours<24 else 7 if hours<72 else 4
        return urgency + item.priority*2 + (2 if item.effort_minutes<=30 else 0) + (2 if item.follow_up_required else 0) + item.confidence
    ranked=sorted([i for i in items if i.status in {'open','scheduled','waiting'}], key=score, reverse=True)
    if bucket=='today': return [i for i in ranked if i.due_at and i.due_at<=now+timedelta(days=1)] or ranked[:3]
    if bucket=='week': return [i for i in ranked if i.due_at and i.due_at<=now+timedelta(days=7)]
    return [i for i in ranked if not i.due_at or i.due_at>now+timedelta(days=7)]

def suggest_focus_blocks() -> list[dict[str,str]]:
    rules=STATE['rules']; assert isinstance(rules, ScheduleRule); base=utc_now().replace(minute=0,second=0,microsecond=0); blocks=[]
    for i in range(3):
        start=base+timedelta(days=i, hours=rules.no_meetings_before_hour-base.hour)
        blocks.append({'start':start.isoformat(),'end':(start+timedelta(minutes=90)).isoformat(),'type':'deep_work'})
    return blocks
