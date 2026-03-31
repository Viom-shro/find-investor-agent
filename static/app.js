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

function renderDebug(debug) {
  if (!debug) return "";
  const parts = [
    `provider: ${debug.provider_used ?? ""}`,
    `serp results: ${debug.search_results_count ?? 0}`,
    `pages considered: ${debug.pages_considered ?? 0}`,
    `fetched ok: ${debug.pages_fetched_ok ?? 0}`,
    `empty text: ${debug.pages_empty_text ?? 0}`,
    `fetch failed: ${debug.pages_fetch_failed ?? 0}`,
    `extract ok: ${debug.pages_extraction_ok ?? 0}`,
    `extract failed: ${debug.pages_extraction_failed ?? 0}`,
  ];
  return parts.filter(Boolean).join(" | ");
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
    const dbg = renderDebug(data.debug);
    metaEl.textContent = `Records: ${data.records_count} (job_id: ${data.job_id})${dbg ? " — " + dbg : ""}`;
    resultsEl.classList.remove("hidden");

    if (data.csv_url) {
      downloadLink.href = data.csv_url;
      downloadLink.classList.remove("hidden");
    }

    if ((data.records_count || 0) === 0) {
      setStatus("Done, but 0 records found. Try increasing Max search results, changing the query wording, or switching provider.", true);
    } else {
      setStatus("Done.");
    }
  } catch (err) {
    setStatus(String(err?.message || err), true);
  } finally {
    runBtn.disabled = false;
  }
});

runBtn.addEventListener("click", async () => {
  // ADD THESE LINES TEMPORARILY
  console.log("maxResults el:", $("maxResults"));
  console.log("maxPages el:", $("maxPages"));
  console.log("provider el:", $("provider"));
  console.log("query el:", $("query"));
});