const statusEl = document.getElementById("status");
const intervalEl = document.getElementById("interval");
const providerEl = document.getElementById("provider");
const emailEl = document.getElementById("email");
const connectionsEl = document.getElementById("connections");
const inboxEl = document.getElementById("inbox");
const chatInputEl = document.getElementById("chat-input");
const chatFilesEl = document.getElementById("chat-files");
const chatOutputEl = document.getElementById("chat-output");
const chatStatusEl = document.getElementById("chat-status");
const briefOutcomesEl = document.getElementById("brief-outcomes");
const briefFollowupsEl = document.getElementById("brief-followups");
const briefFocusEl = document.getElementById("brief-focus");

function renderList(container, items, fallback = "Nothing yet") {
  container.innerHTML = "";
  if (!items || items.length === 0) {
    const li = document.createElement("li");
    li.textContent = fallback;
    container.appendChild(li);
    return;
  }

  for (const text of items) {
    const li = document.createElement("li");
    li.textContent = text;
    container.appendChild(li);
  }
}

async function sendChat() {
  const message = chatInputEl.value.trim();
  if (!message) return;

  chatStatusEl.textContent = "Thinking…";
  chatOutputEl.textContent = "";

  try {
    let response;
    const files = Array.from(chatFilesEl.files || []);
    if (files.length > 0) {
      const formData = new FormData();
      formData.append("message", message);
      files.forEach((file) => formData.append("files", file));
      response = await fetch("/api/chat/files", { method: "POST", body: formData });
    } else {
      response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
    }

    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Assistant error");

    chatOutputEl.textContent = payload.reply || "No reply returned.";
    if (files.length > 0) {
      chatFilesEl.value = "";
    }
    chatStatusEl.textContent = "";
  } catch (error) {
    chatOutputEl.textContent = `Sorry, I couldn't process that request. ${error.message}`;
    chatStatusEl.textContent = "";
  }
}

document.getElementById("send-chat").addEventListener("click", sendChat);
chatInputEl.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    sendChat();
  }
});

document.getElementById("start").addEventListener("click", async () => {
  const interval = Number(intervalEl.value || 300);
  await fetch(`/api/autopilot/start?interval_seconds=${interval}`, { method: "POST" });
  await refresh();
});

document.getElementById("stop").addEventListener("click", async () => {
  await fetch("/api/autopilot/stop", { method: "POST" });
  await refresh();
});

document.getElementById("connect-email").addEventListener("click", async () => {
  const accountEmail = emailEl.value.trim();
  if (!accountEmail) return;

  await fetch("/api/email/connect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider: providerEl.value, account_email: accountEmail }),
  });

  emailEl.value = "";
  await refresh();
});

document.getElementById("connect-gmail-oauth").addEventListener("click", async () => {
  const response = await fetch("/api/email/gmail/auth-url");
  const payload = await response.json();
  if (!response.ok) {
    alert(payload.detail || "Could not start Gmail OAuth.");
    return;
  }
  window.location.href = payload.auth_url;
});

async function refresh() {
  const [status, brief, connectionData, inboxData] = await Promise.all([
    (await fetch("/api/autopilot/status")).json(),
    (await fetch("/api/brief")).json(),
    (await fetch("/api/email/connections")).json(),
    (await fetch("/api/email/messages")).json(),
  ]);

  renderList(statusEl, [
    `State: ${status.enabled ? "running" : "stopped"}`,
    `Interval: every ${status.interval_seconds}s`,
    `Last run: ${status.last_run_at ? new Date(status.last_run_at).toLocaleString() : "not run yet"}`,
  ]);

  renderList(
    connectionsEl,
    (connectionData.connections || [])
      .filter((c) => c.status === "connected")
      .map((c) => `${c.provider}: ${c.account_email}`),
    "No accounts connected"
  );

  const gmailConnections = (connectionData.connections || []).filter((c) => c.provider === "gmail" && c.status === "connected");
  for (const connection of gmailConnections) {
    await fetch(`/api/email/gmail/sync/${connection.id}`, { method: "POST" });
  }
  const summary = brief.inbox_summary || { unread: 0, needs_reply: 0 };
  const latestMessages = (inboxData.messages || []).slice(0, 3).map((m) => {
    const sender = m.from_name || m.from_email;
    return `${sender}: ${m.subject}`;
  });
  renderList(
    inboxEl,
    [`Unread: ${summary.unread}`, `Needs reply: ${summary.needs_reply}`, ...latestMessages],
    "No inbox messages yet"
  );

  renderList(briefOutcomesEl, brief.top_3_outcomes || [], "No priorities yet");
  renderList(
    briefFollowupsEl,
    (brief.followups_due || []).map((f) => `${f.counterpart}: ${f.action}`),
    "No follow-ups due"
  );
  renderList(
    briefFocusEl,
    (brief.focus_blocks || []).map((b) => `${new Date(b.start).toLocaleString()} → ${new Date(b.end).toLocaleTimeString()}`),
    "No focus blocks"
  );
}

setInterval(refresh, 5000);
refresh();
