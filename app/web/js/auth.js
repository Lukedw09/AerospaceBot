(function () {
  const storage = window.sessionStorage;
  let config = null;

  function randomBytes() {
    const bytes = new Uint8Array(32);
    crypto.getRandomValues(bytes);
    return bytes;
  }

  function b64url(bytes) {
    let text = btoa(String.fromCharCode(...bytes));
    return text.replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
  }

  async function challenge(verifier) {
    const data = new TextEncoder().encode(verifier);
    const digest = await crypto.subtle.digest("SHA-256", data);
    return b64url(new Uint8Array(digest));
  }

  async function loadConfig() {
    if (config) return config;
    const response = await fetch("/account/public-config");
    if (!response.ok) {
      throw new Error("Could not load the plugin configuration.");
    }
    config = await response.json();
    return config;
  }

  async function startLogin(provider, linking) {
    const current = await loadConfig();
    const verifier = b64url(randomBytes());
    storage.setItem("verifier", verifier);
    storage.setItem("linking", linking ? "1" : "");
    const params = new URLSearchParams({
      client_id: current.client_id,
      response_type: "code",
      scope: current.scopes,
      redirect_uri: current.redirect_uri,
      code_challenge: await challenge(verifier),
      code_challenge_method: "S256",
      identity_provider: provider
    });
    window.location = current.hosted_ui.replace(/\/$/, "") + "/oauth2/authorize?" + params.toString();
  }

  async function exchange(code) {
    const current = await loadConfig();
    const body = new URLSearchParams({
      grant_type: "authorization_code",
      client_id: current.client_id,
      code: code,
      redirect_uri: current.redirect_uri,
      code_verifier: storage.getItem("verifier") || ""
    });
    const response = await fetch(current.hosted_ui.replace(/\/$/, "") + "/oauth2/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    return response.json();
  }

  async function api(path, method, payload) {
    const response = await fetch(path, {
      method: method,
      headers: {
        "Authorization": "Bearer " + storage.getItem("access"),
        "Content-Type": "application/json"
      },
      body: payload ? JSON.stringify(payload) : undefined
    });
    const text = await response.text();
    let data = {};
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (error) {
        throw new Error("The account service did not answer.");
      }
    }
    if (!response.ok) {
      const error = new Error(data.error || response.statusText);
      error.status = response.status;
      throw error;
    }
    return data;
  }

  function snippetText(current) {
    const snippet = {
      mcpServers: {
        aerospace: {
          url: current.mcp_url,
          auth: { CLIENT_ID: current.client_id, scopes: ["openid", "email", "profile"] }
        }
      }
    };
    return JSON.stringify(snippet, null, 2);
  }

  function hasSession() {
    return Boolean(storage.getItem("access"));
  }

  async function completeRedirect() {
    const params = new URLSearchParams(window.location.search);
    if (params.get("error")) {
      history.replaceState({}, "", "/");
      throw new Error(params.get("error_description") || params.get("error"));
    }
    if (!params.get("code")) return false;
    const tokens = await exchange(params.get("code"));
    history.replaceState({}, "", "/");
    if (storage.getItem("linking") === "1" && storage.getItem("access")) {
      storage.removeItem("linking");
      await api("/account/link", "POST", { id_token: tokens.id_token });
    } else {
      storage.setItem("access", tokens.access_token);
      storage.setItem("id", tokens.id_token);
    }
    window.location.replace("/profile.html");
    return true;
  }

  window.AstraeusAuth = {
    storage,
    loadConfig,
    startLogin,
    api,
    snippetText,
    hasSession,
    completeRedirect
  };
})();
