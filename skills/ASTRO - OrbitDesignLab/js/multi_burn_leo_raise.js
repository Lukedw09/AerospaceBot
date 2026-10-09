/* Impulsive LEO-raise budget from MultiBurnLeoRaise.hohmann_impulsive
   plus PlaneChangeImpulse at the slower circular radius.
   Gravity loss stays on the finite-thrust one-shot; this tab reports 0. */
var Lab = Lab || {};

Lab.leoRaise = function (mu, r1, r2, di) {
  var hohmann = Lab.hohmann(mu, r1, r2);
  var slower = Math.sqrt(mu / Math.max(r1, r2));
  var dvPlane = Math.abs(di) < 1e-15 ? 0.0 : Lab.planeChangeImpulse(slower, di);
  var dv = hohmann.dv + dvPlane;
  return {
    dv_hohmann: hohmann.dv,
    dv_plane: dvPlane,
    dv_gravity_loss: 0.0,
    dv_steered: dv,
    dv_total: dv,
    note: "impulsive Hohmann plus plane-change impulse; not the finite-thrust gravity-loss integral"
  };
};
