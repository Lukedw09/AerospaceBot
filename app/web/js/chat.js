(function () {
  const STORAGE_KEY = "astraeus-chat";
  let transcript = [];
  let sending = false;

  function el(tag, className) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    return node;
  }

  function loadTranscript() {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      const data = raw ? JSON.parse(raw) : [];
      return Array.isArray(data) ? data : [];
    } catch (error) {
      return [];
    }
  }

  function saveTranscript() {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(transcript));
    } catch (error) {
      // A long plot can exceed the session limit. The thread still shows it.
    }
  }

  function showError(error) {
    const status = document.getElementById("status");
    if (!status) return;
    status.textContent = error && error.message ? error.message : String(error);
    status.classList.add("is-error");
  }

  function clearError() {
    const status = document.getElementById("status");
    if (!status) return;
    status.textContent = "";
    status.classList.remove("is-error");
  }

  function showRemaining(usage) {
    const node = document.getElementById("remaining");
    if (!node || !usage || typeof usage.remaining !== "number") return;
    const left = usage.remaining === 1 ? "1 call left today" : usage.remaining + " calls left today";
    node.textContent = left;
  }

  function showComposer() {
    document.getElementById("gate").hidden = true;
    document.getElementById("compose").hidden = false;
  }

  function showSignedOut() {
    document.getElementById("gate").hidden = false;
    document.getElementById("compose").hidden = true;
    document.getElementById("remaining").textContent = "";
  }

  function protectMath(text) {
    const blocks = [];
    const saved = String(text)
      .replace(/\$\$([\s\S]+?)\$\$/g, (_, tex) => {
        blocks.push({ display: true, tex: tex });
        return "ASTRAEUSMATH" + (blocks.length - 1) + "END";
      })
      .replace(/\\\(([\s\S]+?)\\\)/g, (_, tex) => {
        blocks.push({ display: false, tex: tex });
        return "ASTRAEUSMATH" + (blocks.length - 1) + "END";
      });
    return { saved: saved, blocks: blocks };
  }

  function renderMarkdown(text) {
    const node = el("div", "prose");
    if (!window.marked || !window.DOMPurify) {
      node.textContent = text;
      return node;
    }
    const packed = protectMath(text);
    const parsed = window.marked.parse(packed.saved, { gfm: true, breaks: true, headerIds: false, mangle: false });
    let html = window.DOMPurify.sanitize(parsed, { USE_PROFILES: { html: true } });
    html = html.replace(/ASTRAEUSMATH(\d+)END/g, (_, index) => {
      const block = packed.blocks[Number(index)];
      if (!block) return "";
      if (!window.katex) return block.tex;
      return window.katex.renderToString(block.tex, {
        displayMode: block.display,
        throwOnError: false
      });
    });
    node.innerHTML = html;
    return node;
  }

  function userBubble(text) {
    const p = el("p", "msg-user");
    p.textContent = text;
    return p;
  }

  function sourceList(sources) {
    const list = el("ul");
    if (!sources || !sources.length) {
      const item = el("li");
      item.textContent = "No sources listed.";
      list.appendChild(item);
      return list;
    }
    sources.forEach((source) => {
      const item = el("li");
      const label = source.document || source.id || "Source";
      if (source.href && /^https?:\/\//i.test(source.href)) {
        const link = document.createElement("a");
        link.href = source.href;
        link.rel = "noopener";
        link.textContent = label;
        item.appendChild(link);
      } else {
        item.textContent = label;
      }
      list.appendChild(item);
    });
    return list;
  }

  function detailsBlock(details) {
    const wrap = el("details", "chat-details");
    const summary = el("summary");
    summary.textContent = "Show details";
    wrap.appendChild(summary);
    (details || []).forEach((detail) => {
      const block = el("div", "chat-detail");
      const title = el("p", "who");
      title.textContent = detail.tool || "tool";
      const inputs = el("pre", "lines");
      inputs.textContent = JSON.stringify(detail.arguments || {}, null, 2);
      const output = el("pre", "lines");
      output.textContent = detail.output || "";
      block.append(title, inputs, output, sourceList(detail.sources));
      wrap.appendChild(block);
    });
    return wrap;
  }

  function plotsBlock(plots) {
    const wrap = el("div", "chat-plots");
    (plots || []).forEach((plot) => {
      if (!plot || typeof plot.src !== "string") return;
      if (!/^https?:\/\//i.test(plot.src) && !plot.src.startsWith("data:image/png;base64,")) return;
      const image = document.createElement("img");
      image.src = plot.src;
      image.alt = plot.tool ? "Plot from " + plot.tool : "Plot";
      wrap.appendChild(image);
    });
    return wrap;
  }

  function assistantBubble(item) {
    const wrap = el("div", "msg-bot");
    const avatar = el("div", "avatar");
    const img = document.createElement("img");
    img.src = "/assets/astraeus.png";
    img.alt = "";
    avatar.appendChild(img);
    const body = el("div", "msg-body");
    const who = el("p", "who");
    who.textContent = "Astraeus";
    body.append(who, renderMarkdown(item.content || ""));
    if (item.plots && item.plots.length) body.appendChild(plotsBlock(item.plots));
    if (item.details && item.details.length) body.appendChild(detailsBlock(item.details));
    wrap.append(avatar, body);
    return wrap;
  }

  function thinkingRow() {
    const row = el("div", "tool is-running");
    row.id = "thinking";
    const dot = el("span", "tool-dot");
    const label = el("span");
    label.textContent = "Thinking / running tools";
    row.append(dot, label);
    return row;
  }

  function paint() {
    const thread = document.getElementById("thread");
    if (!thread) return;
    thread.replaceChildren();
    transcript.forEach((item) => {
      if (item.role === "user") thread.appendChild(userBubble(item.content || ""));
      else thread.appendChild(assistantBubble(item));
    });
    thread.scrollTop = thread.scrollHeight;
  }

  function historyPayload() {
    return transcript.map((item) => ({ role: item.role, content: item.content || "" }));
  }

  async function send(event) {
    if (event) event.preventDefault();
    if (sending) return;
    const draft = document.getElementById("draft");
    const text = draft.value.trim();
    if (!text) return;
    clearError();
    transcript.push({ role: "user", content: text });
    draft.value = "";
    sending = true;
    draft.disabled = true;
    paint();
    document.getElementById("thread").appendChild(thinkingRow());
    try {
      const data = await AstraeusAuth.api("/api/chat", "POST", { messages: historyPayload() });
      transcript.push({
        role: "assistant",
        content: data.answer || "",
        plots: data.plots || [],
        details: data.details || []
      });
      saveTranscript();
      showRemaining(data.usage);
    } catch (error) {
      transcript.pop();
      draft.value = text;
      if (error.status === 401) {
        AstraeusAuth.storage.clear();
        const account = document.querySelector("[data-nav='account']");
        const signin = document.querySelector("[data-nav='signin']");
        if (account) account.hidden = true;
        if (signin) signin.hidden = false;
        showSignedOut();
      }
      showError(error);
    } finally {
      sending = false;
      draft.disabled = false;
      paint();
      if (!document.getElementById("compose").hidden) draft.focus();
    }
  }

  async function boot() {
    transcript = loadTranscript();
    paint();
    AstraeusSite.start();
    let status = null;
    try {
      status = await AstraeusAuth.api("/api/chat/status", "GET");
    } catch (error) {
      if (error.status === 401) {
        AstraeusAuth.storage.clear();
        const account = document.querySelector("[data-nav='account']");
        const signin = document.querySelector("[data-nav='signin']");
        if (account) account.hidden = true;
        if (signin) signin.hidden = false;
        showSignedOut();
        return;
      }
      showError(error);
      showSignedOut();
      return;
    }
    showRemaining(status);
    if (status.sign_in_required && !AstraeusAuth.hasSession()) {
      showSignedOut();
      return;
    }
    showComposer();
  }

  document.getElementById("compose").addEventListener("submit", send);
  document.getElementById("draft").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  });
  boot();
})();
