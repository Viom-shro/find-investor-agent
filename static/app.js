const $ = (id) => document.getElementById(id);

const runBtn = $("runBtn");
const statusEl = $("status");
const resultsEl = $("results");
const tbody = $("table").querySelector("tbody");
const metaEl = $("meta");
const downloadLink = $("downloadLink");

function setStatus(msg, isError = false) {
  statusEl.textContent = msg;
  statusEl.style.color = isError ? "#ffb3b3" : "#9fb0c4";
}

function escapeHtml(s) {
  if (s === null || s === undefined) return "";
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderRecords(records) {
  tbody.innerHTML = "";
  for (const r of records) {
    const tr = document.createElement("tr");
    const stage =
      [r.investment_stage_min_usd, r.investment_stage_max_usd]
        .filter(Boolean)
        .join(" - ") || "";

    const location = [r.investor_location_city, r.investor_location_country]
      .filter(Boolean)
      .join(", ");

    tr.innerHTML = `
      <td>${escapeHtml(r.investor_name)}</td>
      <td>${escapeHtml(r.investor_type)}</td>
      <td>${escapeHtml(stage)}</td>
      <td>${escapeHtml(location)}</td>
      <td>${escapeHtml(r.focus_industries)}</td>
      <td><a href="${escapeHtml(r.source_url)}" target="_blank" rel="noreferrer">link</a></td>
    `;
    tbody.appendChild(tr);
  }
}

runBtn.addEventListener("click", async () => {
  const query = $("query").value.trim();
  if (!query) {
    setStatus("Please enter a query.", true);
    return;
  }

  runBtn.disabled = true;
  resultsEl.classList.add("hidden");
  downloadLink.classList.add("hidden");
  tbody.innerHTML = "";
  setStatus("Running agent... (this may take a while)");

  const maxResults = Number($("maxResults").value);
  const maxPagesRaw = $("maxPages").value.trim();
  const maxPages = maxPagesRaw ? Number(maxPagesRaw) : null;
  const provider = $("provider").value || null;

  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        max_results: maxResults,
        max_pages: maxPages,
        provider,
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Request failed");

    renderRecords(data.records || []);
    metaEl.textContent = `Records: ${data.records_count} (job_id: ${data.job_id})`;
    resultsEl.classList.remove("hidden");

    if (data.csv_url) {
      downloadLink.href = data.csv_url;
      downloadLink.classList.remove("hidden");
    }

    setStatus("Done.");
  } catch (err) {
    setStatus(String(err?.message || err), true);
  } finally {
    runBtn.disabled = false;
  }
});

