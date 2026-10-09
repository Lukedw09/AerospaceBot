/* Lifting-line slope, induced drag, and the cosine sweep factor on a0. */
var Lab = Lab || {};

Lab.wingSlope = function (a0, aspectRatio, efficiency) {
  return a0 / (1 + a0 / (Math.PI * aspectRatio * efficiency));
};

Lab.inducedDrag = function (cl, aspectRatio, efficiency) {
  return cl * cl / (Math.PI * aspectRatio * efficiency);
};

Lab.wingLift = function (slope, alpha, alphaL0) {
  return slope * (alpha - alphaL0);
};

Lab.stallAngle = function (alphaL0, clmax, slope) {
  return alphaL0 + clmax / slope;
};
