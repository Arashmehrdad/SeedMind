"use strict";

async function loadSnapshot() {
  const response = await fetch("/api/snapshot");
  if (!response.ok) {
    throw new Error(`Snapshot request failed with ${response.status}`);
  }
  return response.json();
}

function metricCard(metric) {
  return `
    <article class="metric-card">
      <p class="metric-label">${metric.label}</p>
      <p class="metric-value">${metric.value}</p>
      <p class="metric-note">${metric.note}</p>
    </article>
  `;
}

function sectionCard(section) {
  const bullets = section.bullets.map((item) => `<li>${item}</li>`).join("");
  const refs = section.evidence_refs.map((item) => `<code>${item}</code>`).join(" ");
  return `
    <article class="section-card">
      <h2>${section.title}</h2>
      <p>${section.summary}</p>
      <ul>${bullets}</ul>
      <p class="evidence">Evidence: ${refs}</p>
    </article>
  `;
}

function claimRow(claim) {
  return `
    <article class="claim-row ${claim.status}">
      <div>
        <p class="claim-id">${claim.claim_id}</p>
        <h3>${claim.statement}</h3>
      </div>
      <p class="claim-status">${claim.status}</p>
      <p>${claim.observed}</p>
      <p class="threshold">${claim.threshold}</p>
    </article>
  `;
}

function render(snapshot) {
  document.title = snapshot.title;
  document.getElementById("scope-notice").textContent = snapshot.scope_notice;
  document.getElementById("metrics").innerHTML = snapshot.metrics.map(metricCard).join("");
  document.getElementById("sections").innerHTML = snapshot.sections.map(sectionCard).join("");
  document.getElementById("claims").innerHTML = `
    <h2>Week 13 Claim Status</h2>
    ${snapshot.claims.map(claimRow).join("")}
  `;
  document.getElementById("limitations").innerHTML = snapshot.limitations
    .map((item) => `<li>${item}</li>`)
    .join("");
}

loadSnapshot().then(render).catch((error) => {
  document.getElementById("scope-notice").textContent = error.message;
});
