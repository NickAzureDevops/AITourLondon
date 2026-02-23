import os
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
BASE_DIR = Path(__file__).parent.parent
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchTool, Tool, PromptAgentDefinition, MemoryStoreDefaultDefinition, MemoryStoreDefaultOptions, MemorySearchTool, ResponsesUserMessageItemParam, MemorySearchOptions
import uuid
from azure.ai.projects.models import MCPTool
import glob
load_dotenv()

# Load environment variables with correct names
search_service_endpoint = os.environ.get("search_service_endpoint")
knowledge_base_name = os.environ.get("KNOWLEDGE_BASE_NAME")
mcp_endpoint = f"{search_service_endpoint}/knowledgebases/{knowledge_base_name}/mcp?api-version=2023-11-01"
PROJECT_ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
agent_model = os.environ.get("FOUNDRY_MODEL")
EMBEDDING_MODEL = os.environ.get("FOUNDRY_EMBEDDING_MODEL")
project_connection_name = os.environ.get("project_connection_name")

project_client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)

openai_client = project_client.get_openai_client()

vector_store_id = ""

if vector_store_id:
    vector_store = openai_client.vector_stores.retrieve(vector_store_id)
    print(f"Using existing vector store (id: {vector_store.id})")
else:
    vector_store = openai_client.vector_stores.create(name="AITour-schedule")
    print(f"Vector store created (id: {vector_store.id})")

    # Upload file(s) to vector store
    files_uploaded = False
    for file_path in glob.glob(str(BASE_DIR / "data/schedule-london.md")):
        with open(file_path, "rb") as f:
            file = openai_client.vector_stores.files.upload_and_poll(
                vector_store_id=vector_store.id, file=f
            )
        print(f"File uploaded to vector store (id: {file.id})")
        files_uploaded = True
    if not files_uploaded:
        print("Warning: No schedule-london.md file found to upload to the vector store.")

session_vector_store_id = vector_store.id
session_toolset = [FileSearchTool(vector_store_ids=[session_vector_store_id])]
session_agent = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
).agents.create_version(
    agent_name="session-agent",
    definition=PromptAgentDefinition(
          model=agent_model,
        instructions=open(BASE_DIR / "src/instructions/session.txt").read(),
        tools=session_toolset,
    ),
)
print(f"Session Agent created (id: {session_agent.id}, name: {session_agent.name}, version: {session_agent.version})")

# Create MCP tool with knowledge base
mcp_kb_tool = MCPTool(
    server_label = "knowledge-base",
    server_url = mcp_endpoint,
    require_approval = "never",
    allowed_tools = ["knowledge_base_retrieve"],
    project_connection_id = project_connection_name
)

# Create agent with MCP tool
faq_agent = project_client.agents.create_version(
    agent_name="faq-agent",
    definition=PromptAgentDefinition(
        model=agent_model,
        instructions=open(BASE_DIR / "src/instructions/faq.txt").read(),
        tools=[mcp_kb_tool], 
    )
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
    FileSearchTool(vector_store_ids=[session_vector_store_id]),
    FileSearchTool(vector_store_ids=["faq_vector_store_id"]), 
    personalised_memory_tool,
]

# Personalized Agent (uses both schedule and FAQ, with persistent memory)
personalised_agent = project_client.agents.create_version(
    agent_name="personalised-agent",
    definition=PromptAgentDefinition(
        model=agent_model,
        instructions=open(BASE_DIR / "src/instructions/personalised.txt").read(),
        tools=personalised_toolset,
    )
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
                chat_model=agent_model,
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
                user_input = input("You: ").strip()
                if user_input.lower() in ["exit", "quit"]:
                    print("Exiting the chat.")
                    break
                if not user_input:
                    print("Please enter a message.")
                    continue

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
                    conversation = openai_client.conversations.create()
                    print(f"Created conversation (id: {conversation.id})")
                    while True:
                        user_input = input("You: ").strip()
                        if user_input.lower() in ["exit", "quit"]:
                            print("Exiting the chat.")
                            break
                        if not user_input:
                            print("Please enter a message.")
                            continue
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
                    user_input = input("You: ").strip()
                    if user_input.lower() in ["exit", "quit"]:
                        print("Exiting the chat.")
                        break
                    if not user_input:
                        print("Please enter a message.")
                        continue
                    response = openai_client.responses.create(
                        conversation=conversation.id,
                        extra_body={"agent": {"name": "faq-agent", "type": "agent_reference"}},
                        input=user_input
                    )
                    print(f"FAQ agent: {response.output_text}")

if __name__ == "__main__":
    chat_with_agent()