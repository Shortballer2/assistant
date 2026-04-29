# Personalized Assistant Blueprint

## 1) What you want this assistant to do

Your assistant should:
- Organize email and surface what matters.
- Build and maintain to-do lists.
- Plan schedules and spread work across time blocks.
- Check texts/messages and suggest follow-ups.
- Track job applications and next actions.
- Connect to your accounts and learn your preferences over time.

## 2) Recommended architecture (high-level)

### Core modules
1. **Inbox Triage**
   - Connect Gmail/Outlook.
   - Auto-label by project, urgency, and sender.
   - Detect action items and due dates.
   - Produce daily summary: urgent, waiting, low-priority.

2. **Task & Project Manager**
   - Central task model with fields:
     - title, context (work/personal/job search), due date, priority, estimated effort, dependency, status.
   - Sync with your preferred tool (Notion, Todoist, Asana, ClickUp, Linear, etc.).

3. **Calendar & Scheduling Agent**
   - Integrate Google/Outlook Calendar.
   - Auto-timeblock deep work and admin work.
   - Enforce rules (e.g., no meetings before 10 AM, focus blocks on Tue/Thu).
   - Rebalance when conflicts appear.

4. **Follow-up Intelligence**
   - Scan recent outbound messages and detect unanswered threads.
   - Suggest “follow up today / this week / archive.”
   - Draft concise follow-up messages.

5. **Job Application Tracker**
   - Parse job confirmations from email.
   - Store company, role, applied date, status, recruiter, and next steps.
   - Trigger reminders for follow-ups.

6. **Learning & Personalization Layer**
   - Observe your edits to priorities/schedules.
   - Learn preferred work cadence and task duration bias.
   - Build user profile: best focus times, response style, risk tolerance for overbooking.

7. **Unified Assistant Interface**
   - Chat UI + mobile notifications.
   - “Morning brief” and “end-of-day wrap-up.”
   - One-click actions (schedule, snooze, reply draft, create task).

## 3) Account connections you likely need

- Email: Gmail or Outlook (OAuth).
- Calendar: Google Calendar or Outlook Calendar.
- Messaging: SMS/iMessage (via phone bridge), Slack, WhatsApp (if needed).
- Task systems: Notion/Todoist/Asana/etc.
- Job platforms: LinkedIn, Greenhouse/Lever email parsing.
- Cloud storage: Google Drive/OneDrive for attachments.

## 4) Data model essentials

Use a shared schema for all “actionable items”:
- `source` (email/text/calendar/job)
- `who`
- `what`
- `due_at`
- `priority`
- `effort_minutes`
- `follow_up_required`
- `status`
- `confidence`

This gives the planner one normalized queue to prioritize from.

## 5) Prioritization rules (simple but effective)

Score tasks with:
- Urgency (time to due date)
- Importance (strategic value)
- Effort (short tasks for momentum + long tasks for deep work)
- Relationship sensitivity (people you should not ignore)
- Staleness (how long waiting)

Then assign:
- **Today must-do**
- **This week scheduled**
- **Backlog**

## 6) Daily operating cadence

1. **Morning (5–10 min):**
   - Summarize overnight inbox/messages.
   - Propose top 3 outcomes for the day.
   - Draft schedule blocks.

2. **Midday check-in (2–5 min):**
   - Re-plan based on actual progress.

3. **End-of-day (5 min):**
   - Close loops and prepare tomorrow.
   - Suggest follow-ups and carryovers.

## 7) Security and privacy requirements (non-negotiable)

- OAuth with least-privilege scopes.
- Encryption at rest and in transit.
- Secret manager for API tokens.
- Audit log for assistant actions.
- Human approval for sending messages or booking meetings (until trusted).
- Fine-grained memory controls (what to remember/forget).

## 8) MVP rollout plan (4 phases)

### Phase 1 (Week 1–2): Foundation
- Connect email + calendar.
- Build daily summary and action extraction.
- Manual approval flow for actions.

### Phase 2 (Week 3–4): Planning
- Task normalization and prioritization engine.
- Time-blocking suggestions.
- Follow-up detector.

### Phase 3 (Week 5–6): Job search workflows
- Application tracker from emails.
- Automated reminder cadence.

### Phase 4 (Week 7+): Personalization
- Preference learning.
- Better effort estimates and schedule tuning.

## 9) Recommended stack (practical)

- Backend: Python (FastAPI) or TypeScript (NestJS).
- Worker queue: Celery/RQ or BullMQ.
- Database: Postgres + pgvector (for semantic memory).
- Integrations: official APIs + OAuth.
- LLM orchestration: tool-calling agent with strict policies.
- Frontend: web dashboard + mobile notifications.

## 10) Success metrics

- Inbox to zero rate (or average unread age).
- % of planned tasks completed daily.
- Follow-up miss rate.
- Calendar adherence vs. plan.
- Job application response/follow-up cycle time.

## 11) First actions I recommend for you now

1. Pick your primary stack (Google vs Microsoft ecosystem).
2. Pick your task manager (or use built-in assistant tasks).
3. Define your scheduling rules (work hours, deep work windows).
4. Start with human-in-the-loop mode for 2 weeks.
5. Review weekly what the assistant got wrong and adjust rules.

---

If you want, the next step is to convert this into:
- a concrete technical spec,
- API integration checklist,
- and a build-ready implementation plan with milestones and tickets.
