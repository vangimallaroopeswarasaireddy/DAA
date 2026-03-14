const API_BASE = "http://127.0.0.1:8000";

const token = localStorage.getItem("token");
if (!token) {
  window.location.href = "index.html";
}

const userInfo = document.getElementById("userInfo");
const logoutBtn = document.getElementById("logoutBtn");
const optimizeForm = document.getElementById("optimizeForm");
const dashboardMessage = document.getElementById("dashboardMessage");
const resultArea = document.getElementById("resultArea");
const summaryPanel = document.getElementById("summaryPanel");
const loadHistoryBtn = document.getElementById("loadHistoryBtn");
const historyArea = document.getElementById("historyArea");

function showDashboardMessage(text, type = "success") {
  dashboardMessage.textContent = text;
  dashboardMessage.className = `message ${type}`;
  dashboardMessage.classList.remove("hidden");
}

function authHeaders() {
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  };
}

function parseEdges(rawText) {
  const lines = rawText
    .split("\n")
    .map(line => line.trim())
    .filter(Boolean);

  return lines.map((line, index) => {
    const parts = line.split(",").map(x => x.trim());

    if (parts.length !== 4) {
      throw new Error(`Invalid edge format on line ${index + 1}`);
    }

    const [from_node, to_node, base_cost, capacity] = parts;

    if (!from_node || !to_node) {
      throw new Error(`Invalid node name on line ${index + 1}`);
    }

    const parsedBaseCost = Number(base_cost);
    const parsedCapacity = Number(capacity);

    if (Number.isNaN(parsedBaseCost) || Number.isNaN(parsedCapacity)) {
      throw new Error(`Invalid numeric value on line ${index + 1}`);
    }

    return {
      from_node,
      to_node,
      base_cost: parsedBaseCost,
      capacity: parsedCapacity
    };
  });
}

function renderSummary(data) {
  summaryPanel.innerHTML = `
    <div class="summary-grid">
      <div class="summary-item">
        <strong>Run ID</strong>
        <span>${data.run_id ?? "-"}</span>
      </div>
      <div class="summary-item">
        <strong>Status</strong>
        <span>${data.status}</span>
      </div>
      <div class="summary-item">
        <strong>Total Cost</strong>
        <span>${data.total_cost}</span>
      </div>
      <div class="summary-item">
        <strong>Delivered Volume</strong>
        <span>${data.delivered_volume}</span>
      </div>
      <div class="summary-item">
        <strong>Total Demand</strong>
        <span>${data.total_demand}</span>
      </div>
      <div class="summary-item">
        <strong>Unmet Demand</strong>
        <span>${data.unmet_demand}</span>
      </div>
      <div class="summary-item">
        <strong>Hours</strong>
        <span>${data.hours}</span>
      </div>
      <div class="summary-item">
        <strong>Note</strong>
        <span>${data.note || "None"}</span>
      </div>
    </div>
  `;
}

function renderSchedule(data) {
  if (!data.schedule || data.schedule.length === 0) {
    resultArea.innerHTML = "<p>No schedule returned.</p>";
    return;
  }

  let html = "";

  data.schedule.forEach(hourBlock => {
    html += `
      <div class="result-hour">
        <h3>Hour ${hourBlock.hour}</h3>
        <p><strong>Delivered this hour:</strong> ${hourBlock.delivered_this_hour}</p>
        <p><strong>Hour cost:</strong> ${hourBlock.hour_cost}</p>
    `;

    if (!hourBlock.flows || hourBlock.flows.length === 0) {
      html += `<p>No flow used in this hour.</p>`;
    } else {
      html += `
        <table class="flow-table">
          <thead>
            <tr>
              <th>From</th>
              <th>To</th>
              <th>Flow</th>
              <th>Effective Cost</th>
              <th>Edge Cost Total</th>
            </tr>
          </thead>
          <tbody>
      `;

      hourBlock.flows.forEach(flow => {
        html += `
          <tr>
            <td>${flow.from_node}</td>
            <td>${flow.to_node}</td>
            <td>${flow.flow}</td>
            <td>${flow.effective_cost}</td>
            <td>${flow.edge_cost_total}</td>
          </tr>
        `;
      });

      html += `
          </tbody>
        </table>
      `;
    }

    html += `</div>`;
  });

  resultArea.innerHTML = html;
}

function renderHistory(runs) {
  if (!runs || runs.length === 0) {
    historyArea.innerHTML = "<p>No optimization history found.</p>";
    return;
  }

  let html = `
    <table class="history-table">
      <thead>
        <tr>
          <th>Run ID</th>
          <th>Source</th>
          <th>Sink</th>
          <th>Total Demand</th>
          <th>Delivered</th>
          <th>Hours</th>
          <th>Total Cost</th>
          <th>Status</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
  `;

  runs.forEach(run => {
    html += `
      <tr>
        <td>${run.run_id}</td>
        <td>${run.source}</td>
        <td>${run.sink}</td>
        <td>${run.total_demand}</td>
        <td>${run.delivered_volume}</td>
        <td>${run.hours}</td>
        <td>${run.total_cost}</td>
        <td>${run.status}</td>
        <td class="history-actions">
          <button class="view-btn" onclick="loadRunById(${run.run_id})">View</button>
        </td>
      </tr>
    `;
  });

  html += `
      </tbody>
    </table>
  `;

  historyArea.innerHTML = html;
}

async function loadProfile() {
  try {
    const res = await fetch(`${API_BASE}/me`, {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    if (res.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "index.html";
      return;
    }

    const data = await res.json();
    userInfo.textContent = `${data.username} (${data.email})`;
  } catch (error) {
    userInfo.textContent = "Profile load failed";
  }
}

optimizeForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  dashboardMessage.classList.add("hidden");

  try {
    const nodes = document.getElementById("nodes").value
      .split(",")
      .map(n => n.trim())
      .filter(Boolean);

    const payload = {
      nodes,
      source: document.getElementById("source").value.trim(),
      sink: document.getElementById("sink").value.trim(),
      total_demand: Number(document.getElementById("totalDemand").value),
      hours: Number(document.getElementById("hours").value),
      edges: parseEdges(document.getElementById("edgesInput").value)
    };

    const res = await fetch(`${API_BASE}/optimize`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok) {
      showDashboardMessage(data.detail || "Optimization failed", "error");
      return;
    }

    renderSummary(data);
    renderSchedule(data);
    showDashboardMessage("Optimization completed successfully", "success");
    loadHistory();
  } catch (error) {
    showDashboardMessage(error.message || "Failed to run optimization", "error");
  }
});

async function loadHistory() {
  try {
    const res = await fetch(`${API_BASE}/optimizations`, {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    const data = await res.json();

    if (!res.ok) {
      historyArea.innerHTML = `<p>${data.detail || "Failed to load history"}</p>`;
      return;
    }

    renderHistory(data);
  } catch (error) {
    historyArea.innerHTML = "<p>Cannot connect to backend.</p>";
  }
}

async function loadRunById(runId) {
  try {
    const res = await fetch(`${API_BASE}/optimizations/${runId}`, {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    const data = await res.json();

    if (!res.ok) {
      showDashboardMessage(data.detail || "Failed to load run", "error");
      return;
    }

    renderSummary(data);
    renderSchedule(data);
    showDashboardMessage(`Loaded optimization run ${runId}`, "success");
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (error) {
    showDashboardMessage("Cannot connect to backend", "error");
  }
}

window.loadRunById = loadRunById;

loadHistoryBtn.addEventListener("click", loadHistory);

logoutBtn.addEventListener("click", () => {
  localStorage.removeItem("token");
  window.location.href = "index.html";
});

loadProfile();
loadHistory();