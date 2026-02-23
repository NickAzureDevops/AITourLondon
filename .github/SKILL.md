# AI Tour Concierge — Agent Skills

This project uses **Agent Skills** to define typed, reusable capabilities that the Orchestrator Agent can call.  
Skills follow the same pattern as MCP tools — structured inputs, structured outputs, and clear intent triggers — but run locally for speed and reliability during the demo.

Below are the core skills used in the Build session, each mapped to an MCP concept.

---

## 1. City Skill  
**MCP Concept:** Elicitation Flows  
**Purpose:** Retrieve sessions, speakers, and topics for a specific city.

See: `city_skill.md`

---

## 2. Itinerary Skill  
**MCP Concept:** Exporting Reports  
**Purpose:** Generate a structured itinerary combining sessions, Learn modules, and preferences.

See: `itinerary_skill.md`

---

## Optional Skills (Not shown in the Build demo)

These skills exist in the project but are not demonstrated on stage:

- `github_cli_skill.md` — example of a teammate‑style tool
