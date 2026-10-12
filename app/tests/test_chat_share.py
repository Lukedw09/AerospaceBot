"""Chat share payload: encode, decode, slice rules, and JS interop."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from app.catalog import repo_root_from
from app.chat_share import (
    MAX_SHARE_CHARS,
    MAX_SHARE_MESSAGES,
    decode_share,
    encode_share,
    parse_share_hash,
    share_hash,
    slice_transcript,
)

ROOT = repo_root_from()
SHARE_JS = ROOT / "app" / "web" / "js" / "share.js"


SAMPLE = [
    {"role": "user", "content": "Hohmann from 200 km to 35786 km"},
    {
        "role": "assistant",
        "content": "delta-v total is 3.9 km/s",
        "plots": [
            {"src": "https://astraeus.de-wet.com/results/abc", "tool": "hohmann"},
            {"src": "data:image/png;base64,AAAA"},
        ],
        "details": [{"tool": "hohmann_transfer", "arguments": {"r1_km": 6578}, "output": "ok"}],
    },
    {"role": "user", "content": "and the period?"},
    {"role": "assistant", "content": "GEO period is about 23.93 h"},
]


class ChatShareTests(unittest.TestCase):
    def test_slice_keeps_http_plots_drops_data_and_details(self) -> None:
        sliced = slice_transcript(SAMPLE, 1)
        self.assertEqual(len(sliced), 2)
        self.assertEqual(sliced[0]["role"], "user")
        self.assertEqual(sliced[1]["content"], "delta-v total is 3.9 km/s")
        self.assertEqual(sliced[1]["plots"], [{"src": "https://astraeus.de-wet.com/results/abc", "tool": "hohmann"}])
        self.assertNotIn("details", sliced[1])

    def test_slice_upto_stops_mid_thread(self) -> None:
        sliced = slice_transcript(SAMPLE, 1)
        self.assertEqual([item["role"] for item in sliced], ["user", "assistant"])

    def test_round_trip(self) -> None:
        token = encode_share(SAMPLE, 3)
        restored = decode_share(token)
        self.assertEqual(restored[0]["content"], SAMPLE[0]["content"])
        self.assertEqual(restored[1]["plots"][0]["src"], "https://astraeus.de-wet.com/results/abc")
        self.assertEqual(restored[3]["content"], SAMPLE[3]["content"])
        self.assertTrue(token)
        self.assertNotIn("=", token)
        self.assertNotIn("+", token)
        self.assertNotIn("/", token)

    def test_share_hash_parse(self) -> None:
        token = encode_share(SAMPLE, 1)
        self.assertEqual(parse_share_hash(share_hash(token)), token)
        self.assertEqual(parse_share_hash("s=" + token), token)
        self.assertIsNone(parse_share_hash(""))
        self.assertIsNone(parse_share_hash("#other=1"))

    def test_rejects_bad_index_and_role(self) -> None:
        with self.assertRaises(ValueError):
            encode_share(SAMPLE, 99)
        with self.assertRaises(ValueError):
            slice_transcript([{"role": "system", "content": "no"}], 0)
        with self.assertRaises(ValueError):
            encode_share([])

    def test_rejects_corrupt_token(self) -> None:
        with self.assertRaises(ValueError):
            decode_share("")
        with self.assertRaises(ValueError):
            decode_share("not-a-valid-token!!!")
        with self.assertRaises(ValueError):
            decode_share("AAAA")

    def test_rejects_oversized_message_count(self) -> None:
        huge = [{"role": "user" if i % 2 == 0 else "assistant", "content": "x"} for i in range(MAX_SHARE_MESSAGES + 1)]
        with self.assertRaises(ValueError):
            encode_share(huge)

    def test_rejects_oversized_content(self) -> None:
        big = [{"role": "user", "content": "a" * (MAX_SHARE_CHARS + 1)}, {"role": "assistant", "content": "ok"}]
        with self.assertRaises(ValueError):
            encode_share(big, 1)

    def test_python_token_opens_in_node(self) -> None:
        if not shutil.which("node"):
            self.skipTest("node is not installed")
        token = encode_share(SAMPLE, 1)
        script = f"""
const fs = require("fs");
const vm = require("vm");
const path = {json.dumps(str(SHARE_JS))};
const code = fs.readFileSync(path, "utf8");
const sandbox = {{
  module: {{ exports: {{}} }},
  exports: {{}},
  atob: (value) => Buffer.from(value, "base64").toString("binary"),
  btoa: (value) => Buffer.from(value, "binary").toString("base64"),
  TextEncoder,
  TextDecoder,
  Blob,
  Response,
  CompressionStream,
  DecompressionStream,
  globalThis: {{}},
}};
sandbox.globalThis = sandbox;
sandbox.module.exports = sandbox.exports;
vm.runInNewContext(code, sandbox);
const share = sandbox.module.exports;
(async () => {{
  const messages = await share.decodeShare({json.dumps(token)});
  if (messages.length !== 2) throw new Error("length " + messages.length);
  if (messages[1].content !== "delta-v total is 3.9 km/s") throw new Error("content");
  if (!messages[1].plots || messages[1].plots.length !== 1) throw new Error("plots");
  const again = await share.encodeShare(messages, 1);
  const back = await share.decodeShare(again);
  if (back[0].content !== messages[0].content) throw new Error("round trip");
  const hash = share.shareHash(again);
  if (share.parseShareHash(hash) !== again) throw new Error("hash");
  console.log("ok");
}})().catch((error) => {{
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
}});
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "share_check.mjs"
            # Use .cjs so require works; script uses require.
            path = Path(tmp) / "share_check.cjs"
            path.write_text(script, encoding="utf-8")
            completed = subprocess.run(
                ["node", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertIn("ok", completed.stdout)

    def test_node_token_opens_in_python(self) -> None:
        if not shutil.which("node"):
            self.skipTest("node is not installed")
        script = f"""
const fs = require("fs");
const vm = require("vm");
const path = {json.dumps(str(SHARE_JS))};
const code = fs.readFileSync(path, "utf8");
const sandbox = {{
  module: {{ exports: {{}} }},
  exports: {{}},
  atob: (value) => Buffer.from(value, "base64").toString("binary"),
  btoa: (value) => Buffer.from(value, "binary").toString("base64"),
  TextEncoder,
  TextDecoder,
  Blob,
  Response,
  CompressionStream,
  DecompressionStream,
  globalThis: {{}},
}};
sandbox.globalThis = sandbox;
sandbox.module.exports = sandbox.exports;
vm.runInNewContext(code, sandbox);
const share = sandbox.module.exports;
const sample = {json.dumps(SAMPLE)};
(async () => {{
  const token = await share.encodeShare(sample, 3);
  process.stdout.write(token);
}})().catch((error) => {{
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
}});
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "share_encode.cjs"
            path.write_text(script, encoding="utf-8")
            completed = subprocess.run(
                ["node", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        restored = decode_share(completed.stdout.strip())
        self.assertEqual(len(restored), 4)
        self.assertEqual(restored[3]["content"], "GEO period is about 23.93 h")
        self.assertEqual(len(restored[1]["plots"]), 1)

    def test_auth_safe_return_path_in_source(self) -> None:
        auth = (ROOT / "app" / "web" / "js" / "auth.js").read_text(encoding="utf-8")
        self.assertIn("function safeReturnPath", auth)
        self.assertIn("function clearSession", auth)
        self.assertIn('storage.setItem("return_to"', auth)
        self.assertIn("clearSession()", (ROOT / "app" / "web" / "js" / "chat.js").read_text(encoding="utf-8"))

    def test_chat_page_wires_share_assets(self) -> None:
        html = (ROOT / "app" / "web" / "chat.html").read_text(encoding="utf-8")
        self.assertIn("/js/share.js", html)
        self.assertIn('id="share-note"', html)
        chat_js = (ROOT / "app" / "web" / "js" / "chat.js").read_text(encoding="utf-8")
        self.assertIn("Share", chat_js)
        self.assertIn("absorbShareLink", chat_js)
        self.assertIn('addEventListener("hashchange"', chat_js)
        self.assertIn("Sign in to keep chatting", chat_js)
        self.assertIn("clearSession()", chat_js)
        self.assertIn("EXAMPLE_PROMPTS", chat_js)
        self.assertIn("chat-suggestions", chat_js)
        self.assertIn("Try asking", chat_js)


if __name__ == "__main__":
    unittest.main()
