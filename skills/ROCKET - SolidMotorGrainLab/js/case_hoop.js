/* Port of ROCKET - ChamberVolumeAndCaseHoopStress hoop and margin. */
var Lab = Lab || {};

Lab.THIN_WALL_LIMIT = 0.1;

Lab.hoopStress = function (pc, radius, thickness) {
  return pc * radius / thickness;
};

Lab.marginOfSafety = function (allowable, design) {
  return allowable / design - 1;
};

Lab.thinWall = function (radius, thickness) {
  return thickness / radius < Lab.THIN_WALL_LIMIT ? "yes" : "no";
};
