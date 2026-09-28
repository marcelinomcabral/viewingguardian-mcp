# ViewingGuardian + Lingo

AI Guardian and Language Layer for Fire TV, built as a self-hosted MCP server for Alexa+.

---

## Table of Contents

1. [What it is](#what-it-is)
2. [Architecture](#architecture)
3. [Code entry points](#code-entry-points)
4. [Prerequisites](#prerequisites)
5. [Setup](#setup)
6. [Environment variables](#environment-variables)
7. [Running the MCP server](#running-the-mcp-server)
8. [Exposing the server publicly](#exposing-the-server-publicly)
9. [Testing the server](#testing-the-server)
10. [Alexa Developer Console setup](#alexa-developer-console-setup)
11. [Running the demo](#running-the-demo)
12. [Troubleshooting](#troubleshooting)
13. [What we built during the hackathon](#what-we-built-during-the-hackathon)
14. [Tracks and mini challenges](#tracks-and-mini-challenges)
15. [AWS services used](#aws-services-used)
16. [Friction Log](./FRICTION_LOG.md)
17. [License](#license)

---

## What it is

ViewingGuardian + Lingo is an Alexa+ MCP server that gives Fire TV real-time, scene-level awareness of what is playing and who is watching. It does two things existing parental controls and language settings cannot:

**Guardian interventions** - Analyzes scenes against a child profile (age, sensitivities, household rules) and intervenes before harmful content hits: skipping jump scares, softening peril, replacing profanity, pausing intense moments.

**Language transformation** - Translates subtitles in real time, dubs scenes while preserving the original actor voice, and replaces specific dialogue with family-friendly alternatives - without leaving playback.

Every other Alexa+ Fire TV project answers questions. This one acts on live content.

---

## Architecture

One self-hosted MCP server (spec 2025-11-25, Streamable HTTP) exposes two tool namespaces, with Alexa+ as the MCP client.

```
+-----------------------------------------------------------+
|               ALEXA+ (MCP Client)                          |
|   NLU, orchestration, UI rendering                         |
+-------------------------+---------------------------------+
                          |  Streamable HTTP (POST /mcp)
                          |  Authorization: Bearer TOKEN
                          v
+-----------------------------------------------------------+
|          VIEWINGGUARDIAN + LINGO MCP SERVER                |
|                                                            |
|   +---------------------+   +--------------------------+   |
|   |  Guardian Tools     |   |  Lingo Tools             |   |
|   |  - get_current_ctx  |   |  - translate_subtitles   |   |
|   |  - analyze_scene    |   |  - dub_scene             |   |
|   |  - skip_scene       |   |  - replace_dialogue      |   |
|   |  - get_child_profile|   |  - get_lingo_status      |   |
|   |  - log_decision     |   |                          |   |
|   |  - set_boundary     |   |                          |   |
|   +---------------------+   +--------------------------+   |
|                                                            |
|   State Layer: scene metadata (JSON), child profiles,      |
|   intervention log                                         |
+-------------------------+---------------------------------+
                          |  Internal control channel
                          v
+-----------------------------------------------------------+
|              FIRE TV RUNTIME (Renderer)                    |
|   Playback control | Subtitle overlay | Audio stem switch  |
|   Guardian alert overlay                                   |
+-----------------------------------------------------------+

```
**Design decision:** The MCP server is stateless per request but backed by a persistent state store. Alexa+ may call tools in any order, so the server reconstructs context from the session ID plus playback timestamp.

---

## Code entry points

Reviewers can find the required integrations here:

| Integration | File |
|---|---|
| FastMCP server (spec 2025-11-25) | server/main.py |
| Amazon Bedrock (scene analysis) | server/analysis.py |
| ElevenLabs (voice-preserving dubbing) | server/lingo.py |
| OAuth 2.1 + PKCE S256 | server/auth.py, server/well_known.py |
| ASK-to-MCP shim (Developer Console) | server/ask_shim.py |
| Guardian tools | server/tools/guardian.py |
| Lingo tools | server/tools/lingo.py |
| Scene metadata | server/data/whispering_woods_metadata.json |
| Child profiles | server/data/profiles.json |

---

## Prerequisites

Required:

- Python 3.11 or higher - https://www.python.org/downloads/
- uv (Python package manager) - https://docs.astral.sh/uv/
- Cloudflare Tunnel (cloudflared) - https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
- An Amazon Developer account for the Alexa Developer Console

Optional (enhances the demo):

- AWS account with Bedrock access (Claude 3 Sonnet enabled)
- ElevenLabs API key for real voice-preserving dubbing
- Home Assistant with the Fire TV integration for real playback control

The demo runs without AWS, ElevenLabs, or Home Assistant credentials. Scene metadata drives rule-based verdicts, and dubbing returns pre-rendered demo URLs. Real credentials unlock the live LLM and TTS paths.

### Windows 11 - one-time prerequisites install

```
winget install Python.Python.3.12
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
winget install --id Cloudflare.cloudflared

```
Close and reopen PowerShell so PATH updates take effect. Verify:

```
python --version
uv --version
cloudflared --version

```
---

## Setup

### Step 1 - Clone or create the project

If you have the repo:

```
git clone REPO_URL viewingguardian-mcp
cd viewingguardian-mcp

```
If starting from scratch:

```
mkdir viewingguardian-mcp
cd viewingguardian-mcp

New-Item -ItemType Directory -Path "server","server\tools","server\data","tests","demo","demo\audio_stems","deploy" -Force

New-Item -ItemType File -Path "pyproject.toml",".env.example","README.md","LICENSE" -Force
New-Item -ItemType File -Path "server\__init__.py","server\main.py","server\auth.py","server\well_known.py","server\models.py","server\state.py","server\analysis.py","server\lingo.py","server\firetv.py","server\ask_shim.py" -Force
New-Item -ItemType File -Path "server\tools\__init__.py","server\tools\guardian.py","server\tools\lingo.py" -Force
New-Item -ItemType File -Path "server\data\profiles.json","server\data\whispering_woods_metadata.json" -Force
New-Item -ItemType File -Path "tests\__init__.py","tests\test_tools.py","tests\test_auth.py","tests\test_latency.py" -Force
New-Item -ItemType File -Path "deploy\Dockerfile" -Force

```
### Step 2 - Install Python dependencies

From inside the project folder:

```
uv sync

```
This reads pyproject.toml, creates a .venv folder, and installs FastMCP, Uvicorn, boto3, httpx, and all other dependencies.

If you see "warning: No requires-python value found", verify that pyproject.toml contains:

```
requires-python = ">=3.11"

```
### Step 3 - Create your .env file

```
Copy-Item .env.example .env
code .env

```
Fill in the required values (see Environment variables below). At minimum, set OAUTH_JWT_SECRET to a random string and OAUTH_CLIENT_ID to any identifier. AWS and ElevenLabs keys are optional for the demo.

### Step 4 - Add the LICENSE file

```
Invoke-WebRequest -Uri "https://www.apache.org/licenses/LICENSE-2.0.txt" -OutFile "LICENSE"

```
### Step 5 - Verify the setup

```
uv run python -c "import fastmcp, boto3, httpx; print('Dependencies OK')"

```
If this prints Dependencies OK, the environment is ready.

---

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| OAUTH_ISSUER | Yes | Public HTTPS URL of your tunnel |
| OAUTH_JWT_SECRET | Yes | Random string used to sign JWTs (64+ characters) |
| OAUTH_CLIENT_ID | Yes | OAuth client identifier (e.g. viewingguardian-client) |
| AWS_ACCESS_KEY_ID | No | Bedrock access - falls back to rule-based verdicts if absent |
| AWS_SECRET_ACCESS_KEY | No | Bedrock access |
| AWS_REGION | No | Defaults to us-east-1 |
| BEDROCK_MODEL_ID | No | Defaults to anthropic.claude-3-sonnet-20240229-v1:0 |
| ELEVENLABS_API_KEY | No | Voice-preserving dubbing - falls back to demo URLs |
| HA_URL | No | Home Assistant URL for Fire TV bridge |
| HA_TOKEN | No | Home Assistant long-lived access token |
| SERVER_HOST | No | Defaults to 0.0.0.0 |
| SERVER_PORT | No | Defaults to 8000 |

Generate a strong JWT secret with:

```
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})

```
Copy the output into .env as OAUTH_JWT_SECRET.

---

## Running the MCP server

Open a PowerShell window, navigate to the project folder, and start the server:

```
cd C:\Users\YOUR-USER\viewingguardian-mcp
uv run python -m server.main

```
You should see:

```
INFO:     Started server process [xxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)

```
Leave this terminal running. The server must stay up for the entire session.

### Verify the server is responding

In a new PowerShell window:

```
curl.exe http://localhost:8000/.well-known/oauth-authorization-server

```
Expected JSON includes:

```
"code_challenge_methods_supported": ["S256"]

```
If you see this, the server is live and the OAuth discovery layer works.

---

## Exposing the server publicly

Alexa+ requires a public HTTPS endpoint. Use Cloudflare quick tunnel for development.

### Step 1 - Start the tunnel

Open a second PowerShell window (leave the server terminal running):

```
cloudflared tunnel --url http://localhost:8000

```
Cloudflare will print output like:

```
Your quick Tunnel has been created! Visit it at:
https://random-words-here.trycloudflare.com

```
Copy this HTTPS URL. It is your public endpoint.

### Step 2 - Update .env with the tunnel URL

Open .env and update:

```
OAUTH_ISSUER=https://random-words-here.trycloudflare.com

```
Save the file.

### Step 3 - Restart the MCP server

The server reads .env at startup, so it must be restarted to pick up the new issuer.

In the server terminal, press Ctrl+C, then:

```
uv run python -m server.main

```
### Step 4 - Verify the public URL

In a new PowerShell window:

```
curl.exe https://random-words-here.trycloudflare.com/.well-known/oauth-authorization-server

```
The issuer field in the output should now match your tunnel URL.

### Important about Cloudflare quick tunnels

- The URL changes every time cloudflared restarts. If you close the tunnel terminal, you will get a new URL and must repeat Steps 2-4.
- Keep the tunnel terminal open through the entire session.
- Prevent your laptop from sleeping while the tunnel is live (Settings > System > Power > Screen and sleep > set to Never).

---

## Testing the server

### Test 1 - MCP protocol with the Inspector

In a new PowerShell window:

```
npx @modelcontextprotocol/inspector

```
A browser will open at http://127.0.0.1:6274. Configure:

| Field | Value |
|---|---|
| Transport Type | Streamable HTTP |
| URL | http://localhost:8000/mcp |
| Authorization | (leave empty for local testing) |

Click Connect, then go to the Tools tab and click List Tools. You should see all 10 tools:

```
analyze_scene_for_child
dub_scene
get_child_profile
get_current_context
get_lingo_status
log_decision
replace_dialogue
set_boundary
skip_scene
translate_subtitles

```
Run the jump scare test. Select analyze_scene_for_child, enter:

```
{
  "session_id": "demo-session-1",
  "profile_id": "mia",
  "timestamp_seconds": 80.0
}

```
Expected:

```
{
  "verdict": "skip",
  "reason": "Jump scare detected at 75s. Not suitable for Mia (age 7).",
  "recommended_action": "skip_forward",
  "skip_seconds": 12
}

```
Note: If the server has auth middleware enabled, the Inspector will receive 401 Unauthorized. For local testing, comment out mcp.add_middleware(AlexaAuthMiddleware()) in server/main.py, restart the server, and reconnect. Re-enable it before the Alexa demo.

### Test 2 - ASK shim via curl

Create a test payload file:

```
@'
{"version":"1.0","request":{"type":"IntentRequest","intent":{"name":"AnalyzeSceneIntent","slots":{"child":{"name":"child","value":"Mia"}}}}}
'@ | Set-Content -Path test_intent.json -Encoding ascii

```
Send it to the local server:

```
curl.exe -X POST http://localhost:8000/alexa -H "Content-Type: application/json" --data "@test_intent.json"

```
Expected:

```
{
  "version": "1.0",
  "response": {
    "outputSpeech": {
      "type": "SSML",
      "ssml": "<speak>This is a flagged scene. Jump scare detected at 60s. Not suitable for Mia (age 7). I recommend skipping forward 12 seconds. Say skip it to proceed.</speak>"
    },
    "shouldEndSession": false
  }
}

```
Test the same against the tunnel:

```
curl.exe -X POST https://random-words-here.trycloudflare.com/alexa -H "Content-Type: application/json" --data "@test_intent.json"

```
Identical output confirms end-to-end routing through Cloudflare.

### Test 3 - Unit tests

```
uv run pytest tests/ -v

```
Expected: all tests pass, including test_analyze_scene_jump_scare which verifies the guardian returns skip_forward at t=80.0.

---

## Alexa Developer Console setup

The @alexa-ai/cli MCP Toolkit is currently behind a private preview. This repo uses the traditional Custom Skill path with an ASK-to-MCP shim at /alexa.

### Step 1 - Create the skill

1. Log in to the Alexa Developer Console at https://developer.amazon.com/alexa/console/ask
2. Click Create Skill
3. Skill name: ViewingGuardian
4. Default language: English (US)
5. Model: Custom
6. Hosting: Provision your own
7. Click Create skill, then choose Start from Scratch

### Step 2 - Configure the endpoint

1. In the left sidebar, click Build > Endpoint
2. Select HTTPS
3. Default Region URL: https://random-words-here.trycloudflare.com/alexa
4. SSL certificate: select "My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority"
5. Click Save Endpoints

### Step 3 - Configure Account Linking

1. In the left sidebar, click Tools > Account Linking
2. Toggle "Do you allow users to create an account or link to an existing account?" to ON
3. Configure:

| Field | Value |
|---|---|
| Authorization Grant Type | Authorization Code Grant |
| Client ID | viewingguardian-client |
| Client Secret | Your OAUTH_JWT_SECRET from .env |
| Authorization URI | https://random-words-here.trycloudflare.com/oauth/authorize |
| Access Token URI | https://random-words-here.trycloudflare.com/oauth/token |
| Client Authentication Scheme | HTTP Basic (Recommended) |
| Scope | playback:read,playback:control,profile:read,profile:write |

Critical:

- Scopes must be comma-separated, no spaces. The console rejects any string with spaces (regex for word-characters-only).
- In Advanced Settings, enable S256 as the PKCE code challenge method. Account linking fails without it.

Click Save.

### Step 4 - Set the invocation name

1. In the left sidebar, click Build > Invocations
2. Set Skill Invocation Name: view guardian
3. Click Save Model

The default placeholder is "change name". If you do not replace it, the simulator will respond "I am not quite sure how to help you with that."

### Step 5 - Build the interaction model

1. In the left sidebar, click Build > Interaction Model > Intents
2. Click + Add Intent
3. Name: AnalyzeSceneIntent
4. Add sample utterances, one per line:

```
what is playing
what is playing
is this okay for {child}
is this ok for {child}
check this scene
check this scene for {child}
is this suitable for {child}
is this okay for mia

```
5. In the left sidebar, click Slot Types > + Add Slot Type
6. Name: CHILD_NAME
7. Values:

```
Mia
mia
my daughter
my son

```
8. Go back to AnalyzeSceneIntent > Intent Slots > + Add Slot
9. Name: child, Type: CHILD_NAME
10. Click Save Model

### Step 6 - Build the skill

Click Build skill at the top right. Wait for the green checkmark next to Interaction Model in the left sidebar.

### Step 7 - Test in the simulator

1. Click the Test tab
2. Set the dropdown to Development
3. Type: open view guardian

Expected: "Viewing Guardian is ready. Ask me what is playing, or whether a scene is okay for your child."

Then type: ask view guardian is this okay for mia

Expected: "This is a flagged scene. Jump scare detected at 60s. Not suitable for Mia (age 7). I recommend skipping forward 12 seconds. Say skip it to proceed."

Take a screenshot - that is your end-to-end proof.

---

## Running the demo

### Complete demo sequence

Follow these steps in order. Each terminal must stay open.

Terminal 1 - MCP server:

```
cd C:\Users\YOUR-USER\viewingguardian-mcp
uv run python -m server.main

```
Terminal 2 - Cloudflare tunnel:

```
cloudflared tunnel --url http://localhost:8000

```
Copy the tunnel URL, update OAUTH_ISSUER in .env, then restart Terminal 1 so the server picks up the new issuer.

Terminal 3 - Alexa Developer Console:

In your browser:

1. Open the Developer Console, go to your skill, click Test tab
2. Set the dropdown to Development
3. Run these commands in sequence:

| Command | What it demonstrates |
|---|---|
| open view guardian | Skill launch, endpoint connectivity |
| ask view guardian is this okay for mia | Full guardian flow with jump scare detection |
| ask view guardian what is playing | Context retrieval |
| ask view guardian check this scene for mia | Alternate phrasing of the same intent |

Terminal 4 - MCP Inspector (optional, for protocol proof):

```
npx @modelcontextprotocol/inspector

```
Connect to http://localhost:8000/mcp, list tools, and run analyze_scene_for_child with the jump scare timestamp.

### Scene timeline for the mock film

The included demo film The Whispering Woods has these flagged moments:

| Timestamp | Scene | Flag | Guardian action |
|---|---|---|---|
| 60-75s | Sudden silence before scare | pre_jump_scare | Skip forward 12s |
| 75-90s | Deer bursts from brush | jump_scare | Skip forward 12s |
| 125-140s | Mild profanity | mild_profanity | Replace dialogue |
| 150-170s | Ravine edge, log crossing | peril | Combined intervention |
| 170-195s | Peak peril moment | peak_moment | Skip forward 8s |

### Demo video checklist

For the hackathon submission, your under-3-minute video should show:

- [ ] Fire TV or Vega simulator running the mock film
- [ ] Developer Console simulator responding to ask view guardian is this okay for mia
- [ ] MCP Inspector showing all 10 tools and the analyze_scene_for_child verdict
- [ ] Guardian intervention playing out on screen (skip, dub, or replacement)
- [ ] The public tunnel URL visible in the browser address bar

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| NoCredentialsError on scene analysis | No AWS credentials configured | Expected - falls back to rule-based verdicts. Add credentials to .env to enable live Bedrock. |
| ModuleNotFoundError: server.ask_shim | File not saved or wrong path | Test-Path server\ask_shim.py - if False, create it with New-Item -ItemType File -Path "server\ask_shim.py" -Force |
| error: Failed to build on uv sync | pyproject.toml missing wheel target config | Add packages = ["server"] under [tool.hatch.build.targets.wheel] |
| warning: No requires-python value found | Missing field in pyproject.toml | Add requires-python = ">=3.11" |
| Cloudflare Error 1033 | Tunnel rotated or stopped | Restart cloudflared, update OAUTH_ISSUER in .env, restart the MCP server, update the Developer Console endpoint |
| Alexa says I am not quite sure how to help you with that | Invocation name is the placeholder change name | Set it to view guardian and rebuild the model |
| Alexa says There was a problem with the requested skill response | Endpoint returned invalid data | Check the server terminal for errors. Verify the endpoint URL ends in /alexa, not /mcp. |
| OAuth scope rejected | Spaces in the Scope field | Use comma-separated scopes without spaces: playback:read,playback:control,profile:read,profile:write |
| Account linking fails | S256 missing from metadata | Verify curl https://TUNNEL/.well-known/oauth-authorization-server includes code_challenge_methods_supported: [S256] |
| 401 Unauthorized from MCP Inspector | Auth middleware active | Comment out mcp.add_middleware(AlexaAuthMiddleware()) in server/main.py, restart, reconnect |
| Tunnel URL changes every restart | Free Cloudflare quick tunnel limitation | Keep the tunnel terminal open. If it restarts, repeat the URL update steps. |

---

## What we built during the hackathon

ViewingGuardian + Lingo was conceived and built entirely during the submission window. Nothing existed beforehand. This includes:

- The MCP server with 10 tools (server/)
- The ASK-to-MCP shim (server/ask_shim.py)
- The OAuth 2.1 discovery implementation with PKCE S256
- The mock film The Whispering Woods and its scene metadata
- All Fire TV control and language transformation logic
- The full test suite (unit, auth, latency)

The only pre-existing components are open source libraries (FastMCP, Uvicorn, boto3, httpx) and third-party APIs (Bedrock, ElevenLabs, Home Assistant).

---

## Tracks and mini challenges

- Track: Alexa+
- Mini challenges: Open Source, AWS Builder

---

## AWS services used

- Amazon Bedrock (Claude 3 Sonnet) - scene analysis in server/analysis.py. Called via bedrock.invoke_model(). Falls back to rule-based verdicts when credentials are absent.
- AWS Lambda / DynamoDB / ECS - planned production deployment targets (documented in deploy/).

---

## Friction Log

Development friction encountered while building this project is documented in
[FRICTION_LOG.md](./FRICTION_LOG.md).

---

## License

Apache 2.0 - see LICENSE.
