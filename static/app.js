const statusEl = document.getElementById("status");
const briefEl = document.getElementById("brief");
const intervalEl = document.getElementById("interval");

document.getElementById("start").addEventListener("click", async () => {
  const interval = Number(intervalEl.value || 300);
  await fetch(`/api/autopilot/start?interval_seconds=${interval}`, { method: "POST" });
  await refresh();
});

document.getElementById("stop").addEventListener("click", async () => {
  await fetch("/api/autopilot/stop", { method: "POST" });
  await refresh();
});

async function refresh() {
  const status = await (await fetch("/api/autopilot/status")).json();
  statusEl.textContent = JSON.stringify(status, null, 2);

  const brief = await (await fetch("/api/brief")).json();
  briefEl.textContent = JSON.stringify(brief, null, 2);
}

setInterval(refresh, 5000);
refresh();
