const statusEl = document.getElementById("status");
const briefEl = document.getElementById("brief");
const intervalEl = document.getElementById("interval");
const providerEl = document.getElementById("provider");
const emailEl = document.getElementById("email");
const connectionsEl = document.getElementById("connections");

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

async function refresh() {
  const status = await (await fetch("/api/autopilot/status")).json();
  statusEl.textContent = JSON.stringify(status, null, 2);

  const brief = await (await fetch("/api/brief")).json();
  briefEl.textContent = JSON.stringify(brief, null, 2);

  const connectionData = await (await fetch("/api/email/connections")).json();
  connectionsEl.textContent = JSON.stringify(connectionData, null, 2);
}

setInterval(refresh, 5000);
refresh();
