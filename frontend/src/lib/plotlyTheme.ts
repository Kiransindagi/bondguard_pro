/**
 * Shared Plotly + Recharts theme configuration.
 * Import this in every chart-bearing page to ensure visual consistency.
 */

// ─── Plotly ────────────────────────────────────────────────────────

export const PLOT_LAYOUT: Partial<any> = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { family: 'Inter, system-ui, sans-serif', color: '#8fa3bf', size: 11 },
  xaxis: {
    gridcolor: 'rgba(148,163,184,0.07)',
    linecolor: 'rgba(148,163,184,0.14)',
    tickfont: { size: 11, color: '#8fa3bf' },
    zeroline: false,
    showgrid: true,
  },
  yaxis: {
    gridcolor: 'rgba(148,163,184,0.07)',
    linecolor: 'rgba(148,163,184,0.14)',
    tickfont: { size: 11, color: '#8fa3bf' },
    zeroline: false,
    showgrid: true,
  },
  legend: {
    bgcolor: 'transparent',
    bordercolor: 'transparent',
    font: { size: 11, color: '#8fa3bf' },
  },
  margin: { t: 20, r: 20, b: 44, l: 64 },
  hoverlabel: {
    bgcolor: '#0f1a2e',
    bordercolor: 'rgba(148,163,184,0.22)',
    font: { color: '#dde4ef', size: 12, family: 'Inter, system-ui' },
  },
  colorway: ['#10b981', '#38bdf8', '#a78bfa', '#fbbf24', '#f87171', '#67e8f9'],
};

export const PLOT_CONFIG: Partial<any> = {
  displayModeBar: false,
  responsive: true,
};

/** Merge page-level overrides with the base theme */
export function plotLayout(overrides: Partial<any> = {}): Partial<any> {
  return {
    ...PLOT_LAYOUT,
    ...overrides,
    xaxis: { ...PLOT_LAYOUT.xaxis, ...(overrides.xaxis ?? {}) },
    yaxis: { ...PLOT_LAYOUT.yaxis, ...(overrides.yaxis ?? {}) },
  };
}

// ─── Recharts ──────────────────────────────────────────────────────

export const RC_GRID_PROPS = {
  strokeDasharray: '3 3',
  stroke: 'rgba(148,163,184,0.09)',
  vertical: false,
};

export const RC_AXIS_STYLE = {
  stroke: 'rgba(148,163,184,0.15)',
  tick: { fontSize: 11, fill: '#8fa3bf' },
};

export const RC_TOOLTIP_STYLE = {
  contentStyle: {
    backgroundColor: '#0f1a2e',
    border: '1px solid rgba(148,163,184,0.20)',
    borderRadius: '6px',
    fontSize: '12px',
    color: '#dde4ef',
  },
  labelStyle: { color: '#8fa3bf', fontSize: '11px', marginBottom: '4px' },
  cursor: { stroke: 'rgba(148,163,184,0.15)' },
};

export const RC_LEGEND_STYLE = {
  wrapperStyle: { fontSize: '11px', color: '#8fa3bf', paddingTop: '8px' },
};

// ─── Palette ───────────────────────────────────────────────────────

export const CHART_COLORS = {
  primary:  '#10b981',
  accent:   '#38bdf8',
  purple:   '#a78bfa',
  amber:    '#fbbf24',
  red:      '#f87171',
  cyan:     '#67e8f9',
  slate:    '#8fa3bf',
};
