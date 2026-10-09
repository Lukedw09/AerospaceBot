/* Isentropic stagnation and sonic reference. Mirrors AERO - IsentropicStagnation. */
var Lab = Lab || {};

Lab.DEFAULT_R = 8.31432e3 / 28.9644;

Lab.stagnationTemperatureRatio = function (mach, gamma) {
  return 1 + 0.5 * (gamma - 1) * mach * mach;
};

Lab.stagnationPressureRatio = function (mach, gamma) {
  var tRatio = Lab.stagnationTemperatureRatio(mach, gamma);
  return Math.pow(tRatio, gamma / (gamma - 1));
};

Lab.stagnationDensityRatio = function (mach, gamma) {
  var tRatio = Lab.stagnationTemperatureRatio(mach, gamma);
  return Math.pow(tRatio, 1 / (gamma - 1));
};

Lab.stagnationSoundSpeedRatio = function (mach, gamma) {
  return Math.sqrt(Lab.stagnationTemperatureRatio(mach, gamma));
};

Lab.sonicTemperatureRatio = function (gamma) {
  return 2 / (gamma + 1);
};

Lab.sonicPressureRatio = function (gamma) {
  return Math.pow(2 / (gamma + 1), gamma / (gamma - 1));
};

Lab.sonicDensityRatio = function (gamma) {
  return Math.pow(2 / (gamma + 1), 1 / (gamma - 1));
};

Lab.stagnationState = function (mach, gamma, temperature, pressure, density) {
  if (!isFinite(mach) || mach < 0 || mach > 1e6) {
    throw new Error("Mach must satisfy 0 <= M <= 1e6");
  }
  if (!isFinite(gamma) || gamma <= 1) {
    throw new Error("gamma must be finite and > 1");
  }
  if (temperature != null && (!isFinite(temperature) || temperature <= 0)) {
    throw new Error("static temperature must be finite and > 0 K");
  }
  if (pressure != null && (!isFinite(pressure) || pressure <= 0)) {
    throw new Error("static pressure must be finite and > 0 Pa");
  }
  if (density != null && (!isFinite(density) || density <= 0)) {
    throw new Error("static density must be finite and > 0 kg/m^3");
  }
  var ttOverT = Lab.stagnationTemperatureRatio(mach, gamma);
  var ptOverP = Lab.stagnationPressureRatio(mach, gamma);
  var rhotOverRho = Lab.stagnationDensityRatio(mach, gamma);
  var atOverA = Lab.stagnationSoundSpeedRatio(mach, gamma);
  var tStarOverTt = Lab.sonicTemperatureRatio(gamma);
  var pStarOverPt = Lab.sonicPressureRatio(gamma);
  var rhoStarOverRhot = Lab.sonicDensityRatio(gamma);
  var gasConstant = null;
  var rSource = null;
  if (temperature != null && pressure != null && density != null) {
    gasConstant = pressure / (density * temperature);
    rSource = "equation_of_state";
  } else if (temperature != null) {
    gasConstant = Lab.DEFAULT_R;
    rSource = "default_air";
  }
  var a = null;
  var aSource = null;
  if (pressure != null && density != null) {
    a = Math.sqrt(gamma * pressure / density);
    aSource = "pressure_density";
  } else if (temperature != null && gasConstant != null) {
    a = Math.sqrt(gamma * gasConstant * temperature);
    aSource = "temperature";
  }
  return {
    M: mach,
    gamma: gamma,
    Tt_over_T: ttOverT,
    pt_over_p: ptOverP,
    rhot_over_rho: rhotOverRho,
    at_over_a: atOverA,
    Tstar_over_Tt: tStarOverTt,
    pstar_over_pt: pStarOverPt,
    rhostar_over_rhot: rhoStarOverRhot,
    Tt: temperature == null ? null : temperature * ttOverT,
    pt: pressure == null ? null : pressure * ptOverP,
    rhot: density == null ? null : density * rhotOverRho,
    T_star: temperature == null ? null : temperature * ttOverT * tStarOverTt,
    p_star: pressure == null ? null : pressure * ptOverP * pStarOverPt,
    rho_star: density == null ? null : density * rhotOverRho * rhoStarOverRhot,
    R: gasConstant,
    R_source: rSource,
    a: a,
    a_source: aSource,
    a_t: a == null ? null : a * atOverA
  };
};
