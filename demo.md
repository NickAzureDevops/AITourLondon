# AI Tour Concierge Demo Plan

Introduction (1 min)
- Briefly explain the project:  
  “AI Tour Concierge for Microsoft AI Tour—helps attendees find sessions, answer FAQs, and build personalized itineraries.”

 Local MCP Concepts (2 min)
- Show local CLI skill pattern (e.g., `gh issue list`).
- Demo: “Show me all sessions in London” (local skill).
- Export report: “Create a summary of AI sessions in London and Tokyo.”
- Explain: “These skills run locally for speed and reliability.”


Agent Skills (1 min)
- Slide: “Skills: Typed, Reusable Capabilities”
- Code snippet:
  ```python
  @skill
  def city_skill(city: str, topic: str | None = None):
      return CityAgent(city).handle(filters={"topic": topic})


Azure AI Foundry Workflow (3 min)
* Pivot: “Now, let’s see how this scales in Azure AI Foundry.”
* Show Foundry agent registration and orchestration.
* Demo: Agent calls skills automatically, produces structured output.
* Show structured output viewer (screenshot or live).

Full End-to-End Flow (2 min)
* Run full flow:
    1. Ask for sessions → triggers elicitation → calls city_skill.
c* Highlight: “This is the ‘wow moment’—local skills, cloud orchestration, structured outputs.”
