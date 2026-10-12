(function (root) {
  const MAX_SHARE_CHARS = 80000;
  const MAX_SHARE_MESSAGES = 80;

  function b64urlFromBytes(bytes) {
    let binary = "";
    bytes.forEach((value) => {
      binary += String.fromCharCode(value);
    });
    return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
  }

  function bytesFromB64url(token) {
    const padded = token + "=".repeat((4 - (token.length % 4)) % 4);
    const binary = atob(padded.replaceAll("-", "+").replaceAll("_", "/"));
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    return bytes;
  }

  async function deflateRaw(bytes) {
    if (typeof CompressionStream === "undefined") {
      throw new Error("This browser cannot build a share link.");
    }
    const stream = new Blob([bytes]).stream().pipeThrough(new CompressionStream("deflate-raw"));
    return new Uint8Array(await new Response(stream).arrayBuffer());
  }

  async function inflateRaw(bytes) {
    if (typeof DecompressionStream === "undefined") {
      throw new Error("This browser cannot open a share link.");
    }
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
    return new Uint8Array(await new Response(stream).arrayBuffer());
  }

  function sliceTranscript(messages, upto) {
    if (!Array.isArray(messages) || upto < 0 || upto >= messages.length) {
      throw new Error("share index is out of range");
    }
    return messages.slice(0, upto + 1).map((item) => {
      const role = item && item.role;
      if (role !== "user" && role !== "assistant") {
        throw new Error("share message role is invalid");
      }
      const row = { role: role, content: item.content == null ? "" : String(item.content) };
      if (Array.isArray(item.plots)) {
        const plots = [];
        item.plots.forEach((plot) => {
          if (!plot || typeof plot.src !== "string") return;
          if (!/^https?:\/\//i.test(plot.src)) return;
          const entry = { src: plot.src };
          if (typeof plot.tool === "string" && plot.tool) entry.tool = plot.tool;
          plots.push(entry);
        });
        if (plots.length) row.plots = plots;
      }
      return row;
    });
  }

  function totalChars(messages) {
    return messages.reduce((sum, item) => sum + String(item.content || "").length, 0);
  }

  async function encodeShare(messages, upto) {
    if (!Array.isArray(messages) || !messages.length) {
      throw new Error("nothing to share");
    }
    const end = upto == null ? messages.length - 1 : upto;
    const payload = sliceTranscript(messages, end);
    if (payload.length > MAX_SHARE_MESSAGES || totalChars(payload) > MAX_SHARE_CHARS) {
      throw new Error("shared chat is too long");
    }
    const raw = new TextEncoder().encode(JSON.stringify(payload));
    const compressed = await deflateRaw(raw);
    return b64urlFromBytes(compressed);
  }

  async function decodeShare(token) {
    if (!token || typeof token !== "string") {
      throw new Error("share link is empty");
    }
    let raw;
    try {
      raw = await inflateRaw(bytesFromB64url(token));
    } catch (error) {
      throw new Error("share link is not valid");
    }
    let data;
    try {
      data = JSON.parse(new TextDecoder().decode(raw));
    } catch (error) {
      throw new Error("share link is not valid");
    }
    if (!Array.isArray(data) || !data.length || data.length > MAX_SHARE_MESSAGES) {
      throw new Error("share link is not valid");
    }
    return sliceTranscript(data, data.length - 1);
  }

  function shareHash(token) {
    return "#s=" + token;
  }

  function parseShareHash(fragment) {
    if (!fragment) return null;
    const text = fragment.charAt(0) === "#" ? fragment.slice(1) : fragment;
    if (text.indexOf("s=") !== 0) return null;
    const token = text.slice(2);
    return token || null;
  }

  function buildShareUrl(token) {
    const origin = root.location && root.location.origin ? root.location.origin : "";
    return origin + "/chat" + shareHash(token);
  }

  const api = {
    MAX_SHARE_CHARS,
    MAX_SHARE_MESSAGES,
    sliceTranscript,
    encodeShare,
    decodeShare,
    shareHash,
    parseShareHash,
    buildShareUrl
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  root.AstraeusShare = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
