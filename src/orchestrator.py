from .agent import PROJECT_ENDPOINT, session_agent, faq_agent, personalised_agent, openai_client
import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

def route(agent: str, message: str):
	"""Route a message to the specified agent using Azure AI Projects SDK."""
	if agent in ["faq", "faq-agent"]:
		agent_obj = faq_agent
	elif agent in ["session", "session-agent"]:
		agent_obj = session_agent
	elif agent in ["personalized", "personalised-agent"]:
		agent_obj = personalised_agent
	else:
		return f"Unknown agent: {agent}"

	response = openai_client.responses.create(
		model=os.environ["FOUNDRY_MODEL"],
		input=message,
		instructions=agent_obj.definition.instructions,
		tools=agent_obj.definition.tools,
	)
	return response.output_text
