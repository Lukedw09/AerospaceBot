var Lab = Lab || {};

Lab.budgetInert = function (mp, stage) {
  if (!stage.budget) return null;
  if (!(mp > 0)) throw new Error("each stage needs mp > 0");
  var residuals = stage.residuals || 0;
  if (residuals < 0) throw new Error("residuals must be >= 0");
  if (stage.law === "linear") {
    var k = stage.k;
    var hardware = stage.mH || 0;
    if (k < 0 || hardware < 0) throw new Error("mH and k must be >= 0");
    return hardware + k * mp + residuals;
  }
  function get(name) {
    var value = stage[name] || 0;
    if (value < 0) throw new Error(name + " must be >= 0");
    return value;
  }
  var engineMass = get("engineMass");
  var count = stage.engineCount;
  if (count === undefined || count === null) count = 1;
  if (!isFinite(count) || count < 0) throw new Error("engine-count must be >= 0");
  var engines = engineMass * count;
  return get("tank") + engines + get("fairing") + get("interstage") + get("other") + get("mH") + residuals;
};
