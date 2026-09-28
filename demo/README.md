# Demo - ViewingGuardian + Lingo

## The mock film

The Whispering Woods - a 4-minute original short film about two
siblings lost in the woods. Written and produced for this hackathon.
No third-party footage or trademarks.

## Scene timeline

| Timestamp | Scene | Flag | Guardian action |
|---|---|---|---|
| 60-75s | Sudden silence before scare | pre_jump_scare | Skip forward 12s |
| 75-90s | Deer bursts from brush | jump_scare | Skip forward 12s |
| 125-140s | Mild profanity | mild_profanity | Replace dialogue |
| 150-170s | Ravine edge | peril | Combined intervention |
| 170-195s | Peak peril moment | peak_moment | Skip forward 8s |

## Child profile

- Name: Mia
- Age: 7
- Sensitivities: jump scares (high), peril (high)
- Household rules: family-friendly language (strict)

## Running the demo

1. Start the MCP server: uv run python -m server.main
2. Start the tunnel: cloudflared tunnel --url http://localhost:8000
3. Update .env with the tunnel URL and restart the server
4. Open the Alexa Developer Console Test tab
5. Say: open view guardian
6. Say: ask view guardian is this okay for mia
