// ============ CLOCK ============
function tickClock() {
  const el = document.getElementById('clock');
  if (!el) return;
  const d = new Date();
  const hh = String(d.getUTCHours()).padStart(2, '0');
  const mm = String(d.getUTCMinutes()).padStart(2, '0');
  const ss = String(d.getUTCSeconds()).padStart(2, '0');
  el.textContent = `${hh}:${mm}:${ss} Z`;
}
tickClock();
setInterval(tickClock, 1000);

// ============ DASHBOARD DATA ============
async function fetchDashboardData() {
  try {
    const dataRes = await fetch('/api/latest-data');
    const data = await dataRes.json();

    const telemetryEl = document.getElementById('telemetry-data');

    if (data.status || data.error) {
      telemetryEl.innerHTML = `
        <p class="font-mono text-xs text-amber tracking-widest uppercase">Awaiting data ingestion…</p>
      `;
    } else {
      telemetryEl.innerHTML = `
        <div class="flex items-end justify-between border-b border-white/5 pb-3">
          <span class="font-mono text-[11px] text-muted tracking-[0.15em] uppercase">Traffic Volume</span>
          <span class="font-mono text-lg text-ghost">${data.plane_count}<span class="text-muted text-xs ml-1">ac</span></span>
        </div>
        <div class="flex items-end justify-between border-b border-white/5 pb-3">
          <span class="font-mono text-[11px] text-muted tracking-[0.15em] uppercase">Wind Speed</span>
          <span class="font-mono text-lg text-ghost">${data.wind_speed}<span class="text-muted text-xs ml-1">km/h</span></span>
        </div>
        <div class="flex items-end justify-between border-b border-white/5 pb-3">
          <span class="font-mono text-[11px] text-muted tracking-[0.15em] uppercase">Precipitation</span>
          <span class="font-mono text-lg text-ghost">${data.precipitation}<span class="text-muted text-xs ml-1">mm</span></span>
        </div>
        <div class="flex items-center justify-between pt-1">
          <span class="font-mono text-[10px] text-muted tracking-[0.15em] uppercase">Last Sync</span>
          <span class="font-mono text-[11px] text-signal/80">${data.timestamp}</span>
        </div>
      `;
    }

    const predRes = await fetch('/api/predict');
    const pred = await predRes.json();
    const predContainer = document.getElementById('prediction-result');

    if (pred.error) {
      predContainer.innerHTML = `<p class="font-mono text-sm text-amber">${pred.error}</p>`;
    } else {
      const isHigh = pred.risk_level === 'High';
      const textColor = isHigh ? 'text-amber' : 'text-phosphor';
      const barColor  = isHigh ? 'bg-amber' : 'bg-phosphor';
      const glow      = isHigh ? 'shadow-glowAmber' : 'shadow-glow';
      const prob = (pred.probability * 100).toFixed(1);

      predContainer.innerHTML = `
        <p class="font-mono text-[11px] text-muted tracking-[0.35em] uppercase mb-3">Disruption Risk</p>
        <h3 class="font-display text-5xl md:text-6xl font-bold ${textColor}">${pred.risk_level} Risk</h3>
        <p class="font-mono text-sm text-ghost/70 mt-3">${prob}% probability</p>
        <div class="w-44 h-1 rounded-full bg-white/10 mx-auto mt-4 overflow-hidden">
          <div class="h-full ${barColor} ${glow}" style="width:${prob}%"></div>
        </div>
      `;

      // sync the 3D radar's target blip color to the current risk level
      if (window.setRadarRisk) window.setRadarRisk(pred.risk_level);
    }
  } catch (error) {
    console.error('Error fetching data:', error);
    const telemetryEl = document.getElementById('telemetry-data');
    if (telemetryEl) {
      telemetryEl.innerHTML = `<p class="font-mono text-xs text-amber tracking-widest uppercase">Link error — retrying…</p>`;
    }
  }
}
fetchDashboardData();
setInterval(fetchDashboardData, 30000);