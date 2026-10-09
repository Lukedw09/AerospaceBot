/* Port of ROCKET - ChamberVolumeAndCaseHoopStress chamber_case.py, plus a 30° convergent frustum. */
var Lab = Lab || {};

Lab.THIN_WALL_LIMIT = 0.1;
Lab.CONV_HALF = 30 * Math.PI / 180;
Lab.CHAMBER_FACTOR = 2.5;

Lab.chamberVolume = function (throat, lstar) {
  return lstar * throat;
};

Lab.hoopStress = function (pc, radius, thickness) {
  return pc * radius / thickness;
};

Lab.marginOfSafety = function (allowable, design) {
  return allowable / design - 1;
};

Lab.thinWall = function (radius, thickness) {
  return thickness / radius < Lab.THIN_WALL_LIMIT ? "yes" : "no";
};

Lab.chamberProfile = function (rc, rt, lstar, at) {
  if (!(rc > rt)) throw new Error("chamber radius must be greater than throat radius");
  var vc = Lab.chamberVolume(at, lstar);
  var lConv = (rc - rt) / Math.tan(Lab.CONV_HALF);
  var vConv = Math.PI / 3 * lConv * (rc * rc + rc * rt + rt * rt);
  var lCyl = 0;
  var volumeShort = false;
  if (vConv >= vc) volumeShort = true;
  else lCyl = (vc - vConv) / (Math.PI * rc * rc);
  return { Vc: vc, Lcyl: lCyl, Lconv: lConv, volumeShort: volumeShort };
};
