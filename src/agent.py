from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, FileSearchTool
from dotenv import load_dotenv
import os
import glob

load_dotenv()

project_client = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
openai_client = project_client.get_openai_client()

session_vector_store = openai_client.vector_stores.create(name="SessionStore")
faq_vector_store = openai_client.vector_stores.create(name="FAQStore")

print(f"Session vector store: {session_vector_store.id}")
print(f"FAQ vector store: {faq_vector_store.id}")

# Upload files to session vector store
for file_path in glob.glob("data/schedule-data-all.json"):
    with open(file_path, "rb") as f:
        file = openai_client.vector_stores.files.upload_and_poll(
            vector_store_id=session_vector_store.id,
            file=f
        )
        print(f"Session file uploaded (id: {file.id})")

# Upload files to FAQ vector store
for file_path in glob.glob("data/faq.md"):
    with open(file_path, "rb") as f:
        file = openai_client.vector_stores.files.upload_and_poll(
            vector_store_id=faq_vector_store.id,
            file=f
        )
        print(f"FAQ file uploaded (id: {file.id})")

# --- Toolsets ---
session_toolset = [FileSearchTool(vector_store_ids=[session_vector_store.id])]
faq_toolset = [FileSearchTool(vector_store_ids=[faq_vector_store.id])]
personalised_toolset = session_toolset + faq_toolset

# --- Agents ---
session_agent = project_client.agents.create_version(
    agent_name="session-agent",
    definition=PromptAgentDefinition(
        model=os.environ["FOUNDRY_MODEL"],
        instructions=open("src/instructions/session.txt").read(),
        tools=session_toolset,
    ),
)

faq_agent = project_client.agents.create_version(
    agent_name="faq-agent",
    definition=PromptAgentDefinition(
        model=os.environ["FOUNDRY_MODEL"],
        instructions=open("src/instructions/faq.txt").read(),
        tools=faq_toolset,
    ),
)

personalised_agent = project_client.agents.create_version(
    agent_name="personalised-agent",
    definition=PromptAgentDefinition(
        model=os.environ["FOUNDRY_MODEL"],
        instructions=open("src/instructions/personalised.txt").read(),
        tools=personalised_toolset,
    ),
)

print(f"Session Agent created (id: {session_agent.id})")
print(f"FAQ Agent created (id: {faq_agent.id})")
print(f"Personalised Agent created (id: {personalised_agent.id})")


def chat_with_agent():
    print("\nSelect agent: session, faq, personalized")
    agent_choice = input("Agent: ").strip().lower()

    if agent_choice not in ["session", "faq", "personalized"]:
        print("Invalid agent. Defaulting to personalized.")
        agent_choice = "personalized"

    scope = "{{$userId}}"  # Maps to authenticated user, see MS Learn docs
    model = os.environ["FOUNDRY_MODEL"]

    with AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
    ) as project_client:
        if agent_choice == "personalized":

            while True:
                user_input = input("You: ")
                if user_input.lower() in ["exit", "quit"]:
                    print("Exiting the chat.")
                    break

                user_message = ResponsesUserMessageItemParam(
                    content=user_input
                )
                content = "What are my preferences?"

                print("Personalized agent logic would go here.")
        
        elif agent_choice == "session":
                    print("Ready to chat with session agent.")
                    conversation = openai_client.conversations.create()
                    print(f"Created conversation (id: {conversation.id})")
                    while True:
                        user_input = input("You: ")
                        if user_input.lower() in ["exit", "quit"]:
                            print("Exiting the chat.")
                            break
                        response = openai_client.responses.create(
                            conversation=conversation.id,
                            extra_body={"agent": {"name": "session-agent", "type": "agent_reference"}},
                            input=user_input
                        )
                        print(f"Session agent: {response.output_text}")
        
        elif agent_choice == "faq":
                print("Ready to chat with FAQ agent (Azure knowledge base).")
                conversation = openai_client.conversations.create()
                print(f"Created conversation (id: {conversation.id})")
                while True:
                    user_input = input("You: ")
                    if user_input.lower() in ["exit", "quit"]:
                        print("Exiting the chat.")
                        break
                    response = openai_client.responses.create(
                        conversation=conversation.id,
                        extra_body={"agent": {"name": "faq-agent", "type": "agent_reference"}},
                        input=user_input
                    )
                    print(f"FAQ agent: {response.output_text}")

if __name__ == "__main__":
    chat_with_agent()