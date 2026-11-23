  // ------------------------------------------------------------------ estadistica
  function erfc(x) {
    const z = Math.abs(x);
    const t = 1 / (1 + 0.5 * z);
    const r = t * Math.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (0.37409196 + t * (0.09678418 + t * (-0.18628806 + t * (0.27886807 + t * (-1.13520398 + t * (1.48851587 + t * (-0.82215223 + t * 0.17087277)))))))));
    return x >= 0 ? r : 2 - r;
  }
  const cdfNormal = (x) => 0.5 * erfc(-x / Math.SQRT2);
  function ppfNormal(p) {
    const a = [-3.969683028665376e1, 2.209460984245205e2, -2.759285104469687e2, 1.38357751867269e2, -3.066479806614716e1, 2.506628277459239];
    const b = [-5.447609879822406e1, 1.615858368580409e2, -1.556989798598866e2, 6.680131188771972e1, -1.328068155288572e1];
    const c = [-7.784894002430293e-3, -3.223964580411365e-1, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783];
    const d = [7.784695709041462e-3, 3.224671290700398e-1, 2.445134137142996, 3.754408661907416];
    const bajo = 0.02425;
    if (p < bajo) {
      const q = Math.sqrt(-2 * Math.log(p));
      return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    }
    if (p > 1 - bajo) {
      const q = Math.sqrt(-2 * Math.log(1 - p));
      return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    }
    const q = p - 0.5;
    const r = q * q;
    return ((((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q) / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  function tamanoMuestra(p0, delta, potencia = 0.8, alfa = 0.05) {
    const p1 = p0 + delta;
    if (!(p0 > 0 && p0 < 1 && p1 > 0 && p1 < 1) || delta === 0) throw new Error("p0 y p0 + delta deben estar entre 0 y 1 y delta no puede ser 0");
    const media = (p0 + p1) / 2;
    const za = ppfNormal(1 - alfa / 2);
    const zb = ppfNormal(potencia);
    const num = (za * Math.sqrt(2 * media * (1 - media)) + zb * Math.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) ** 2;
    return Math.ceil(num / delta ** 2);
  }
  function potenciaAnalitica(p0, delta, n, alfa = 0.05) {
    const p1 = p0 + delta;
    const media = (p0 + p1) / 2;
    const za = ppfNormal(1 - alfa / 2);
    return cdfNormal((Math.abs(delta) * Math.sqrt(n) - za * Math.sqrt(2 * media * (1 - media))) / Math.sqrt(p0 * (1 - p0) + p1 * (1 - p1)));
  }
  function percentil(valores, q) {
    const orden = valores.slice().sort((a, b) => a - b);
    const pos = (q / 100) * (orden.length - 1);
    const i = Math.floor(pos);
    return orden[i] + (orden[Math.min(i + 1, orden.length - 1)] - orden[i]) * (pos - i);
  }
  function generador(semilla) {
    let a = semilla >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

