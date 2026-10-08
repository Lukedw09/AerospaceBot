(function () {
  // Numbers are frozen from real plugin runs. Do not round them.
  const SCENARIOS = [
    {
      tool: "ATMOS · standard_1976",
      ask: "What is the density of the atmosphere at 30 km?",
      prose: "At a geometric altitude of 30 km, the 1976 U.S. Standard Atmosphere prints:",
      lines: [
        "Z_m: 30000",
        "rho_kg_m3: 0.01841017",
        "T_K: 226.50908",
        "p_Pa: 1197.0316"
      ]
    },
    {
      tool: "ASTRO · hohmann_transfer",
      ask: "What is the delta-v for a Hohmann transfer from 400 km to 35,786 km?",
      prose: "The program used its default Earth radius and printed these impulsive burns:",
      lines: [
        "dv_depart_m_s: 2398.0514",
        "dv_arrive_m_s: 1456.6166",
        "dv_m_s: 3854.6681"
      ]
    },
    {
      tool: "AERO · normal_shock",
      ask: "What is the downstream Mach number after a Mach 2 normal shock?",
      prose: "For a calorically perfect normal shock at Mach 2, gamma 1.4:",
      lines: [
        "M2: 0.57735027",
        "p2_over_p1: 4.5",
        "T2_over_T1: 1.6875"
      ]
    },
    {
      tool: "ASTRO · orbital_parameters",
      ask: "What is the period of a 500 km circular Earth orbit?",
      prose: "For that circular orbit above the program's default Earth radius, the period is:",
      lines: [
        "a_m: 6874200",
        "period_s: 5673.1869",
        "vy_m_s: 7613.335"
      ]
    },
    {
      tool: "ROCKET · performance",
      ask: "What is the ideal specific impulse of LOX/RP-1 at 40 bar, mixture ratio 2.3, area ratio 40, in vacuum?",
      prose: "Frozen performance at the 40 bar table, exhausting to vacuum, prints:",
      lines: [
        "Isp_vac_s: 357.97699",
        "cstar_m_s: 1801.1223",
        "pc_table_bar: 40"
      ]
    },
    {
      tool: "AERO · naca_four_digit_section",
      ask: "What is the zero-lift angle of a NACA 2412 section with a 1 m chord?",
      prose: "NACA Report 824 for a smooth 2412 section at the digitized Reynolds number prints:",
      lines: [
        "alpha_L0_deg: -2",
        "alpha_L0_rad: -0.034906585",
        "Re: 5700000"
      ]
    }
  ];

  let runToken = 0;

  function el(tag, className) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    return node;
  }

  function userBubble(text) {
    const p = el("p", "msg-user");
    p.textContent = text;
    return p;
  }

  function toolRow(name, running) {
    const row = el("div", running ? "tool is-running" : "tool");
    const dot = el("span", "tool-dot");
    const label = el("span", "tool-label");
    label.textContent = running ? "Running " + name : name;
    row.append(dot, label);
    return row;
  }

  function assistant(prose, lines) {
    const wrap = el("div", "msg-bot");
    const avatar = el("div", "avatar");
    const img = document.createElement("img");
    img.src = "/assets/astraeus.png";
    img.alt = "";
    avatar.appendChild(img);
    const body = el("div", "msg-body");
    const who = el("p", "who");
    who.textContent = "Astraeus";
    const proseNode = el("p", "prose");
    proseNode.textContent = prose;
    const linesNode = el("div", "lines");
    lines.forEach((line) => {
      const row = el("div");
      row.textContent = line;
      linesNode.appendChild(row);
    });
    body.append(who, proseNode, linesNode);
    wrap.append(avatar, body);
    return wrap;
  }

  function paint(scenario) {
    const thread = document.getElementById("thread");
    if (!thread) return;
    thread.classList.remove("is-fading");
    thread.replaceChildren(
      userBubble(scenario.ask),
      toolRow(scenario.tool, false),
      assistant(scenario.prose, scenario.lines)
    );
  }

  function wait(ms, token) {
    return new Promise((resolve) => {
      let left = ms;
      const step = () => {
        if (token !== runToken) {
          resolve(false);
          return;
        }
        if (document.hidden) {
          window.setTimeout(step, 250);
          return;
        }
        if (left <= 0) {
          resolve(true);
          return;
        }
        const slice = Math.min(left, 80);
        left -= slice;
        window.setTimeout(step, slice);
      };
      step();
    });
  }

  async function typeInto(node, text, token, ms) {
    node.textContent = "";
    for (const ch of text) {
      node.textContent += ch;
      const thread = document.getElementById("thread");
      if (thread) thread.scrollTop = thread.scrollHeight;
      if (!(await wait(ms, token))) return false;
    }
    return true;
  }

  async function play(scenario, token) {
    const thread = document.getElementById("thread");
    thread.classList.add("is-fading");
    if (!(await wait(380, token))) return false;
    thread.replaceChildren();
    thread.classList.remove("is-fading");

    const user = el("p", "msg-user");
    thread.appendChild(user);
    if (!(await typeInto(user, scenario.ask, token, 36))) return false;
    if (!(await wait(700, token))) return false;

    const tool = toolRow(scenario.tool, true);
    thread.appendChild(tool);
    thread.scrollTop = thread.scrollHeight;
    if (!(await wait(1300, token))) return false;
    tool.classList.remove("is-running");
    tool.querySelector(".tool-label").textContent = scenario.tool;

    const wrap = el("div", "msg-bot");
    const avatar = el("div", "avatar");
    const img = document.createElement("img");
    img.src = "/assets/astraeus.png";
    img.alt = "";
    avatar.appendChild(img);
    const body = el("div", "msg-body");
    const who = el("p", "who");
    who.textContent = "Astraeus";
    const prose = el("p", "prose");
    const lines = el("div", "lines");
    lines.hidden = true;
    body.append(who, prose, lines);
    wrap.append(avatar, body);
    thread.appendChild(wrap);
    if (!(await typeInto(prose, scenario.prose, token, 14))) return false;
    lines.hidden = false;
    for (const line of scenario.lines) {
      if (!(await wait(240, token))) return false;
      const row = el("div");
      row.textContent = line;
      lines.appendChild(row);
      thread.scrollTop = thread.scrollHeight;
    }
    return wait(2200, token);
  }

  function start() {
    const thread = document.getElementById("thread");
    if (!thread) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      paint(SCENARIOS[0]);
      return;
    }
    const token = ++runToken;
    (async () => {
      let index = 0;
      while (token === runToken) {
        const started = performance.now();
        const ok = await play(SCENARIOS[index], token);
        if (!ok) return;
        const elapsed = performance.now() - started;
        if (elapsed < 12000 && !(await wait(12000 - elapsed, token))) return;
        index = (index + 1) % SCENARIOS.length;
      }
    })();
  }

  window.AstraeusDemo = { start };
})();
