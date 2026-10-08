(function () {
  function showError(error) {
    const status = document.getElementById("status");
    if (!status) return;
    status.textContent = error && error.message ? error.message : String(error);
    status.classList.add("is-error");
  }

  function providerLabel(name) {
    if (name === "Facebook") return "Meta";
    return name || "login";
  }

  function ensureDialog() {
    if (document.getElementById("signin-dialog")) return;
    const dialog = document.createElement("div");
    dialog.id = "signin-dialog";
    dialog.className = "dialog";
    dialog.hidden = true;
    dialog.innerHTML =
      '<div class="dialog-card" role="dialog" aria-modal="true" aria-labelledby="signin-title">' +
      '<h2 id="signin-title">Sign in</h2>' +
      '<p>Sign in with Google or Meta. That login is the credential for the plugin.</p>' +
      '<div class="stack">' +
      '<button type="button" class="btn btn-primary" id="google">Sign in with Google</button>' +
      '<button type="button" class="btn btn-ghost" id="meta">Sign in with Meta</button>' +
      '<button type="button" class="btn btn-ghost" data-close-signin>Close</button>' +
      "</div></div>";
    document.body.appendChild(dialog);
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) closeSignIn();
    });
    dialog.querySelector("[data-close-signin]").addEventListener("click", closeSignIn);
    dialog.querySelector("#google").addEventListener("click", () => {
      AstraeusAuth.startLogin("Google", false).catch(showError);
    });
    dialog.querySelector("#meta").addEventListener("click", () => {
      AstraeusAuth.startLogin("Facebook", false).catch(showError);
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeSignIn();
    });
  }

  function openSignIn() {
    ensureDialog();
    const dialog = document.getElementById("signin-dialog");
    dialog.hidden = false;
    const google = document.getElementById("google");
    if (google) google.focus();
  }

  function closeSignIn() {
    const dialog = document.getElementById("signin-dialog");
    if (dialog) dialog.hidden = true;
  }

  function mountChrome() {
    const page = document.body.dataset.page || "";
    document.querySelectorAll(".nav-links a[data-page]").forEach((link) => {
      if (link.dataset.page === page) link.setAttribute("aria-current", "page");
    });
    const account = document.querySelector("[data-nav='account']");
    const signin = document.querySelector("[data-nav='signin']");
    const signedIn = AstraeusAuth.hasSession();
    if (account) account.hidden = !signedIn;
    if (signin) signin.hidden = signedIn;
    const toggle = document.querySelector(".nav-toggle");
    const nav = document.querySelector(".nav");
    if (toggle && nav) {
      toggle.addEventListener("click", () => {
        const open = nav.classList.toggle("is-open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
    }
    document.querySelectorAll("[data-open-signin]").forEach((button) => {
      button.addEventListener("click", openSignIn);
    });
  }

  async function fillSnippets() {
    const nodes = document.querySelectorAll("[data-snippet]");
    if (!nodes.length) return;
    try {
      const current = await AstraeusAuth.loadConfig();
      const text = AstraeusAuth.snippetText(current);
      nodes.forEach((node) => {
        node.textContent = text;
      });
    } catch (error) {
      nodes.forEach((node) => {
        node.textContent = "The install snippet is published with the live site at https://astraeus.de-wet.com/install.html.";
      });
    }
  }

  function bindCopy() {
    document.querySelectorAll("[data-copy]").forEach((button) => {
      button.addEventListener("click", async () => {
        const pre = button.parentElement.querySelector("pre");
        const text = pre ? pre.textContent : "";
        try {
          await navigator.clipboard.writeText(text);
          const previous = button.textContent;
          button.textContent = "Copied";
          window.setTimeout(() => {
            button.textContent = previous;
          }, 1600);
        } catch (error) {
          showError(error);
        }
      });
    });
  }

  async function loadAccount() {
    const account = await AstraeusAuth.api("/account", "GET");
    document.getElementById("who").textContent = account.email || account.sub;
    document.getElementById("plan").textContent = String(account.plan);
    const used = Number(account.used_today);
    const cap = Number(account.daily_cap);
    document.getElementById("usage").textContent = used + " of " + cap + " tool calls today.";
    const meter = document.getElementById("meter");
    const bar = document.getElementById("meter-bar");
    const pct = cap > 0 ? Math.min(100, (used / cap) * 100) : 0;
    bar.style.width = pct + "%";
    meter.setAttribute("aria-valuenow", String(used));
    meter.setAttribute("aria-valuemax", String(cap));
    const list = document.getElementById("linked");
    list.replaceChildren();
    const items = account.linked || [];
    if (!items.length) {
      const li = document.createElement("li");
      li.textContent = "No linked login yet.";
      list.appendChild(li);
    } else {
      for (const item of items) {
        const li = document.createElement("li");
        li.textContent = providerLabel(item.provider);
        list.appendChild(li);
      }
    }
    await fillSnippets();
  }

  function bindAccount() {
    const linkGoogle = document.getElementById("link-google");
    if (!linkGoogle) return;
    linkGoogle.addEventListener("click", () => {
      AstraeusAuth.startLogin("Google", true).catch(showError);
    });
    document.getElementById("link-meta").addEventListener("click", () => {
      AstraeusAuth.startLogin("Facebook", true).catch(showError);
    });
    document.getElementById("unlink-google").addEventListener("click", () => {
      AstraeusAuth.api("/account/unlink", "POST", { provider: "Google" }).then(loadAccount).catch(showError);
    });
    document.getElementById("unlink-meta").addEventListener("click", () => {
      AstraeusAuth.api("/account/unlink", "POST", { provider: "Facebook" }).then(loadAccount).catch(showError);
    });
    document.getElementById("local-out").addEventListener("click", () => {
      AstraeusAuth.storage.clear();
      window.location = "/";
    });
    document.getElementById("global-out").addEventListener("click", () => {
      AstraeusAuth.api("/account/signout", "POST").then((data) => {
        document.getElementById("note").textContent = data.message;
      }).catch(showError);
    });
    document.getElementById("delete").addEventListener("click", () => {
      if (!window.confirm("Delete this account and its pictures?")) return;
      AstraeusAuth.api("/account/delete", "POST").then(() => {
        AstraeusAuth.storage.clear();
        window.location = "/";
      }).catch(showError);
    });
  }

  function start() {
    mountChrome();
    bindCopy();
    fillSnippets();
    bindAccount();
  }

  window.AstraeusSite = { start, showError, openSignIn, loadAccount };
})();
