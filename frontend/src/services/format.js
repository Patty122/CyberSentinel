export const fmtInt = (n) => (n == null ? "-" : Number(n).toLocaleString("en-US"));
export const fmt = (n, d = 4) => (n == null || Number.isNaN(n) ? "-" : Number(n).toFixed(d));
export const pct = (n, d = 2) => (n == null ? "-" : `${Number(n).toFixed(d)}%`);
export const ratioPct = (n, d = 1) => (n == null ? "-" : `${(n * 100).toFixed(d)}%`);
