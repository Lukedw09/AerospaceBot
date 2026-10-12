(function () {
  const STORAGE_KEY = "astraeus-chat";
  const SHARED_FLAG = "astraeus-chat-shared";
  const PENDING_KEY = "astraeus-chat-pending";
  // Same starter asks as the homepage demo — one per basic skill.
  const EXAMPLE_PROMPTS = [
    "What is the density of the atmosphere at 30 km?",
    "What is the delta-v for a Hohmann transfer from 400 km to 35,786 km?",
    "What is the downstream Mach number after a Mach 2 normal shock?",
    "What is the period of a 500 km circular Earth orbit?",
    "What is the ideal specific impulse of LOX/RP-1 at 40 bar, mixture ratio 2.3, area ratio 40, in vacuum?",
    "What is the zero-lift angle of a NACA 2412 section with a 1 m chord?"
  ];
  let transcript = [];
  let sending = false;
  let openedFromShare = false;
  const suggestedPrompts = pickExamples(3);

  function el(tag, className) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    return node;
  }

  function pickExamples(count) {
    const pool = EXAMPLE_PROMPTS.slice();
    for (let i = pool.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      const tmp = pool[i];
      pool[i] = pool[j];
      pool[j] = tmp;
    }
    return pool.slice(0, Math.min(count, pool.length));
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

  function updateGateCopy() {
    const button = document.querySelector("#gate [data-open-signin]");
    const note = document.getElementById("share-note");
    const gate = document.getElementById("gate");
    const signedOut = gate && !gate.hidden;
    const hasThread = transcript.length > 0;
    if (button) {
      button.textContent = hasThread ? "Sign in to keep chatting" : "Sign in to chat";
    }
    if (note) {
      const show = signedOut && openedFromShare && hasThread;
      note.hidden = !show;
      if (show) {
        note.textContent = "Someone shared this chat with you. Sign in with your own account to keep chatting.";
      }
    }
  }

  function showComposer() {
    document.getElementById("gate").hidden = true;
    document.getElementById("compose").hidden = false;
    restorePendingPrompt();
    updateGateCopy();
  }

  function showSignedOut() {
    document.getElementById("gate").hidden = false;
    document.getElementById("compose").hidden = true;
    document.getElementById("remaining").textContent = "";
    updateGateCopy();
  }

  function protectMath(text) {
    const blocks = [];
    const hold = (display, tex) => {
      blocks.push({ display: display, tex: tex });
      return "ASTRAEUSMATH" + (blocks.length - 1) + "END";
    };
    const saved = String(text)
      .replace(/\$\$([\s\S]+?)\$\$/g, (_, tex) => hold(true, tex))
      .replace(/\\\[([\s\S]+?)\\\]/g, (_, tex) => hold(true, tex))
      .replace(/\\\(([\s\S]+?)\\\)/g, (_, tex) => hold(false, tex));
    return { saved: saved, blocks: blocks };
  }

  function fillMath(node, text) {
    const packed = protectMath(text);
    if (!packed.blocks.length || !window.katex) {
      node.textContent = text;
      return;
    }
    packed.saved.split(/(ASTRAEUSMATH\d+END)/).forEach((part) => {
      const match = part.match(/^ASTRAEUSMATH(\d+)END$/);
      if (!match) {
        if (part) node.appendChild(document.createTextNode(part));
        return;
      }
      const block = packed.blocks[Number(match[1])];
      const span = document.createElement("span");
      if (!block) return;
      try {
        span.innerHTML = window.katex.renderToString(block.tex, {
          displayMode: block.display,
          throwOnError: false
        });
      } catch (error) {
        span.textContent = block.tex;
      }
      node.appendChild(span);
    });
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

  function shortenMath(text, limit) {
    const packed = protectMath(String(text || "").replace(/\s+/g, " ").trim());
    let saved = packed.saved;
    const sentence = saved.indexOf(". ");
    if (sentence > 40 && sentence < 220) saved = saved.slice(0, sentence + 1);
    else if (saved.length > limit) {
      let cut = saved.slice(0, limit - 1);
      const open = cut.lastIndexOf("ASTRAEUSMATH");
      const close = cut.lastIndexOf("END");
      if (open !== -1 && open > close) cut = cut.slice(0, open);
      saved = cut.replace(/\s+$/, "") + "…";
    }
    return restoreMath(saved, packed.blocks);
  }

  function restoreMath(saved, blocks) {
    return saved.replace(/ASTRAEUSMATH(\d+)END/g, (_, index) => {
      const block = blocks[Number(index)];
      if (!block) return "";
      return (block.display ? "\\[" : "\\(") + block.tex + (block.display ? "\\]" : "\\)");
    });
  }

  function sourceTitle(source) {
    const id = source.id ? source.id + ". " : "";
    const document = shortenMath(source.document || "", 180);
    return id + (document || "Source");
  }

  function sourceList(sources) {
    const list = el("ul", "chat-sources");
    if (!sources || !sources.length) {
      const item = el("li");
      item.textContent = "No source in sources.md names this tool.";
      list.appendChild(item);
      return list;
    }
    sources.forEach((source) => {
      const item = el("li");
      const label = sourceTitle(source);
      if (source.href && /^https?:\/\//i.test(source.href)) {
        const link = document.createElement("a");
        link.href = source.href;
        link.rel = "noopener";
        link.target = "_blank";
        fillMath(link, label);
        item.appendChild(link);
      } else {
        fillMath(item, label);
      }
      list.appendChild(item);
    });
    return list;
  }

  function pairList(rows) {
    const list = el("dl", "chat-kv");
    rows.forEach((row) => {
      const term = el("dt");
      term.textContent = row.key || "note";
      const value = el("dd");
      fillMath(value, row.value);
      list.append(term, value);
    });
    return list;
  }

  function clause(text) {
    const trimmed = text.trim();
    if (!trimmed) return "";
    const word = trimmed.split(/[\s,]/, 1)[0];
    const sentenceWord = /^(?:a|an|the|[a-z]{4,}(?:-[a-z]+)*)$/.test(word);
    if (!sentenceWord) return trimmed;
    return trimmed.charAt(0).toUpperCase() + trimmed.slice(1);
  }

  function splitOutput(text) {
    const results = [];
    let assumptions = [];
    String(text || "").split(/\r?\n/).forEach((line) => {
      const match = line.match(/^([A-Za-z][A-Za-z0-9_]*):\s*(.*)$/);
      if (!match) {
        if (line.trim()) results.push({ key: "", value: line.trim() });
        return;
      }
      const key = match[1];
      const value = match[2].trim();
      if (key === "assumptions") {
        const packed = protectMath(value);
        assumptions = packed.saved
          .split(";")
          .map((part) => clause(restoreMath(part, packed.blocks)))
          .filter(Boolean);
        return;
      }
      if (key === "graph" || key === "viewer" || key === "coefficients_graph" || key === "polar_graph") return;
      results.push({ key: key, value: value });
    });
    return { results: results, assumptions: assumptions };
  }

  function assumptionsBlock(items) {
    const wrap = el("details", "chat-assumptions");
    const summary = el("summary");
    summary.textContent = "Assumptions (" + items.length + ")";
    const list = el("ul");
    items.forEach((item) => {
      const line = el("li");
      fillMath(line, item);
      list.appendChild(line);
    });
    wrap.append(summary, list);
    return wrap;
  }

  function sectionLabel(text) {
    const label = el("p", "chat-kicker");
    label.textContent = text;
    return label;
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
      block.appendChild(title);
      const inputs = Object.entries(detail.arguments || {}).map(([key, value]) => {
        const raw = typeof value === "string" ? value : JSON.stringify(value);
        return { key: key, value: raw == null ? "" : raw };
      });
      block.appendChild(sectionLabel("Inputs"));
      if (inputs.length) block.appendChild(pairList(inputs));
      else {
        const empty = el("p", "chat-empty");
        empty.textContent = "None recorded.";
        block.appendChild(empty);
      }
      const parsed = splitOutput(detail.output || "");
      block.appendChild(sectionLabel("Results"));
      if (parsed.results.length) block.appendChild(pairList(parsed.results));
      else {
        const empty = el("p", "chat-empty");
        empty.textContent = "No printed results.";
        block.appendChild(empty);
      }
      if (parsed.assumptions.length) block.appendChild(assumptionsBlock(parsed.assumptions));
      block.appendChild(sectionLabel("Sources"));
      block.appendChild(sourceList(detail.sources));
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

  async function shareTurn(index, button) {
    if (!window.AstraeusShare) {
      showError(new Error("Share is not available."));
      return;
    }
    clearError();
    const previous = button.textContent;
    button.disabled = true;
    try {
      const token = await AstraeusShare.encodeShare(transcript, index);
      const url = AstraeusShare.buildShareUrl(token);
      if (navigator.share) {
        try {
          await navigator.share({ title: "Astraeus chat", url: url });
          button.textContent = "Shared";
          window.setTimeout(() => {
            button.textContent = previous;
            button.disabled = false;
          }, 1600);
          return;
        } catch (error) {
          if (error && error.name === "AbortError") {
            button.disabled = false;
            return;
          }
        }
      }
      await navigator.clipboard.writeText(url);
      button.textContent = "Link copied";
      window.setTimeout(() => {
        button.textContent = previous;
        button.disabled = false;
      }, 1600);
    } catch (error) {
      button.disabled = false;
      button.textContent = previous;
      showError(error);
    }
  }

  function historyThrough(index) {
    return transcript.slice(0, index + 1).map((item) => ({
      role: item.role,
      content: item.content || ""
    }));
  }

  function rememberVote(index, value) {
    transcript[index].feedback = value;
    saveTranscript();
    paint();
    if (value === "down-open") {
      const box = document.querySelector(".msg-reason textarea");
      if (box) box.focus();
    }
  }

  async function submitDown(index, reason, button) {
    const text = reason.trim();
    if (!text) {
      showError(new Error("Say why."));
      return;
    }
    clearError();
    button.disabled = true;
    try {
      await AstraeusAuth.api("/api/chat/feedback", "POST", {
        reason: text,
        history: historyThrough(index)
      });
      transcript[index].feedback = "down";
      saveTranscript();
      paint();
    } catch (error) {
      button.disabled = false;
      showError(error);
    }
  }

  function voteControls(item, index) {
    const votes = el("span", "msg-votes");
    if (item.feedback === "down") {
      const thanks = el("span", "msg-thanks");
      thanks.textContent = "Thanks";
      votes.appendChild(thanks);
      return votes;
    }
    const up = el("button", "msg-vote");
    up.type = "button";
    up.textContent = "Thumbs up";
    up.setAttribute("aria-label", "Thumbs up");
    up.setAttribute("aria-pressed", item.feedback === "up" ? "true" : "false");
    if (item.feedback === "up") up.classList.add("is-on");
    up.addEventListener("click", () => {
      rememberVote(index, item.feedback === "up" ? "" : "up");
    });
    const down = el("button", "msg-vote");
    down.type = "button";
    down.textContent = "Thumbs down";
    down.setAttribute("aria-label", "Thumbs down");
    down.setAttribute("aria-pressed", item.feedback === "down-open" ? "true" : "false");
    if (item.feedback === "down-open") down.classList.add("is-on");
    down.addEventListener("click", () => {
      rememberVote(index, item.feedback === "down-open" ? "" : "down-open");
    });
    votes.append(up, down);
    return votes;
  }

  function reasonForm(index) {
    const form = el("form", "msg-reason");
    const box = document.createElement("textarea");
    box.rows = 2;
    box.placeholder = "What was wrong?";
    box.setAttribute("aria-label", "Why thumbs down");
    const send = el("button", "msg-share");
    send.type = "submit";
    send.textContent = "Send";
    form.append(box, send);
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      submitDown(index, box.value, send);
    });
    return form;
  }

  function assistantBubble(item, index) {
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
    const actions = el("div", "msg-actions");
    const share = el("button", "msg-share");
    share.type = "button";
    share.textContent = "Share";
    share.setAttribute("aria-label", "Share this chat");
    share.addEventListener("click", () => {
      shareTurn(index, share);
    });
    actions.append(share, voteControls(item, index));
    if (item.feedback === "down-open") actions.appendChild(reasonForm(index));
    body.appendChild(actions);
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

  function useExample(text) {
    const compose = document.getElementById("compose");
    const draft = document.getElementById("draft");
    if (!compose || !draft) return;
    if (compose.hidden) {
      try {
        sessionStorage.setItem(PENDING_KEY, text);
      } catch (error) {
        // Ignore storage failures; sign-in still proceeds.
      }
      const signin = document.querySelector("[data-open-signin]");
      if (signin) signin.click();
      return;
    }
    draft.value = text;
    send();
  }

  function restorePendingPrompt() {
    const draft = document.getElementById("draft");
    if (!draft) return;
    try {
      const pending = sessionStorage.getItem(PENDING_KEY);
      if (!pending) return;
      sessionStorage.removeItem(PENDING_KEY);
      draft.value = pending;
    } catch (error) {
      // Ignore storage failures.
    }
  }

  function suggestionsBlock() {
    const wrap = el("div", "chat-suggestions");
    const label = el("p", "chat-suggestions-label");
    label.textContent = "Try asking";
    const list = el("div", "chat-suggestions-list");
    suggestedPrompts.forEach((text) => {
      const button = el("button", "chat-suggestion");
      button.type = "button";
      button.textContent = text;
      button.addEventListener("click", () => {
        useExample(text);
      });
      list.appendChild(button);
    });
    wrap.append(label, list);
    return wrap;
  }

  function paint() {
    const thread = document.getElementById("thread");
    if (!thread) return;
    thread.replaceChildren();
    if (!transcript.length) {
      thread.appendChild(suggestionsBlock());
      return;
    }
    transcript.forEach((item, index) => {
      if (item.role === "user") thread.appendChild(userBubble(item.content || ""));
      else thread.appendChild(assistantBubble(item, index));
    });
    thread.scrollTop = thread.scrollHeight;
  }

  function historyPayload() {
    return transcript.map((item) => ({ role: item.role, content: item.content || "" }));
  }

  async function absorbShareLink() {
    if (!window.AstraeusShare) return false;
    const token = AstraeusShare.parseShareHash(window.location.hash || "");
    if (!token) {
      openedFromShare = sessionStorage.getItem(SHARED_FLAG) === "1";
      return false;
    }
    try {
      transcript = await AstraeusShare.decodeShare(token);
      saveTranscript();
      sessionStorage.setItem(SHARED_FLAG, "1");
      openedFromShare = true;
      history.replaceState({}, "", "/chat");
      return true;
    } catch (error) {
      showError(error);
      history.replaceState({}, "", "/chat");
      return false;
    }
  }

  async function onShareHash() {
    const loaded = await absorbShareLink();
    if (!loaded) return;
    paint();
    if (document.getElementById("compose").hidden) {
      showSignedOut();
    } else {
      updateGateCopy();
    }
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
    openedFromShare = false;
    sessionStorage.removeItem(SHARED_FLAG);
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
        AstraeusAuth.clearSession();
        const account = document.querySelector("[data-nav='account']");
        const admin = document.querySelector("[data-nav='admin']");
        const signin = document.querySelector("[data-nav='signin']");
        if (account) account.hidden = true;
        if (admin) admin.hidden = true;
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
    const fromShare = await absorbShareLink();
    if (!fromShare) transcript = loadTranscript();
    paint();
    updateGateCopy();
    AstraeusSite.start();
    let status = null;
    try {
      status = await AstraeusAuth.api("/api/chat/status", "GET");
    } catch (error) {
      if (error.status === 401) {
        AstraeusAuth.clearSession();
        const account = document.querySelector("[data-nav='account']");
        const admin = document.querySelector("[data-nav='admin']");
        const signin = document.querySelector("[data-nav='signin']");
        if (account) account.hidden = true;
        if (admin) admin.hidden = true;
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
  window.addEventListener("hashchange", () => {
    onShareHash().catch(showError);
  });
  boot();
})();
