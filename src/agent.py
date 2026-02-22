import os
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
BASE_DIR = Path(__file__).parent.parent
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchTool, Tool, PromptAgentDefinition, MemoryStoreDefaultDefinition, MemoryStoreDefaultOptions, MemorySearchTool, ResponsesUserMessageItemParam, MemorySearchOptions
import uuid

load_dotenv()

PROJECT_ENDPOINT = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", os.environ.get("FOUNDRY_PROJECT_ENDPOINT"))
CHAT_MODEL = os.environ.get("MEMORY_STORE_CHAT_MODEL_DEPLOYMENT_NAME", os.environ.get("FOUNDRY_MODEL"))
EMBEDDING_MODEL = os.environ.get("MEMORY_STORE_EMBEDDING_MODEL_DEPLOYMENT_NAME", os.environ.get("FOUNDRY_EMBEDDING_MODEL", CHAT_MODEL))

openai_client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    model=CHAT_MODEL,
    credential=DefaultAzureCredential(),
).get_openai_client()

def create_vector_store_and_upload(name, file_path):
    vector_store = openai_client.vector_stores.create(name=name)
    print(f"Vector store created (id: {vector_store.id}) for {name}")
    file = openai_client.vector_stores.files.upload_and_poll(
        vector_store_id=vector_store.id, file=open(file_path, "rb")
    )
    print(f"File uploaded to vector store (id: {file.id}) for {name}")
    return vector_store

# Schedule Agent vector store and toolset
session_vector_store = create_vector_store_and_upload("AITour-schedule", BASE_DIR / "data/schedule-london.md")
session_toolset = [FileSearchTool(vector_store_ids=[session_vector_store.id])]

session_agent = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
).agents.create_version(
    agent_name="session-agent",
    definition=PromptAgentDefinition(
        model=os.environ["FOUNDRY_MODEL"],
        instructions=open(BASE_DIR / "src/instructions.txt").read(),
        tools=session_toolset,
    ),
)
print(f"Session Agent created (id: {session_agent.id}, name: {session_agent.name}, version: {session_agent.version})")

# FAQ Agent
faq_vector_store = create_vector_store_and_upload("AITour-faq", BASE_DIR / "data/faq.md")
faq_toolset = [FileSearchTool(vector_store_ids=[faq_vector_store.id])]

faq_agent = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
).agents.create_version(
    agent_name="faq-agent",
    definition=PromptAgentDefinition(
        model=os.environ["FOUNDRY_MODEL"],
        instructions="Use the get_faq tool to answer attendee questions about logistics, venue, registration, food, WiFi, workshops, networking, and other frequently asked questions. Always call the get_faq tool for any question that matches or relates to the FAQ data. If the user asks a question that is not covered by the FAQ, respond politely and suggest where they might find more information or direct them to event staff",
        tools=faq_toolset,
    ),
)
print(f"FAQ Agent created (id: {faq_agent.id}, name: {faq_agent.name}, version: {faq_agent.version})")

# Personalised Agent (uses both schedule and FAQ, with persistent memory)
personalised_memory_store_name = "ai_tour_personalised_memory_store"
user_id = str(uuid.uuid4())
personalised_memory_tool = MemorySearchTool(
    memory_store_name=personalised_memory_store_name,
    scope=user_id,
    update_delay=1,
)
personalised_toolset = [
    FileSearchTool(vector_store_ids=[session_vector_store.id]),
    FileSearchTool(vector_store_ids=[faq_vector_store.id]),
    personalised_memory_tool,
]
personalised_agent = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
).agents.create_version(
    agent_name="personalised-agent",
    definition=PromptAgentDefinition(
        model=os.environ["FOUNDRY_MODEL"],
        instructions="You are a personalised concierge agent for the Microsoft AI Tour. Use schedule and FAQ tools to answer questions, and use persistent memory to remember user preferences and context across sessions.",
        tools=personalised_toolset,
    ),
)
print(f"Personalised Agent created (id: {personalised_agent.id}, name: {personalised_agent.name}, version: {personalised_agent.version})")

# Unified chat loop for agent selection and memory operations
def chat_with_agent():
    print("\nSelect agent: session, faq, personalized")
    agent_choice = input("Agent: ").strip().lower()

    if agent_choice not in ["session", "faq", "personalized"]:
        print("Invalid agent. Defaulting to personalized.")
        agent_choice = "personalized"

    scope = "{{$userId}}"  # Maps to authenticated user, see MS Learn docs
    model = os.environ["FOUNDRY_MODEL"]

    with AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    ) as project_client:
        if agent_choice == "personalized":
            all_memory_store_name = personalised_memory_store_name
            all_memory_description = "Unified memory store for AI Tour agents (session, FAQ, personalized)"
            options = MemoryStoreDefaultOptions(
                chat_summary_enabled=True,
                user_profile_enabled=True,
                user_profile_details="Avoid irrelevant or sensitive data, such as age, financials, precise location, and credentials"
            )
            definition = MemoryStoreDefaultDefinition(
                chat_model=CHAT_MODEL,
                embedding_model=EMBEDDING_MODEL,
                options=options
            )
            try:
                project_client.memory_stores.get(all_memory_store_name)
            except Exception:
                project_client.memory_stores.create(
                    name=all_memory_store_name,
                    definition=definition,
                    description=all_memory_description,
                )
            print(f"Ready to store and retrieve user preferences in unified memory store: {all_memory_store_name}")

            while True:
                user_input = input("You: ")
                if user_input.lower() in ["exit", "quit"]:
                    print("Exiting the chat.")
                    break

                user_message = ResponsesUserMessageItemParam(
                    content=user_input
                )
                update_poller = project_client.memory_stores.begin_update_memories(
                    name=all_memory_store_name,
                    scope=scope,
                    items=[user_message],
                    update_delay=0,
                )
                update_result = update_poller.result()
                print(f"Updated with {len(update_result.memory_operations)} memory operations")
                for operation in update_result.memory_operations:
                    print(f"  - Operation: {operation.kind}, Memory ID: {operation.memory_item.memory_id}, Content: {operation.memory_item.content}")

                query_message = ResponsesUserMessageItemParam(
                    content="What are my preferences?"
                )
                search_response = project_client.memory_stores.search_memories(
                    name=all_memory_store_name,
                    scope=scope,
                    items=[query_message],
                    options=MemorySearchOptions(max_memories=5)
                )
                print(f"Found {len(search_response.memories)} memories:")
                for memory in search_response.memories:
                    print(f"  - Memory ID: {memory.memory_item.memory_id}, Content: {memory.memory_item.content}")

                print("Personalized agent logic would go here.")
        
        elif agent_choice == "session":
            print("Ready to chat with session agent.")
            while True:
                user_input = input("You: ")
                if user_input.lower() in ["exit", "quit"]:
                    print("Exiting the chat.")
                    break
                response = openai_client.responses.create(
                    model=model,
                    input=user_input,
                    tools=[{"type": "file_search", "vector_store_ids": [session_vector_store.id]}],
                )
                print(f"Session agent: {response.output_text}")
        
        elif agent_choice == "faq":
            print("Ready to chat with FAQ agent.")
            while True:
                user_input = input("You: ")
                if user_input.lower() in ["exit", "quit"]:
                    print("Exiting the chat.")
                    break
                response = openai_client.responses.create(
                    model=model,
                    input=user_input,
                    tools=[{"type": "file_search", "vector_store_ids": [faq_vector_store.id]}],
                )
                print(f"FAQ agent: {response.output_text}")

if __name__ == "__main__":
    chat_with_agent()
