/* Electric-pump hydraulic, shaft, and drive power. */
var Lab = Lab || {};

Lab.pumpPower = function (mdot, rho, dp, eta, etaDrive) {
  var vdot = mdot / rho;
  var hyd = vdot * dp;
  var shaft = hyd / eta;
  return {
    vdot: vdot,
    hyd: hyd,
    shaft: shaft,
    drive: shaft / etaDrive,
    dp: dp
  };
};
