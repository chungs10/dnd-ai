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
# Test only: dnd master
with open('prompts/agent_personality.txt', 'r') as f:
    AGENT_PERSONALITY = f.read()
def load_world_context():
    """Load all world context files"""
    context_files = [
        'world_history.txt',
        'world_map.txt', 
        'cities_history.txt',
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
def initialize_world_memory(user_id: str, max_chunk_size: int = 2000):
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
                total_chars += len(chunk)
                print(f"Added {key} ({len(content)} chars)")
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
                    total_chars += len(chunk)
                    print(f"Added {key} part {i+1} ({len(content_chunk)} chars)")
                except Exception as e:
                    print(f"Error adding {key} part {i+1}: {e}")
    
    print(f"Loaded {len(added_chunks)} world context chunks ({total_chars} total characters)")
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

    # 解析检索结果
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
        # 例如：Player -- location --> Room A
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
    m.add(messages, user_id=user_id)
    
    print(f"[Agent Output]: {agent_output}")
    return agent_output

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
