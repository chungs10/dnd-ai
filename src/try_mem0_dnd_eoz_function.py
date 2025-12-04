import json
import os
from tools.dnd_tools_script import *
from tools.dnd_tools import DnD_TOOLS
from qwen_token_counter import get_token_count
from openai import OpenAI
from mem0 import Memory

os.environ["OPENAI_API_KEY"] = "api"
# os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
# MODEL_NAME = "capybarahermes"
MODEL_NAME = "qwen3:8b"

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
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": "neo4j://localhost:7687",
            "username": "neo4j",
            "password": "12345678"
        }
    },
    "custom_fact_extraction_prompt": CUSTOM_FACT_EXTRACTION_PROMPT
}

client = OpenAI(
    base_url='http://127.0.0.1:11434/v1'
)
m = Memory.from_config(memory_config)

# Personality
# Test only: dnd master
with open('prompts/agent_personality.txt', 'r', encoding="utf-8") as f:
    AGENT_PERSONALITY = f.read()


def load_world_context():
    """Load all world context files"""
    context_files = [
        'world_history.txt',
        # 'world_map.txt',
        # 'cities_history.txt',
        # 'terminology.txt',
        # 'world_factions.txt',
        # 'dnd_function.txt',
        # 'dnd_master_tools.txt'
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


def initialize_world_memory(user_id: str, max_chunk_size: int = 100000):
    """Load full world context with intelligent chunking"""
    world = load_world_context()

    added_chunks = []
    total_chars = 0

    for key, content in world.items():
        if not content or len(content.strip()) == 0:
            continue

        # Split large content into smaller chunks
        section_title = f"=== {key.replace('_', ' ').title()} ===\n"

        # If content is small, send as one chunk
        if len(content) <= max_chunk_size:
            chunk = section_title + content
            try:
                m.add([{"role": "system", "content": chunk}], user_id=user_id)
                added_chunks.append(chunk)
                new_tks = get_token_count(chunk)
                total_chars += new_tks
                print(f"Added {key} ({new_tks} tokens)")
            except Exception as e:
                print(f"Error adding {key}: {e}")
        else:
            # Split large content into chunks
            content_chunks = split_content(content, max_chunk_size)
            for i, content_chunk in enumerate(content_chunks):
                chunk = section_title if i == 0 else ""
                chunk += content_chunk
                if i < len(content_chunks) - 1:
                    chunk += "\n[continued...]"

                try:
                    m.add([{"role": "system", "content": chunk}], user_id=user_id)
                    added_chunks.append(chunk)
                    total_chars += get_token_count(chunk)
                    print(f"Added {key} part {i + 1} ({get_token_count(content_chunk)} chars)")
                except Exception as e:
                    print(f"Error adding {key} part {i + 1}: {e}")

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


def agent_workflow(user_input: str, user_id: str):
    print(f"\n[User Input]: {user_input}")

    # -------------------------------------------------
    # 1. Retrieval & World Status Check
    # -------------------------------------------------
    # use mem0 to get history context and world state, instead of the entire conversation
    search_results = m.search(query=user_input, user_id=user_id, limit=15)

    # Parse search results
    history_context = ""
    world_status = ""
    world_context = ""

    if "results" in search_results:  # Vector database query result (History Mem)
        # Separate world context from conversation history
        for item in search_results["results"]:
            memory_text = item.get("memory", "")
            if "=== EORZEA WORLD CONTEXT ===" in memory_text:
                world_context = memory_text
            else:
                history_context += memory_text + "\n"

    if "relations" in search_results:  # Graph database query result (World Status)
        # e.g.: Player -- location --> Room A
        world_status = "\n".join(
            [f"{r}" for r in search_results["relations"]])

    print(f"[History]: {history_context}")
    print(f"[Current World Status]: {world_status}")

    # -------------------------------------------------
    # 2. Personality Processing
    # -------------------------------------------------
    # Construct the prompt

    full_prompt = f"""
    {AGENT_PERSONALITY}

    === World Context ===
    {world_context}

    === History Memory ===
    {history_context}

    === World Status ===
    {world_status}

    === User input ===
    {user_input}

    Please generate your response based on the above contexts:
    """

    # Agent Output
    agent_output = complete(messages=[{"role": "user", "content": full_prompt}])

    # -------------------------------------------------
    # 3. Update
    # -------------------------------------------------
    # Update the interaction into:
    #   1. Store into Vector database (History Memory)
    #   2. Analyze the status change and update Graph Store (World Status)

    messages = [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": agent_output}
    ]
    # m.add(messages, user_id=user_id, enable_graph=False)
    m.add(messages, user_id=user_id)

    print(f"[Agent Output]: {agent_output}")
    return agent_output


def complete(messages, tool_choice: str = "auto"):
    # messages.append({"role": "system", "content": llm_system_prompt})

    # Step 1: Send conversation and list of available external functions to GPT
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=DnD_TOOLS,
        tool_choice=tool_choice
    )

    response_message = response.choices[0].message

    # Step 2: Check if GPT called external functions
    if response_message.tool_calls:
        print(f"[Agent Temp Output]: {response_message.content}")
        # Step 3: Call external functions and get results
        available_functions = {
            "roll_dice": roll_dice,
            "defense": defense,
            "attack": attack,
            "create_entity": create_entity,
            "query_target": query_target,
            "query_all": query_all,
        }
        function_names = response_message.tool_calls
        function_responses = []
        # Get matched external functions
        for function_name in function_names:
            function_to_call = available_functions[function_name]
            # Get input parameter information of external functions
            function_args = json.loads(response_message.function_call.arguments)
            # Assemble input parameters according to the specified external function and call it
            if function_name == "roll_dice":
                function_response = function_to_call(
                    modifier=function_args.get("modifier", 0),
                    roll_purpose=function_args.get("roll_purpose", "roll dice"),
                    related_entity=function_args.get("related_entity")
                )
            elif function_name == "defense":
                function_response = function_to_call(
                    defender_id=function_args.get("defender_id"),
                    defense_modifier=function_args.get("defense_modifier", 0),
                    defense_purpose=function_args.get("defense_purpose", "normal_attack")
                )
            elif function_name == "attack":
                function_response = function_to_call(
                    attacker_id=function_args.get("attacker_id"),
                    target_id=function_args.get("target_id"),
                    attack_modifier=function_args.get("attack_modifier", 0),
                    damage_range=function_args.get("damage_range", [1, 4])
                )
            elif function_name == "create_entity":
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
            elif function_name == "query_target":
                function_response = function_to_call(
                    target_id=function_args.get("target_id"),
                    query_type=function_args.get("query_type")
                )
            elif function_name == "query_all":
                function_response = function_to_call()
            else:
                function_response = {"error_msg": f"unsupport function name: {function_name}"}

            function_responses.append(function_response)

        # Step 4: Assemble the original request and external function response results and send to GPT
        messages.append(response_message)
        for i in range(len(function_responses)):
            messages.append(
                {
                    "role": "function",
                    "name": function_names[i],
                    "content": function_responses[i],
                }
            )
    else:
        return response_message.content

    while messages[-1]['role'] == "function":
        complete(messages)


if __name__ == '__main__':
    user_id = "player_01"
    # initialization
    m.delete_all(user_id=user_id)
    # Load world context into memory FIRST
    initialize_world_memory(user_id)
    # The first round
    agent_workflow("I enter a dark room, finding a rusty key on the floor.", user_id)

    # Second round, there should be some memories
    agent_workflow("I pick up the key.", user_id)

    agent_workflow("What do I have?", user_id)