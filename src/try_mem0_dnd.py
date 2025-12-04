import os
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
    },  # TODO: Graph db is better for relationship memorization, need tests
    "custom_fact_extraction_prompt": CUSTOM_FACT_EXTRACTION_PROMPT
}

client = OpenAI(
    base_url='http://127.0.0.1:11434/v1'
)
m = Memory.from_config(memory_config)

# Personality
with open('prompts/agent_personality.txt', 'r') as f:
    AGENT_PERSONALITY = f.read()


def load_world_context():
    """Load all world context files"""
    context_files = [
        'world_history.txt',
        'world_map.txt',
        'city_histories.txt',
        'terminology.txt',
        'world_factions.txt',
        'dnd_function.txt',
        'dnd_master_tools.txt'
    ]

    contexts = {}
    for file in context_files:
        try:
            with open(f'prompts/world_context/{file}', 'r') as f:
                contexts[file.replace('.txt', '')] = f.read()
        except FileNotFoundError:
            print(f"Warning: {file} not found, skipping...")
            contexts[file.replace('.txt', '')] = ""

    return contexts


def dnd_func_call():
    pass


def agent_workflow(user_input: str, user_id: str):
    print(f"\n[User Input]: {user_input}")

    # -------------------------------------------------
    # 1. Retrieval & World Status Check
    # -------------------------------------------------
    # use mem0 to get history context and world state, instead of the entire conversation
    search_results = m.search(query=user_input, user_id=user_id, limit=30)

    # 解析检索结果
    history_context = ""
    world_status = ""

    if "results" in search_results:  # Vector database query result (History Mem)
        history_context = "\n".join([item["memory"] for item in search_results["results"]])

    if "relations" in search_results:  # Graph database query result (World Status)
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

    === History Memory ===
    {history_context}

    === World Status ===
    {world_status}

    === User input ===
    {user_input}

    Please generate your response based on the above contexts:
    """

    # Agent Output
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": full_prompt}]
    )
    agent_output = response.choices[0].message.content

    # -------------------------------------------------
    # 3. Update
    # -------------------------------------------------
    # Update the interaction into   :
    #   1. Store into Vector database (History Memory)
    #   2. Analyze the status change and update Graph Store (World Status)

    messages = [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": agent_output}
    ]
    # m.add(messages, user_id=user_id, enable_graph=False)
    m.add(messages, user_id=user_id, )

    print(f"[Agent Output]: {agent_output}")
    return agent_output

# def initialization():
#     contexts = load_world_context()
#     for context in contexts:
#         m.add([{"role": "user", "content": str(context)}], user_id=user_id)


if __name__ == '__main__':
    user_id = "player_01"
    # initialization
    m.delete_all(user_id=user_id)

    # The first round
    agent_workflow("I enter a dark room, finding a rusty key on the floor.", user_id)

    # Second round, there should be some memories
    agent_workflow("I pick up the key.", user_id)

    agent_workflow("What do I have?", user_id)
