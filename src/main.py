import json
import os

from mem0 import Memory
from mem0.memory.utils import extract_json
from openai import OpenAI
from qwen_token_counter import get_token_count

from simpleMemory.memoryQueue import MemoryQueue
from tools.dnd_tools import DnD_TOOLS
from tools.dnd_tools_script import *

os.environ["OPENAI_API_KEY"] = "api"
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
# MODEL_NAME = "capybarahermes"
MODEL_NAME = "qwen3:8b-8196"

# This helps the mem0 know what facts it needs to remember.
# The default one is for health assistant, so we need a more dnd master one.
# See: https://docs.mem0.ai/open-source/features/custom-fact-extraction-prompt
with open('prompts/fact_extraction.txt', 'r') as f:
    CUSTOM_FACT_EXTRACTION_PROMPT = f.read()

memory_config = {
    "version": "v1.1",
    "vector_store": {
        "provider": "chroma",
        "config": {
            "collection_name": "test",
            "path": "db",
        }
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "multi-qa-MiniLM-L6-cos-v1"
        }
    },
    "llm": {
        "provider": "openai",
        "config": {
            "model": f"{MODEL_NAME}",
            "temperature": 0.1,
            "openai_base_url": "http://127.0.0.1:11434/v1"
        }
    },
    # "graph_store": {
    #     "provider": "neo4j",
    #     "config": {
    #         "url": "neo4j://localhost:7687",
    #         "username": "neo4j",
    #         "password": "12345678"
    #     }
    # },
    "custom_fact_extraction_prompt": CUSTOM_FACT_EXTRACTION_PROMPT
}
WORLD_ID='world_01'

client = OpenAI(
    base_url='http://127.0.0.1:11434/v1'
)
m = Memory.from_config(memory_config)
# Personality
# Test only: dnd master
with open('prompts/agent_personality_tool.txt', 'r', encoding="utf-8") as f:
    AGENT_PERSONALITY = f.read()

recent_conversations = MemoryQueue(size=6)


def load_world_context():
    """Load all world context files"""
    context_files = [
        'world_integration.txt',
        'world_map.txt',
        'world_factions.txt',
        'world_history.txt',
        'cities_history.txt',
        'terminology.txt',
        'magic_sys.txt',
        'dnd_function.txt',
        'dnd_master_tools.txt',
        'combat.txt',
        'loot.txt',
        'chac_creation.txt',
    ]

    contexts = {}
    for file in context_files:
        try:
            with open(f'prompts/world_context/{file}', 'r', encoding="utf-8") as f:
                contexts[file.replace('.txt', '')] = f.read()
        except FileNotFoundError:
            print(f"Warning: {file} not found, skipping...")
            contexts[file.replace('.txt', '')] = ""

    return contexts


def initialize_world_memory(world_id: str, max_chunk_size: int = 100000):
    """Load full world context with intelligent chunking"""
    world = load_world_context()

    added_chunks = []
    total_chars = 0

    for key, content in world.items():
        if not content or len(content.strip()) == 0:
            continue

        # Split large content into smaller chunks
        # section_title = f"=== {key.replace('_', ' ').title()} ===\n"

        # If content is small, send as one chunk
        if len(content) <= max_chunk_size:
            chunk = content
            try:
                m.add([{"role": "system", "content": chunk}], user_id=world_id)
                added_chunks.append(chunk)
                new_tks = get_token_count(chunk)
                total_chars += new_tks
                print(f"Added {key} ({new_tks} tokens)")
            except Exception as e:
                pass
                # print(f"Error adding {key}: {e}")
        else:
            # Split large content into chunks
            content_chunks = split_content(content, max_chunk_size)
            for i, content_chunk in enumerate(content_chunks):
                # chunk = section_title if i == 0 else ""
                chunk = content_chunk
                if i < len(content_chunks) - 1:
                    chunk += "\n[continued...]"

                try:
                    m.add([{"role": "system", "content": chunk}], user_id=world_id)
                    added_chunks.append(chunk)
                    total_chars += get_token_count(chunk)
                    print(f"Added {key} part {i + 1} ({get_token_count(content_chunk)} chars)")
                except Exception as e:
                    pass
                    # print(f"Error adding {key} part {i + 1}: {e}")

    print(f"Loaded {len(added_chunks)} world context chunks ({total_chars} total tokens)")
    return added_chunks


def split_content(content: str, chunk_size: int):
    """Split content intelligently at paragraph boundaries"""
    paragraphs = content.split('\n\n')
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def parse_response(response, tools):
    if tools:
        processed_response = {
            "content": response.choices[0].message.content,
            "tool_calls": [],
        }

        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                processed_response["tool_calls"].append(
                    {
                        "name": tool_call.function.name,
                        "arguments": json.loads(extract_json(tool_call.function.arguments)),
                        "call_id": tool_call.id
                    }
                )

        return processed_response
    else:
        return response.choices[0].message.content


def agent_workflow(user_input: str, user_id: str):
    print(f"\n[User Input]: {user_input}")

    # 1. Retrieval & World Status Check
    # use mem0 to get history context and world state, instead of the entire conversation
    conversation_mem = m.search(query=user_input, user_id=user_id, limit=5)
    world_mem = m.search(query=user_input, user_id=WORLD_ID, limit=15)

    # Parse search results
    history_context = ""
    world_context = ""

    if "results" in conversation_mem:  # Vector database query result (History Mem)
        # Separate world context from conversation history
        for item in conversation_mem["results"]:
            memory_text = item.get("memory", "")
            history_context += memory_text + "\n"

    if "results" in world_mem:  # Vector database query result (History Mem)
        # Separate world context from conversation history
        for item in world_mem["results"]:
            memory_text = item.get("memory", "")
            world_context += memory_text + "\n"

    # if "relations" in search_results:  # Graph database query result (World Status)
    #     # e.g.: Player -- location --> Room A
    #     world_status = "\n".join(
    #         [f"{r}" for r in search_results["relations"]])

    print(f"[History]: {history_context}")
    print(f"[Current World Status]: {world_context}")

    # 2. Personality Processing
    # Construct the prompt

    full_prompt = f"""
    === World Status ===
    {world_context}

    === History Memory ===
    {history_context}
    
    === Recent Few Conversations ===
    {str(recent_conversations.get_all())}

    === User input ===
    {user_input}

    As the DnD master, please give your response with given information.
    """

    # Agent Output
    messages = complete(
        messages=[{"role": "system", "content": AGENT_PERSONALITY},
                  {"role": "user", "content": full_prompt}])
    agent_output = messages[-1]['content']
    print(f"[Agent Output]: {agent_output}")

    # 3. Update
    # Update the interaction into:
    #   1. Store into Vector database (History Memory)
    #   2. Analyze the status change and update Graph Store (World Status)
    try:
        m.add(messages, user_id=user_id)
    except Exception:
        print(messages)

    for msg in messages:
        recent_conversations.add(msg)
    # m.add(messages, user_id=user_id, enable_graph=False)

    return agent_output


def complete(messages, tool_choice: str = "auto"):
    # messages.append({"role": "system", "content": llm_system_prompt})

    # Step 1: Send conversation and list of available external functions to GPT
    print(f'Token count: {get_token_count(str(messages))}')
    response_ = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=DnD_TOOLS,
        tool_choice=tool_choice
    )

    response_message = parse_response(response_, True)

    # Step 2: Check if GPT called external functions
    if response_message["tool_calls"]:
        print(f'[Agent Temp Output]: {response_message["content"]}')
        # Step 3: Call external functions and get results
        available_functions = {
            "roll_dice": roll_dice,
            "defense": defense,
            "attack": attack,
            "create_entity": create_entity,
            "query_target": query_target,
            "query_all": query_all,
        }
        tool_calls = response_message["tool_calls"]
        function_responses = []
        # Get matched external functions
        for tool_call in tool_calls:
            tool_name = tool_call['name']
            function_to_call = available_functions[tool_name]
            # Get input parameter information of external functions
            function_args = tool_call["arguments"]
            # Assemble input parameters according to the specified external function and call it
            if tool_name == "roll_dice":
                function_response = function_to_call(
                    modifier=function_args.get("modifier", 0),
                    roll_purpose=function_args.get("roll_purpose", "roll dice"),
                    related_entity=function_args.get("related_entity")
                )

            elif tool_name == "defense":
                function_response = function_to_call(
                    defender_id=function_args.get("defender_id"),
                    defense_modifier=function_args.get("defense_modifier", 0),
                    defense_purpose=function_args.get("defense_purpose", "normal_attack")
                )
            elif tool_name == "attack":
                function_response = function_to_call(
                    attacker_id=function_args.get("attacker_id"),
                    target_id=function_args.get("target_id"),
                    attack_modifier=function_args.get("attack_modifier", 0),
                    damage_range=function_args.get("damage_range", [1, 4])
                )
            elif tool_name == "create_entity":
                # Handle EntityType enum conversion
                entity_type_str = function_args.get("entity_type")
                entity_type = None
                if entity_type_str:
                    for et in EntityType:
                        if et.value == entity_type_str.lower():
                            entity_type = et
                            break

                function_response = function_to_call(
                    entity_name=function_args.get("entity_name"),
                    entity_type=entity_type,
                    hp_max=function_args.get("hp_max"),
                    attack_modifier=function_args.get("attack_modifier"),
                    defense_modifier=function_args.get("defense_modifier"),
                    custom_id=function_args.get("custom_id")
                )
            elif tool_name == "query_target":
                function_response = function_to_call(
                    target_id=function_args.get("target_id"),
                    query_type=function_args.get("query_type")
                )
            elif tool_name == "query_all":
                function_response = function_to_call()
            else:
                function_response = {"error_msg": f"unsupport function name: {tool_name}"}

            print(f'[{tool_name}]: {function_response}')

            function_responses.append((tool_call["call_id"], function_response))

        # Step 4: Assemble the original request and external function response results and send to GPT
        for i in range(len(function_responses)):
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": function_responses[i][0],
                    "content": json.dumps(function_responses[i][1]),
                }
            )
        complete(messages)
    else:
        messages.append({
            "role": "assistent",
            "content": response_message['content']
        })
    return messages


def try_attack():
    user_id = "player_01"
    # initialization
    m.delete_all(user_id=user_id)
    # Load world context into memory FIRST
    initialize_world_memory(world_id=WORLD_ID)
    # The first round
    agent_workflow("I summon a wooden dummy.", user_id)
    agent_workflow("I attack the wooden dummy.", user_id)


def chat(user_id):
    print(f"[System] Starting...")
    # initialization
    m.delete_all(user_id=user_id)
    # Load world context into memory FIRST
    initialize_world_memory(world_id=WORLD_ID)
    print(f"[System] Running now. Hi, {user_id}!")
    while True:
        print()
        user_input = input('Type "quit" to leave:')
        if user_input == 'quit':
            break
        agent_workflow(user_input, user_id)


if __name__ == '__main__':
    chat("player_01")
