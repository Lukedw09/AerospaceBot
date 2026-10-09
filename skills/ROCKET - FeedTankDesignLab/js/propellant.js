/* Propellant split and loaded volume. Residuals stay in the tank. */
var Lab = Lab || {};

Lab.splitFlows = function (mode, mdot, ratio, mdotOx, mdotFuel) {
  if (mode === "ratio") {
    if (!(mdot > 0) || !(ratio > 0)) throw new Error("total mass flow and mixture ratio must be > 0");
    return {
      mdot: mdot,
      r: ratio,
      mdotOx: ratio * mdot / (ratio + 1),
      mdotFuel: mdot / (ratio + 1)
    };
  }
  if (!(mdotOx > 0) || !(mdotFuel > 0)) throw new Error("oxidizer and fuel mass flow must be > 0");
  return {
    mdot: mdotOx + mdotFuel,
    r: mdotOx / mdotFuel,
    mdotOx: mdotOx,
    mdotFuel: mdotFuel
  };
};

Lab.loadedVolume = function (mdot, burnTime, rho) {
  return mdot * burnTime / rho;
};
