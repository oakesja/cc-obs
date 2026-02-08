import json

EVENT_COLORS = {
    "SessionStart": "#22c55e",
    "Stop": "#6b7280",
    "UserPromptSubmit": "#a855f7",
    "PreToolUse": "#3b82f6",
    "PermissionRequest": "#3b82f6",
    "PostToolUse": "#14b8a6",
    "PostToolUseFailure": "#ef4444",
    "SubagentStart": "#f97316",
    "SubagentStop": "#f97316",
    "PreCompact": "#6b7280",
    "Notification": "#eab308",
    "TeammateIdle": "#6366f1",
    "TaskCompleted": "#6366f1",
}


def render_html(events: list[dict]) -> str:
    data_json = json.dumps(events)
    return HTML_TEMPLATE.replace("__EVENTS_DATA__", data_json)


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>cc-obs viewer</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.5; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
h1 { font-size: 1.5rem; margin-bottom: 4px; }
h2 { font-size: 1.2rem; margin: 20px 0 10px; color: #94a3b8; }
h3 { font-size: 1rem; margin: 12px 0 6px; color: #94a3b8; }

/* Dashboard */
.dashboard { background: #1e293b; border-radius: 8px; padding: 16px; margin-bottom: 20px; }
.dash-row { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 12px; }
.dash-item { min-width: 120px; }
.dash-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
.dash-value { font-size: 1.1rem; font-weight: 600; }
.stat-grid { display: flex; gap: 8px; flex-wrap: wrap; }
.stat-card { background: #334155; border-radius: 6px; padding: 6px 12px; font-size: 0.85rem; }
.stat-card .count { font-weight: 700; margin-right: 4px; }

/* Controls */
.controls { background: #1e293b; border-radius: 8px; padding: 12px 16px; margin-bottom: 20px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
.controls input[type="text"] { background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 6px 12px; color: #e2e8f0; font-size: 0.85rem; width: 260px; }
.controls label { font-size: 0.8rem; cursor: pointer; display: flex; align-items: center; gap: 4px; }
.controls input[type="checkbox"] { accent-color: #3b82f6; }
.filter-group { display: flex; gap: 8px; flex-wrap: wrap; }

/* Tabs */
.tabs { display: flex; gap: 4px; margin-bottom: 20px; }
.tab-btn { background: #334155; color: #94a3b8; border: none; padding: 8px 20px; border-radius: 6px; cursor: pointer; font-size: 0.9rem; font-weight: 500; transition: background 0.15s, color 0.15s; }
.tab-btn:hover { background: #475569; color: #e2e8f0; }
.tab-btn.active { background: #3b82f6; color: #fff; }
.view-container { display: none; }
.view-container.active { display: block; }

/* Timeline */
.event-card { background: #1e293b; border-radius: 8px; margin-bottom: 6px; border-left: 4px solid #334155; overflow: hidden; }
.event-header { display: flex; align-items: center; gap: 10px; padding: 8px 12px; cursor: pointer; user-select: none; }
.event-header:hover { background: #334155; }
.event-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; color: #fff; white-space: nowrap; width: 150px; text-align: center; flex-shrink: 0; }
.event-time { font-size: 0.75rem; color: #64748b; font-family: monospace; white-space: nowrap; width: 65px; text-align: right; flex-shrink: 0; }
.event-summary { font-size: 0.85rem; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.event-summary code { background: #334155; padding: 1px 4px; border-radius: 3px; font-size: 0.8rem; }
.wrap-badge { font-size: 0.7rem; background: #334155; padding: 2px 6px; border-radius: 4px; white-space: nowrap; }
.wrap-badge.ok { color: #22c55e; }
.wrap-badge.fail { color: #ef4444; }
.event-detail { padding: 8px 12px; background: #0f172a; border-top: 1px solid #334155; display: none; }
.event-detail pre { font-size: 0.8rem; white-space: pre-wrap; word-break: break-all; color: #94a3b8; max-height: 400px; overflow-y: auto; }
.gap-marker { text-align: center; padding: 2px 0; font-size: 0.7rem; color: #475569; }

/* Agent tree */
.agent-tree { background: #1e293b; border-radius: 8px; padding: 16px; margin-bottom: 20px; }
.agent-node { margin-left: 20px; border-left: 2px solid #334155; padding-left: 12px; margin-bottom: 8px; }
.agent-node.root { margin-left: 0; border-left: none; padding-left: 0; }
.agent-header { cursor: pointer; padding: 4px 0; font-size: 0.9rem; }
.agent-header:hover { color: #60a5fa; }
.agent-events { display: none; margin-top: 4px; }
.agent-badge { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 0.7rem; background: #f97316; color: #fff; margin-right: 4px; }

/* Spans / Traces */
.spans-container { background: #1e293b; border-radius: 8px; padding: 16px; overflow-x: auto; }
.spans-time-axis { display: flex; position: relative; height: 24px; margin-left: 200px; margin-bottom: 8px; border-bottom: 1px solid #334155; }
.spans-tick { position: absolute; font-size: 0.7rem; color: #64748b; transform: translateX(-50%); }
.spans-tick::after { content: ""; position: absolute; left: 50%; top: 16px; width: 1px; height: 6px; background: #475569; }
.span-row { display: flex; align-items: center; height: 28px; position: relative; }
.span-row:hover { background: #1a2744; }
.span-label { width: 200px; flex-shrink: 0; font-size: 0.8rem; color: #94a3b8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; padding-right: 8px; }
.span-label.depth-1 { padding-left: 20px; }
.span-bar-area { flex: 1; position: relative; height: 20px; }
.span-bar { position: absolute; height: 16px; top: 2px; border-radius: 3px; min-width: 3px; cursor: pointer; opacity: 0.85; transition: opacity 0.1s; }
.span-bar:hover { opacity: 1; }
.span-marker { position: absolute; width: 2px; height: 20px; top: 0; cursor: pointer; opacity: 0.85; }
.span-marker:hover { opacity: 1; }
.span-tooltip { position: fixed; background: #1e293b; border: 1px solid #475569; border-radius: 6px; padding: 8px 12px; font-size: 0.8rem; color: #e2e8f0; pointer-events: none; z-index: 100; max-width: 400px; white-space: pre-line; display: none; }
.span-detail { background: #0f172a; border-top: 1px solid #334155; padding: 8px 12px; margin-left: 200px; display: none; }
.span-detail pre { font-size: 0.8rem; white-space: pre-wrap; word-break: break-all; color: #94a3b8; max-height: 300px; overflow-y: auto; }
</style>
</head>
<body>
<div class="container">
<h1>cc-obs session viewer</h1>

<div id="dashboard" class="dashboard"></div>

<div class="controls">
  <input type="text" id="search" placeholder="Search events..." oninput="filterEvents()">
  <div class="filter-group" id="filters"></div>
</div>

<div class="tabs">
  <button class="tab-btn active" onclick="switchTab('timeline')">Timeline</button>
  <button class="tab-btn" onclick="switchTab('agent-tree')">Agent Tree</button>
  <button class="tab-btn" onclick="switchTab('spans')">Spans</button>
</div>

<div id="view-timeline" class="view-container active">
  <div id="timeline"></div>
</div>

<div id="view-agent-tree" class="view-container">
  <div id="agent-tree" class="agent-tree"></div>
</div>

<div id="view-spans" class="view-container">
  <div id="spans" class="spans-container"></div>
</div>
</div>

<div id="span-tooltip" class="span-tooltip"></div>

<script>
const EVENTS = __EVENTS_DATA__;
const COLORS = {
  SessionStart:"#22c55e", Stop:"#6b7280", UserPromptSubmit:"#a855f7",
  PreToolUse:"#3b82f6", PermissionRequest:"#3b82f6", PostToolUse:"#14b8a6",
  PostToolUseFailure:"#ef4444", SubagentStart:"#f97316", SubagentStop:"#f97316",
  PreCompact:"#6b7280", Notification:"#eab308", TeammateIdle:"#6366f1",
  TaskCompleted:"#6366f1"
};

const eventTypes = [...new Set(EVENTS.map(e => e.hook_event_name).filter(Boolean))];
let activeFilters = new Set(eventTypes);

function init() {
  renderDashboard();
  renderFilters();
  renderTimeline();
  renderAgentTree();
  renderSpans();
}

function switchTab(name) {
  document.querySelectorAll(".view-container").forEach(v => v.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  document.getElementById("view-" + name).classList.add("active");
  const labels = {"timeline": "Timeline", "agent-tree": "Agent Tree", "spans": "Spans"};
  document.querySelectorAll(".tab-btn").forEach(b => {
    if (b.textContent === labels[name]) b.classList.add("active");
  });
}

function renderDashboard() {
  const el = document.getElementById("dashboard");
  if (!EVENTS.length) { el.innerHTML = "<p>No events</p>"; return; }

  const first = EVENTS[0], last = EVENTS[EVENTS.length-1];
  const sessionId = first.session_id || "unknown";
  const model = first.model || "unknown";

  const typeCounts = {};
  const toolCounts = {};
  EVENTS.forEach(e => {
    const t = e.hook_event_name || "unknown";
    typeCounts[t] = (typeCounts[t]||0) + 1;
    if (e.tool_name) toolCounts[e.tool_name] = (toolCounts[e.tool_name]||0) + 1;
  });

  let spanStr = "";
  if (first._ts && last._ts) {
    const secs = (new Date(last._ts) - new Date(first._ts)) / 1000;
    spanStr = secs < 60 ? secs.toFixed(1)+"s" : secs < 3600 ? (secs/60).toFixed(1)+"m" : (secs/3600).toFixed(1)+"h";
  }

  let wrapCount = 0, wrapMs = 0;
  EVENTS.forEach(e => { if(e._wrap) { wrapCount++; wrapMs += e._wrap.duration_ms||0; }});

  let html = `<div class="dash-row">
    <div class="dash-item"><div class="dash-label">Session</div><div class="dash-value">${esc(sessionId)}</div></div>
    <div class="dash-item"><div class="dash-label">Model</div><div class="dash-value">${esc(model)}</div></div>
    <div class="dash-item"><div class="dash-label">Events</div><div class="dash-value">${EVENTS.length}</div></div>
    <div class="dash-item"><div class="dash-label">Span</div><div class="dash-value">${spanStr}</div></div>
    ${wrapCount ? `<div class="dash-item"><div class="dash-label">Hook time</div><div class="dash-value">${wrapMs.toFixed(0)}ms (${wrapCount})</div></div>` : ""}
  </div>`;

  html += `<h3>Events</h3><div class="stat-grid">`;
  Object.entries(typeCounts).sort((a,b)=>b[1]-a[1]).forEach(([name,count]) => {
    const c = COLORS[name]||"#64748b";
    html += `<div class="stat-card"><span class="count" style="color:${c}">${count}</span>${esc(name)}</div>`;
  });
  html += `</div>`;

  if (Object.keys(toolCounts).length) {
    html += `<h3>Tools</h3><div class="stat-grid">`;
    Object.entries(toolCounts).sort((a,b)=>b[1]-a[1]).forEach(([name,count]) => {
      html += `<div class="stat-card"><span class="count">${count}</span>${esc(name)}</div>`;
    });
    html += `</div>`;
  }

  el.innerHTML = html;
}

function renderFilters() {
  const el = document.getElementById("filters");
  el.innerHTML = eventTypes.map(t => {
    const c = COLORS[t]||"#64748b";
    return `<label><input type="checkbox" checked onchange="toggleFilter('${t}', this.checked)" style="accent-color:${c}"> ${t}</label>`;
  }).join("");
}

function toggleFilter(type, on) {
  if (on) activeFilters.add(type); else activeFilters.delete(type);
  filterEvents();
}

function filterEvents() {
  const q = document.getElementById("search").value.toLowerCase();
  document.querySelectorAll(".event-card").forEach(card => {
    const type = card.dataset.type;
    const text = card.dataset.text;
    const typeOk = activeFilters.has(type);
    const searchOk = !q || text.includes(q);
    card.style.display = typeOk && searchOk ? "" : "none";
  });
  document.querySelectorAll(".gap-marker").forEach(g => g.style.display = "");
}

function renderTimeline() {
  const el = document.getElementById("timeline");
  if (!EVENTS.length) { el.innerHTML = "<p>No events</p>"; return; }

  const t0 = EVENTS[0]._ts ? new Date(EVENTS[0]._ts) : null;
  let html = "";

  EVENTS.forEach((e, i) => {
    const type = e.hook_event_name || "unknown";
    const color = COLORS[type] || "#64748b";

    // Gap marker
    if (i > 0 && EVENTS[i-1]._ts && e._ts) {
      const gap = (new Date(e._ts) - new Date(EVENTS[i-1]._ts)) / 1000;
      if (gap > 1) {
        html += `<div class="gap-marker">⋯ ${gap.toFixed(1)}s gap ⋯</div>`;
      }
    }

    let relTime = "";
    if (t0 && e._ts) {
      const rel = (new Date(e._ts) - t0) / 1000;
      relTime = "+" + rel.toFixed(1) + "s";
    }

    let summary = summarize(e);
    let wrapBadge = "";
    if (e._wrap) {
      const cls = e._wrap.exit_code === 0 ? "ok" : "fail";
      wrapBadge = `<span class="wrap-badge ${cls}">${e._wrap.duration_ms}ms exit:${e._wrap.exit_code}</span>`;
    }
    let agentBadge = "";
    if (e._agent_id) {
      agentBadge = `<span class="agent-badge">${esc(e._agent_type || e._agent_id)}</span>`;
    }

    const text = JSON.stringify(e).toLowerCase();

    html += `<div class="event-card" data-type="${type}" data-text="${esc(text)}" style="border-left-color:${color}">
      <div class="event-header" onclick="toggleDetail(this)">
        <span class="event-badge" style="background:${color}">${esc(type)}</span>
        <span class="event-time">${relTime}</span>
        <span class="event-summary">${summary}</span>
        ${agentBadge}${wrapBadge}
      </div>
      <div class="event-detail"><pre>${esc(JSON.stringify(e, null, 2))}</pre></div>
    </div>`;
  });

  el.innerHTML = html;
}

function summarize(e) {
  const type = e.hook_event_name;
  if (type === "SessionStart") return `source: <code>${esc(e.source||"")}</code>`;
  if (type === "UserPromptSubmit") {
    const p = e.prompt || "";
    return `<code>${esc(p.length > 80 ? p.slice(0,80)+"…" : p)}</code>`;
  }
  if (e.tool_name) {
    let detail = "";
    const inp = e.tool_input || {};
    if (e.tool_name === "Bash") detail = inp.command || "";
    else if (e.tool_name === "Read" || e.tool_name === "Write" || e.tool_name === "Edit") detail = inp.file_path || "";
    else if (e.tool_name === "Glob") detail = inp.pattern || "";
    else if (e.tool_name === "Grep") detail = inp.pattern || "";
    else if (e.tool_name === "Task") detail = inp.description || "";
    else detail = Object.keys(inp).slice(0,2).join(", ");
    if (detail.length > 80) detail = detail.slice(0,80) + "…";
    return `${esc(e.tool_name)}: <code>${esc(detail)}</code>`;
  }
  if (type === "SubagentStart") return `agent: <code>${esc(e.agent_type||"")} ${esc(e.agent_id||"")}</code>`;
  if (type === "SubagentStop") return `agent: <code>${esc(e.agent_id||"")}</code>`;
  if (type === "Notification") return `<code>${esc((e.message||"").slice(0,80))}</code>`;
  return "";
}

function toggleDetail(header) {
  const detail = header.nextElementSibling;
  detail.style.display = detail.style.display === "none" || !detail.style.display ? "block" : "none";
}

function renderAgentTree() {
  const el = document.getElementById("agent-tree");
  const starts = EVENTS.filter(e => e.hook_event_name === "SubagentStart");
  if (!starts.length) { el.innerHTML = "<p>No subagent activity</p>"; return; }

  // Group events by agent_id (or enriched _agent_id)
  const agentEvents = {};
  EVENTS.forEach(e => {
    const aid = e.agent_id || e._agent_id;
    if (aid) {
      if (!agentEvents[aid]) agentEvents[aid] = [];
      agentEvents[aid].push(e);
    }
  });

  // Build agent info from SubagentStart events
  const agents = starts.map(s => ({
    id: s.agent_id || "unknown",
    type: s.agent_type || s.subagent_type || "unknown",
    parent: s.parent_agent_id || "main",
    events: agentEvents[s.agent_id] || []
  }));

  // Deduplicate by id
  const seen = new Set();
  const unique = agents.filter(a => { if(seen.has(a.id)) return false; seen.add(a.id); return true; });

  let html = `<div class="agent-node root"><div class="agent-header" onclick="toggleAgentEvents(this)">▸ Main Session (${EVENTS.length} events)</div><div class="agent-events"><pre>${esc(JSON.stringify({session_id: EVENTS[0]?.session_id, model: EVENTS[0]?.model}, null, 2))}</pre></div></div>`;

  unique.forEach(a => {
    html += `<div class="agent-node">
      <div class="agent-header" onclick="toggleAgentEvents(this)">
        <span class="agent-badge">${esc(a.type)}</span> ▸ ${esc(a.id)} (${a.events.length} events)
      </div>
      <div class="agent-events">`;
    a.events.forEach(e => {
      const type = e.hook_event_name || "";
      const color = COLORS[type]||"#64748b";
      html += `<div style="padding:2px 0;font-size:0.8rem;"><span class="event-badge" style="background:${color};font-size:0.65rem">${esc(type)}</span> ${summarize(e)}</div>`;
    });
    html += `</div></div>`;
  });

  el.innerHTML = html;
}

function toggleAgentEvents(header) {
  const detail = header.nextElementSibling;
  if (!detail) return;
  detail.style.display = detail.style.display === "none" || !detail.style.display ? "block" : "none";
  header.textContent = header.textContent.replace(/[▸▾]/, detail.style.display === "block" ? "▾" : "▸");
}

function renderSpans() {
  const el = document.getElementById("spans");
  if (!EVENTS.length) { el.innerHTML = "<p>No events</p>"; return; }

  const tsEvents = EVENTS.filter(e => e._ts);
  if (tsEvents.length < 2) { el.innerHTML = "<p>Not enough timestamped events for span view</p>"; return; }

  const t0 = new Date(tsEvents[0]._ts).getTime();
  const t1 = new Date(tsEvents[tsEvents.length - 1]._ts).getTime();
  const duration = t1 - t0;
  if (duration <= 0) { el.innerHTML = "<p>All events at same timestamp</p>"; return; }

  // Build tool spans: match PreToolUse -> PostToolUse/PostToolUseFailure by tool_use_id
  const preTools = {};
  const toolSpans = [];
  EVENTS.forEach(e => {
    if (e.hook_event_name === "PreToolUse" && e.tool_use_id) {
      preTools[e.tool_use_id] = e;
    }
    if ((e.hook_event_name === "PostToolUse" || e.hook_event_name === "PostToolUseFailure") && e.tool_use_id && preTools[e.tool_use_id]) {
      const pre = preTools[e.tool_use_id];
      toolSpans.push({
        type: "tool",
        label: pre.tool_name || "Tool",
        start: new Date(pre._ts).getTime(),
        end: new Date(e._ts).getTime(),
        color: COLORS[e.hook_event_name] || "#14b8a6",
        agentId: pre._agent_id || null,
        failed: e.hook_event_name === "PostToolUseFailure",
        events: [pre, e]
      });
    }
  });

  // Build agent spans: match SubagentStart -> SubagentStop by agent_id
  const agentStarts = {};
  const agentSpans = [];
  EVENTS.forEach(e => {
    if (e.hook_event_name === "SubagentStart" && e.agent_id) {
      agentStarts[e.agent_id] = e;
    }
    if (e.hook_event_name === "SubagentStop" && e.agent_id && agentStarts[e.agent_id]) {
      const start = agentStarts[e.agent_id];
      agentSpans.push({
        type: "agent",
        label: (start.agent_type || "agent") + " " + start.agent_id,
        shortLabel: start.agent_type || start.agent_id,
        agentId: start.agent_id,
        start: new Date(start._ts).getTime(),
        end: new Date(e._ts).getTime(),
        color: COLORS.SubagentStart,
        events: [start, e]
      });
    }
  });

  // Point events
  const pointTypes = new Set(["SessionStart", "Stop", "UserPromptSubmit", "Notification", "PreCompact"]);
  const pointEvents = EVENTS.filter(e => pointTypes.has(e.hook_event_name) && e._ts).map(e => ({
    type: "point",
    label: e.hook_event_name,
    start: new Date(e._ts).getTime(),
    end: new Date(e._ts).getTime(),
    color: COLORS[e.hook_event_name] || "#64748b",
    events: [e]
  }));

  // Build rows: session-level tools (no agent), then for each agent: agent span + child tools
  const rows = [];

  // Session-level point events and tools without agent
  const sessionTools = toolSpans.filter(s => !s.agentId);
  const sessionItems = [...pointEvents, ...sessionTools].sort((a, b) => a.start - b.start);
  sessionItems.forEach(s => rows.push({ ...s, depth: 0 }));

  // Agent spans with nested children
  agentSpans.sort((a, b) => a.start - b.start).forEach(agent => {
    rows.push({ ...agent, depth: 0 });
    const children = toolSpans.filter(s => s.agentId === agent.agentId).sort((a, b) => a.start - b.start);
    children.forEach(s => rows.push({ ...s, depth: 1, label: s.label }));
  });

  // Render time axis
  const tickCount = 6;
  let axisHtml = '<div class="spans-time-axis">';
  for (let i = 0; i <= tickCount; i++) {
    const pct = (i / tickCount) * 100;
    const secs = (duration * i / tickCount) / 1000;
    const label = secs < 60 ? secs.toFixed(0) + "s" : (secs / 60).toFixed(1) + "m";
    axisHtml += `<span class="spans-tick" style="left:${pct}%">${label}</span>`;
  }
  axisHtml += '</div>';

  // Render rows
  let rowsHtml = '';
  rows.forEach((row, idx) => {
    const leftPct = ((row.start - t0) / duration) * 100;
    const widthPct = Math.max(((row.end - row.start) / duration) * 100, 0.3);
    const depthClass = row.depth === 1 ? ' depth-1' : '';
    const displayLabel = row.depth === 1 ? '\u21b3 ' + row.label : row.label;
    const durationMs = row.end - row.start;
    const durationLabel = durationMs > 0 ? (durationMs < 1000 ? durationMs + "ms" : (durationMs / 1000).toFixed(1) + "s") : "";

    if (row.type === "point") {
      rowsHtml += `<div class="span-row" data-span-idx="${idx}">
        <div class="span-label${depthClass}" title="${esc(displayLabel)}">${esc(displayLabel)}</div>
        <div class="span-bar-area">
          <div class="span-marker" style="left:${leftPct}%;background:${row.color}" data-span-idx="${idx}"></div>
        </div>
      </div>`;
    } else {
      rowsHtml += `<div class="span-row" data-span-idx="${idx}">
        <div class="span-label${depthClass}" title="${esc(displayLabel)}">${esc(displayLabel)}${durationLabel ? ' <span style="color:#64748b;font-size:0.7rem">' + durationLabel + '</span>' : ''}</div>
        <div class="span-bar-area">
          <div class="span-bar" style="left:${leftPct}%;width:${widthPct}%;background:${row.color}" data-span-idx="${idx}"></div>
        </div>
      </div>`;
    }
    rowsHtml += `<div class="span-detail" id="span-detail-${idx}"><pre></pre></div>`;
  });

  el.innerHTML = axisHtml + rowsHtml;

  // Tooltip handlers
  const tooltip = document.getElementById("span-tooltip");
  el.querySelectorAll(".span-bar, .span-marker").forEach(bar => {
    bar.addEventListener("mouseenter", function(ev) {
      const row = rows[this.dataset.spanIdx];
      const durationMs = row.end - row.start;
      const dur = durationMs > 0 ? (durationMs < 1000 ? durationMs + "ms" : (durationMs / 1000).toFixed(1) + "s") : "instant";
      let text = row.label + "\n";
      text += "Duration: " + dur + "\n";
      if (row.events[0]._ts) text += "Start: " + row.events[0]._ts + "\n";
      if (row.events.length > 1 && row.events[1]._ts) text += "End: " + row.events[1]._ts;
      if (row.failed) text += "\nFAILED";
      tooltip.textContent = text;
      tooltip.style.display = "block";
    });
    bar.addEventListener("mousemove", function(ev) {
      tooltip.style.left = (ev.clientX + 12) + "px";
      tooltip.style.top = (ev.clientY + 12) + "px";
    });
    bar.addEventListener("mouseleave", function() {
      tooltip.style.display = "none";
    });
  });

  // Click to expand detail
  el.querySelectorAll(".span-row").forEach(row => {
    row.addEventListener("click", function() {
      const idx = this.dataset.spanIdx;
      const detail = document.getElementById("span-detail-" + idx);
      if (!detail) return;
      const isOpen = detail.style.display === "block";
      detail.style.display = isOpen ? "none" : "block";
      if (!isOpen) {
        const r = rows[idx];
        detail.querySelector("pre").textContent = JSON.stringify(r.events, null, 2);
      }
    });
  });
}

function esc(s) {
  if (typeof s !== "string") return "";
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

init();
</script>
</body>
</html>"""
