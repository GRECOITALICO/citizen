const citizenId = document.getElementById("citizen-id");
const ageEl = document.getElementById("age");
const runtimeEl = document.getElementById("runtime-version");
const manifestEl = document.getElementById("manifest-version");
const syncBtn = document.getElementById("sync-btn");
const exportBtn = document.getElementById("export-btn");
const termEl = document.getElementById("term");
const bioEl = document.getElementById("bio");
const timelineEl = document.getElementById("timeline");
const nodeDetail = document.getElementById("node-detail");

let busy = false;

function paintSync(state, color) {
  syncBtn.textContent = state || "Current";
  syncBtn.classList.remove("green", "orange");
  syncBtn.classList.add(color === "orange" ? "orange" : "green");
  const clickable = color === "orange" && state === "Update Available";
  syncBtn.disabled = busy || !clickable;
}

async function refreshState() {
  const r = await fetch("/api/state");
  const s = await r.json();
  if (s.error) return;
  citizenId.textContent = s.citizen_id || "—";
  ageEl.textContent = s.age || "—";
  runtimeEl.textContent = s.runtime_version || "—";
  manifestEl.textContent = s.manifest_version || "—";
  if (!busy) paintSync(s.sync_state, s.sync_color);
}

async function refreshTerminal() {
  const r = await fetch("/api/terminal");
  const s = await r.json();
  termEl.textContent = (s.lines || []).join("\n");
  termEl.scrollTop = termEl.scrollHeight;
}

async function refreshJournal() {
  const [j, t] = await Promise.all([
    fetch("/api/journal").then((r) => r.json()),
    fetch("/api/timeline").then((r) => r.json()),
  ]);
  bioEl.textContent = j.biography || "";
  const nodes = t.nodes || [];
  timelineEl.innerHTML = "";
  nodes.forEach((n, i) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "t-node";
    btn.innerHTML =
      `<span class="dot"></span><span><div class="label">${n.label || n.node}</div>` +
      `<div class="meta">${n.ts || ""}${i < nodes.length - 1 ? " ↓" : ""}</div></span>`;
    btn.addEventListener("click", () => openNode(n.node));
    timelineEl.appendChild(btn);
  });
}

async function openNode(node) {
  const r = await fetch("/api/timeline/node?node=" + encodeURIComponent(node));
  const s = await r.json();
  nodeDetail.classList.remove("hidden");
  nodeDetail.textContent = JSON.stringify(s, null, 2);
}

syncBtn.addEventListener("click", async () => {
  if (busy || syncBtn.disabled) return;
  busy = true;
  syncBtn.classList.add("busy");
  paintSync("Updating", "orange");
  try {
    const r = await fetch("/api/sync", { method: "POST" });
    const result = await r.json();
    paintSync(result.error ? "Error" : result.state || "Updated", result.error ? "orange" : "green");
  } catch (_) {
    paintSync("Error", "orange");
  } finally {
    busy = false;
    syncBtn.classList.remove("busy");
    await tick();
  }
});

exportBtn.addEventListener("click", async () => {
  exportBtn.disabled = true;
  exportBtn.textContent = "Exporting…";
  try {
    const r = await fetch("/api/export-birth", { method: "POST" });
    const s = await r.json();
    exportBtn.textContent = s.archive ? "Exported" : "Export failed";
    setTimeout(() => {
      exportBtn.textContent = "Export Birth Package";
      exportBtn.disabled = false;
    }, 2000);
  } catch (_) {
    exportBtn.textContent = "Export failed";
    exportBtn.disabled = false;
  }
});

async function tick() {
  try {
    await refreshState();
    await refreshTerminal();
    await refreshJournal();
  } catch (_) {}
}

tick();
setInterval(tick, 1500);
