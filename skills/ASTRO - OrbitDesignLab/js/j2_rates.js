/* First-order J2 rates. Keep in step with ASTRO - J2SecularRates. */
var Lab = Lab || {};

Lab.j2Nodal = function (n, j2, re, inc, a, ecc) {
  return -3.0 * n * j2 * re * re * Math.cos(inc) / (2.0 * a * a * Math.pow(1.0 - ecc * ecc, 2));
};

Lab.j2Apsidal = function (n, j2, re, inc, a, ecc) {
  return 3.0 * n * j2 * re * re * (4.0 - 5.0 * Math.sin(inc) * Math.sin(inc))
    / (4.0 * a * a * Math.pow(1.0 - ecc * ecc, 2));
};

Lab.j2Rates = function (mu, a, ecc, inc, j2, re) {
  var n = Lab.meanMotion(mu, a);
  var node = Lab.j2Nodal(n, j2, re, inc, a, ecc);
  var apsis = Lab.j2Apsidal(n, j2, re, inc, a, ecc);
  var sun = 2.0 * Math.PI / (Lab.YEAR_DAYS * Lab.DAY_S);
  var cosine = -2.0 * sun * a * a * Math.pow(1.0 - ecc * ecc, 2) / (3.0 * n * j2 * re * re);
  var iSs = Math.abs(cosine) <= 1.0 ? Math.acos(cosine) : null;
  return {
    n: n,
    node: node,
    apsis: apsis,
    node_deg_day: node * (180.0 / Math.PI) * Lab.DAY_S,
    apsis_deg_day: apsis * (180.0 / Math.PI) * Lab.DAY_S,
    i_ss: iSs
  };
};
