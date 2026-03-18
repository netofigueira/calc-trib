'use strict';

// ─── Formatters ───────────────────────────────────────────────────────────────

const BRL = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0,
});
const PCT = (v) => `${v.toFixed(1)}%`;
const fmt = (v) => BRL.format(v);

// ─── Chart instance ───────────────────────────────────────────────────────────

let mainChartInstance = null;
let lastData = null;

function buildChartData(data, mode) {
  const labels = data.anos_pf.map((a) => `Ano ${a.ano}`);

  if (mode === 'patrimonio') {
    return {
      labels,
      datasets: [
        {
          label: 'Pessoa Física — Patrimônio Total',
          data: data.anos_pf.map((a) => a.patrimonio_acumulado),
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37,99,235,.1)',
          fill: true,
          tension: 0.3,
          pointRadius: 3,
        },
        {
          label: 'PJ/Holding — Patrimônio Total',
          data: data.anos_pj.map((a) => a.patrimonio_acumulado),
          borderColor: '#16a34a',
          backgroundColor: 'rgba(22,163,74,.1)',
          fill: true,
          tension: 0.3,
          pointRadius: 3,
        },
      ],
    };
  }

  // impostos acumulados
  const cumPF = [];
  const cumPJ = [];
  let accPF = 0;
  let accPJ = 0;
  data.anos_pf.forEach((a) => {
    accPF += a.impostos_ganhos + a.imposto_distribuicao;
    cumPF.push(accPF);
  });
  data.anos_pj.forEach((a) => {
    accPJ += a.impostos_ganhos + a.imposto_distribuicao;
    cumPJ.push(accPJ);
  });

  return {
    labels,
    datasets: [
      {
        label: 'Impostos PF',
        data: cumPF,
        borderColor: '#2563eb',
        backgroundColor: 'rgba(37,99,235,.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 3,
      },
      {
        label: 'Impostos PJ',
        data: cumPJ,
        borderColor: '#16a34a',
        backgroundColor: 'rgba(22,163,74,.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 3,
      },
    ],
  };
}

function renderChart(data, mode = 'patrimonio') {
  const ctx = document.getElementById('mainChart').getContext('2d');
  if (mainChartInstance) mainChartInstance.destroy();

  mainChartInstance = new Chart(ctx, {
    type: 'line',
    data: buildChartData(data, mode),
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'bottom',
          labels: { font: { size: 12 }, boxWidth: 14, padding: 16 },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => `  ${ctx.dataset.label}: ${BRL.format(ctx.raw)}`,
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 11 }, color: '#94a3b8', maxTicksLimit: 10 },
        },
        y: {
          grid: { color: '#f1f5f9' },
          ticks: {
            font: { size: 11 },
            color: '#94a3b8',
            callback: (v) => {
              if (v >= 1_000_000) return `R$ ${(v / 1_000_000).toFixed(1)}M`;
              if (v >= 1_000) return `R$ ${(v / 1_000).toFixed(0)}k`;
              return BRL.format(v);
            },
          },
        },
      },
    },
  });
}

// ─── Tables ───────────────────────────────────────────────────────────────────

function renderTable(anos, tbodyId, includeCustos) {
  const tbody = document.getElementById(tbodyId);
  tbody.innerHTML = '';
  anos.forEach((a) => {
    const tr = document.createElement('tr');
    if (includeCustos) {
      tr.innerHTML = `
        <td>${a.ano}</td>
        <td>${fmt(a.saldo_inicial)}</td>
        <td class="td-positive">${fmt(a.retorno_bruto)}</td>
        <td class="td-negative">${fmt(a.impostos_ganhos)}</td>
        <td class="td-negative">${fmt(a.custos_operacionais)}</td>
        <td>${fmt(a.distribuicao_bruta)}</td>
        <td class="td-negative">${fmt(a.imposto_distribuicao)}</td>
        <td class="td-positive">${fmt(a.reinvestido)}</td>
        <td>${fmt(a.saldo_final)}</td>
      `;
    } else {
      tr.innerHTML = `
        <td>${a.ano}</td>
        <td>${fmt(a.saldo_inicial)}</td>
        <td class="td-positive">${fmt(a.retorno_bruto)}</td>
        <td class="td-negative">${fmt(a.impostos_ganhos)}</td>
        <td>${fmt(a.distribuicao_bruta)}</td>
        <td class="td-negative">${fmt(a.imposto_distribuicao)}</td>
        <td class="td-positive">${fmt(a.reinvestido)}</td>
        <td>${fmt(a.saldo_final)}</td>
        <td class="td-positive">${fmt(a.patrimonio_acumulado)}</td>
      `;
    }
    tbody.appendChild(tr);
  });
}

// ─── Render Results ───────────────────────────────────────────────────────────

function renderResults(data) {
  lastData = data;

  // Verdict
  const winner = data.vencedor;
  const isPJ = winner.includes('PJ');
  const banner = document.getElementById('verdict-banner');
  banner.className = 'verdict-banner ' + (isPJ ? '' : 'pf');

  document.getElementById('verdict-icon').textContent = isPJ ? '🏛️' : '👤';
  document.getElementById('verdict-title').textContent =
    `${winner} é mais eficiente no horizonte informado`;

  const diff = Math.abs(data.diferenca_percentual);
  const absDiff = Math.abs(data.diferenca_absoluta);
  document.getElementById('verdict-sub').textContent =
    `Diferença de ${fmt(absDiff)} (${diff.toFixed(1)}%) no Valor Futuro Líquido.`;

  // Cards
  document.getElementById('card-vfl-pf').textContent = fmt(data.vfl_pf);
  document.getElementById('card-detail-pf').textContent =
    `Saldo: ${fmt(data.saldo_final_pf)} · Distrib.: ${fmt(data.total_distribuido_pf)}`;

  document.getElementById('card-label-pj').textContent = `VFL · ${data.nome_pj}`;
  document.getElementById('card-vfl-pj').textContent = fmt(data.vfl_pj);
  document.getElementById('card-detail-pj').textContent =
    `Saldo: ${fmt(data.saldo_final_pj)} · Distrib.: ${fmt(data.total_distribuido_pj)}`;

  document.getElementById('card-td-pf').textContent = PCT(data.tax_drag_pf);
  document.getElementById('card-td-pj').textContent = PCT(data.tax_drag_pj);

  // ITCMD
  renderItcmd(data);

  // Chart
  renderChart(data, 'patrimonio');

  // Tables
  renderTable(data.anos_pf, 'tbody-pf', false);
  renderTable(data.anos_pj, 'tbody-pj', true);

  // Show results
  document.getElementById('placeholder').classList.add('hidden');
  document.getElementById('results').classList.remove('hidden');

  // Scroll to results on mobile
  if (window.innerWidth < 800) {
    document.getElementById('panel-results').scrollIntoView({ behavior: 'smooth' });
  }
}

// ─── ITCMD Render ─────────────────────────────────────────────────────────────

function renderItcmd(data) {
  const d = data.itcmd;

  // Badge de vencedor na sucessão
  const badge = document.getElementById('itcmd-verdict-badge');
  const isPJSuc = d.vencedor_sucessao.includes('PJ');
  badge.textContent = `Sucessão: ${d.vencedor_sucessao}`;
  badge.className = 'itcmd-badge' + (isPJSuc ? '' : ' pf');

  // Coluna PF
  document.getElementById('itcmd-base-pf').textContent = fmt(d.base_pf);
  document.getElementById('itcmd-valor-pf').textContent = fmt(d.itcmd_pf);
  document.getElementById('itcmd-aliq-pf').textContent = PCT(d.aliquota_efetiva_pf);
  document.getElementById('itcmd-vfl-suc-pf').textContent = fmt(d.vfl_pos_sucessao_pf);

  // Coluna PJ
  document.getElementById('itcmd-col-title-pj').textContent = data.nome_pj;
  document.getElementById('itcmd-base-pj').textContent = fmt(d.base_pj);
  document.getElementById('itcmd-valor-pj').textContent = fmt(d.itcmd_pj);
  document.getElementById('itcmd-aliq-pj').textContent = PCT(d.aliquota_efetiva_pj);
  document.getElementById('itcmd-vfl-suc-pj').textContent = fmt(d.vfl_pos_sucessao_pj);

  // Economia
  const econEl = document.getElementById('itcmd-economia');
  econEl.textContent = fmt(Math.abs(d.economia));
  econEl.className = 'itcmd-economia-valor' + (d.economia < 0 ? ' negativo' : '');

  const pct = d.itcmd_pf > 0
    ? ((d.economia / d.itcmd_pf) * 100).toFixed(1)
    : '0.0';
  document.getElementById('itcmd-economia-sub').textContent = d.economia >= 0
    ? `A holding economiza ${pct}% de ITCMD vs PF`
    : `PF paga ${Math.abs(parseFloat(pct)).toFixed(1)}% menos ITCMD que a holding`;
}

// ─── Chart Tab Switch ─────────────────────────────────────────────────────────

function switchChart(btn) {
  document.querySelectorAll('.chart-card .tab-btn').forEach((b) => b.classList.remove('active'));
  btn.classList.add('active');
  if (lastData) renderChart(lastData, btn.dataset.mode);
}

// ─── Table Tab Switch ─────────────────────────────────────────────────────────

function switchTable(scenario, btn) {
  document.querySelectorAll('.table-card .tab-btn').forEach((b) => b.classList.remove('active'));
  btn.classList.add('active');

  const tablePF = document.getElementById('table-pf');
  const tablePJ = document.getElementById('table-pj');

  if (scenario === 'pf') {
    tablePF.classList.remove('hidden');
    tablePJ.classList.add('hidden');
  } else {
    tablePF.classList.add('hidden');
    tablePJ.classList.remove('hidden');
  }
}

// ─── Form Submission ──────────────────────────────────────────────────────────

document.getElementById('calc-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const btn = document.getElementById('btn-calcular');
  const btnText = document.getElementById('btn-text');
  const spinner = document.getElementById('btn-spinner');

  btn.disabled = true;
  btnText.textContent = 'Calculando…';
  spinner.classList.remove('hidden');

  try {
    const fd = new FormData(e.target);

    const payload = {
      capital_inicial: parseFloat(fd.get('capital_inicial')),
      rentabilidade_anual: parseFloat(fd.get('rentabilidade_anual')) / 100,
      horizonte_anos: parseInt(fd.get('horizonte_anos'), 10),
      ir_pf_rate: parseFloat(fd.get('ir_pf_rate')) / 100,
      ir_pj_rate: parseFloat(fd.get('ir_pj_rate')) / 100,
      overhead_anual: parseFloat(fd.get('overhead_anual')),
      taxa_distribuicao: parseFloat(fd.get('taxa_distribuicao')) / 100,
      usar_deferimento: fd.get('usar_deferimento') === 'on',
      taxa_dividendos: parseFloat(fd.get('taxa_dividendos')) / 100,
      itcmd_max_rate: parseFloat(fd.get('itcmd_max_rate')) / 100,
      desconto_quota_holding: parseFloat(fd.get('desconto_quota_holding')) / 100,
    };

    const res = await fetch('/api/calcular', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erro no servidor');
    }

    const data = await res.json();
    renderResults(data);
  } catch (err) {
    alert(`Erro ao calcular: ${err.message}`);
  } finally {
    btn.disabled = false;
    btnText.textContent = 'Calcular';
    spinner.classList.add('hidden');
  }
});
