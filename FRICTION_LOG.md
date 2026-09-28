# Friction Log — ViewingGuardian + Lingo

Documented during the hackathon submission window. Each entry follows the
required format: task attempted, steps taken, expected vs. actual result,
severity rating, workaround used, and actionable suggestion.

---

## Entry 1 — Configure OAuth 2.1 discovery

**Task attempted:** Register an OAuth 2.1 authorization server for the MCP server.

**Steps taken:** Added `/.well-known/oauth-authorization-server` returning metadata with `S256` in `code_challenge_methods_supported`.

**Expected:** Alexa+ discovers the auth server and completes account linking.

**Actual:** 401 loop; discovery failed; account linking never completed.

**Severity:** Critical.

**Workaround:** Removed the `WWW-Authenticate` header on 401 responses — an undocumented Alexa+ requirement.

**Suggestion:** Document the "no WWW-Authenticate header on 401" rule in the MCP toolkit quickstart.

---

## Entry 2 — Meet the 500ms latency budget

**Task attempted:** Return a scene analysis verdict in under 500ms.

**Steps taken:** Called Bedrock live inside `analyze_scene_for_child`.

**Expected:** Sub-500ms response.

**Actual:** ~1.8s cold-start on the Bedrock call.

**Severity:** Critical.

**Workaround:** Pre-fetched and cached all demo scene verdicts keyed by scene ID. Live Bedrock only fires on unflagged scenes.

**Suggestion:** Publish a latency budget guide plus a caching example in the MCP toolkit docs.

---

## Entry 3 — Install the Alexa MCP Toolkit CLI

**Task attempted:** Install `@alexa-ai/cli` to generate the MCP add-on.

**Steps taken:** `npm install -g @alexa-ai/cli`

**Expected:** Package installs from the public npm registry.

**Actual:** E404 — package is only available behind a private preview gate.

**Severity:** Critical.

**Workaround:** Fell back to a traditional Custom Skill with an ASK-to-MCP shim at `/alexa`.

**Suggestion:** Replace the npm install instruction on the toolkit landing page with a clear "Request Preview Access" CTA.

---

## Entry 4 — Configure OAuth scopes in the Developer Console

**Task attempted:** Enter OAuth scopes for account linking.

**Steps taken:** Typed `playback:read playback:control profile:read profile:write`.

**Expected:** Console accepts the scopes.

**Actual:** Error — "String does not match regular expression `^[\w:]*$`."

**Severity:** High.

**Workaround:** Switched to comma-separated scopes with no spaces.

**Suggestion:** Update the error message to say "use comma-separated values without spaces" instead of only showing the regex.

---

## Entry 5 — Control Fire TV playback from the MCP server

**Task attempted:** Skip forward 12 seconds on Fire TV playback.

**Steps taken:** Wanted to call a native Fire TV playback API.

**Expected:** A direct playback control API.

**Actual:** No native API exists. Had to route through Home Assistant's `media_player.media_next_track`.

**Severity:** High.

**Workaround:** Home Assistant Fire TV integration (coarse skip, not precise seek).

**Suggestion:** Provide an official Fire TV playback control SDK.

---

## Entry 6 — Test the skill in the Alexa Developer Console simulator

**Task attempted:** Exercise the skill end-to-end from the official simulator.

**Steps taken:** Configured endpoint, account linking, and interaction model. Typed `ask view guardian is this okay for mia`.

**Expected:** Simulator sends the request to the MCP server and renders the response.

**Actual:** Simulator sends ASK-format requests; MCP server expects MCP JSON-RPC. Protocol mismatch.

**Severity:** Medium.

**Workaround:** Built an ASK-to-MCP shim at `/alexa` that translates ASK `IntentRequest` into internal guardian tool calls.

**Suggestion:** Document the shim pattern, or provide a native ASK-to-MCP bridge in the toolkit.

---

## Entry 7 — Find a scene metadata schema

**Task attempted:** Author scene metadata for the demo film.

**Steps taken:** Searched for a canonical MCP scene metadata schema.

**Expected:** A recommended schema.

**Actual:** None exists.

**Severity:** Medium.

**Workaround:** Invented a custom JSON schema (`server/data/whispering_woods_metadata.json`).

**Suggestion:** Publish a recommended scene metadata schema for media-related MCP servers.

---

## Entry 8 — Cloudflare quick tunnel URL rotation

**Task attempted:** Keep a stable public HTTPS endpoint during development.

**Steps taken:** Started `cloudflared tunnel --url http://localhost:8000`.

**Expected:** Stable URL for the session.

**Actual:** Every restart of `cloudflared` generated a new random URL, requiring an `.env` update, a server restart, and a Developer Console endpoint change.

**Severity:** Medium.

**Workaround:** Kept the tunnel terminal open and disabled laptop sleep.

**Suggestion:** Document the URL rotation behavior clearly and recommend ngrok or a named Cloudflare tunnel for longer sessions.
