/* Injector orifice area from mdot = Cd * A * sqrt(2 * rho * dp). */
var Lab = Lab || {};

Lab.orificeArea = function (mdot, rho, cd, dp) {
  return mdot / (cd * Math.sqrt(2 * rho * dp));
};

Lab.orificeSolve = function (mdot, rho, cd, dp, count) {
  var area = Lab.orificeArea(mdot, rho, cd, dp);
  var speed = mdot / (rho * area);
  return {
    area: area,
    speed: speed,
    dp: dp,
    q: 0.5 * rho * speed * speed,
    diameter: Math.sqrt(4 * area / (count * Math.PI))
  };
};
