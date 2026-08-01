const IDS = [
  "citizen_seed_version",
  "citizen_id",
  "birth_hash",
  "birth_timestamp",
  "citizen_age",
  "alive_status",
  "cluster_connection_status",
  "node",
  "identity_status",
  "heartbeat",
  "last_sync",
  "telemetry_status",
  "memory_status",
  "filesystem_status",
  "evidence_status",
  "ui_port",
  "current_version",
  "latest_evolution",
  "evolution_date",
  "current_version_label",
];

async function refresh() {
  const err = document.getElementById("err");
  try {
    const r = await fetch("/api/console", { cache: "no-store" });
    const d = await r.json();
    err.hidden = true;
    for (const id of IDS) {
      const el = document.getElementById(id);
      if (!el) continue;
      el.textContent = d[id] == null ? "—" : String(d[id]);
    }

    const alive = document.getElementById("vital_alive");
    const conn = document.getElementById("vital_connected");
    alive.classList.toggle("on", !!d.is_alive);
    conn.classList.toggle("on", !!d.is_connected);
    conn.classList.toggle("off", !d.is_connected);

    if (d.cluster_connection_status === "Offline" && d.is_alive) {
      document.getElementById("cluster_connection_status").textContent = "Offline";
    }

    // Evolutionary line color on SYNC word (fixed palette)
    const syncWord = document.getElementById("sync_word");
    if (d.sync_color) {
      document.documentElement.style.setProperty("--sync-line", d.sync_color);
      syncWord.style.color = d.sync_color;
    }

    const btn = document.getElementById("sync_btn");
    btn.classList.toggle("update-pulse", !!d.update_available);

    const banner = document.getElementById("update_banner");
    if (d.update_available) {
      banner.hidden = false;
      banner.textContent = d.update_label || "Update Available";
    } else {
      banner.hidden = true;
    }

    const badge = document.getElementById("gen_badge");
    badge.textContent = d.badge || "SEED 0.1";
    badge.className = "badge " + (d.badge_class || "gen-seed");

    renderEvolutionHistory(d.evolution_history || []);
    await refreshEvents();
  } catch (e) {
    err.hidden = false;
    err.textContent = String(e);
  }
}

function renderEvolutionHistory(hist) {
  const ol = document.getElementById("evolution_timeline");
  ol.innerHTML = "";
  if (!hist.length) {
    const li = document.createElement("li");
    li.textContent = "History begins at Birth.";
    ol.appendChild(li);
    return;
  }
  hist.forEach((row, i) => {
    const li = document.createElement("li");
    const label = row.kind === "birth" ? "Birth" : String(row.version || row.label || "—");
    li.innerHTML =
      `<span class="ver">${escapeHtml(label)}</span>` +
      `<span class="meta">${escapeHtml(row.ts || "")}` +
      (row.evidence_id ? ` · ${escapeHtml(row.evidence_id)}` : "") +
      `</span>`;
    ol.appendChild(li);
    if (i < hist.length - 1) {
      const arrow = document.createElement("li");
      arrow.className = "arrow";
      arrow.textContent = "↓";
      ol.appendChild(arrow);
    }
  });
}

async function refreshEvents() {
  const ul = document.getElementById("event_log");
  const r = await fetch("/api/events", { cache: "no-store" });
  const d = await r.json();
  ul.innerHTML = "";
  const events = (d.events || []).slice(0, 24);
  if (!events.length) {
    const li = document.createElement("li");
    li.textContent = "No important events yet.";
    ul.appendChild(li);
    return;
  }
  for (const ev of events) {
    const li = document.createElement("li");
    li.innerHTML =
      `<span class="ts">${escapeHtml(ev.ts || "")}</span>` +
      `<span class="kind">${escapeHtml(ev.kind || "")}</span>` +
      `<span class="msg">${escapeHtml(ev.message || "")}</span>`;
    ul.appendChild(li);
  }
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function runSync() {
  const btn = document.getElementById("sync_btn");
  const msg = document.getElementById("sync_msg");
  btn.disabled = true;
  msg.hidden = false;
  msg.textContent = "SYNC in progress…";
  try {
    const r = await fetch("/api/sync", { method: "POST" });
    const d = await r.json();
    const cluster = d.cluster_connection || "Offline";
    const ver = d.current_version ? `v${d.current_version}` : "";
    msg.textContent = `SYNC complete · Alive · ${cluster}` + (ver ? ` · ${ver}` : "");
    // Pulse clears after successful sync (update_available false in refresh)
    await refresh();
  } catch (e) {
    msg.textContent = "SYNC could not finish network steps — Citizen remains Alive.";
  } finally {
    btn.disabled = false;
  }
}

document.getElementById("sync_btn").addEventListener("click", runSync);
refresh();
setInterval(refresh, 5000);
