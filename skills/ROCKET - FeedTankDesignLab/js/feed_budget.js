/* Feed supply pressure. Ports feed_system_pressure_budget.py. */
var Lab = Lab || {};

Lab.G0 = 9.80665;

Lab.supplyPressure = function (pc, dpInjector, dpExtra, rho, height, g) {
  var manifold = pc + dpInjector;
  var head = rho * g * height;
  return {
    manifold: manifold,
    head: head,
    supply: manifold + dpExtra + head
  };
};
