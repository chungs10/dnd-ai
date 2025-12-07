import os
from openai import OpenAI
from mem0 import Memory

WORLD_USER_ID = "world_eorzea"  # Fixed ID for world knowledge
PLAYER_USER_ID = "player_01"    # Player's ID

os.environ["OPENAI_API_KEY"] = "api"
# os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
# MODEL_NAME = "capybarahermes"
MODEL_NAME = "qwen3:8b"

# This helps the mem0 know what facts it needs to remember.
# The default one is for health assistant, so we need a more dnd master one.
# See: https://docs.mem0.ai/open-source/features/custom-fact-extraction-prompt
with open('prompts/fact_extract_2.txt', 'r') as f:
    CUSTOM_FACT_EXTRACTION_PROMPT = f.read()

with open('prompts/agent_personality_2.txt', 'r',encoding="utf-8") as f:
    AGENT_PERSONALITY = f.read()

with open('prompts/function_guide.txt', 'r') as f:
    DND_FUNCTION = f.read()

with open('prompts/conversation.txt', 'r',encoding="utf-8") as f:
    CONVERSATION = f.read()
 
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

def dnd_guide():
    """
    Create a compact master guide from already loaded files.
    """
    master_parts = []
    
    # 1. Core Personality
    master_parts.append("=== ELARA MYSTARA - THE WHISPERING GUIDE ===")
    if AGENT_PERSONALITY:
        master_parts.append(AGENT_PERSONALITY[:1500])
    
    # 2. Conversation Guidelines (already loaded as CONVERSATION)
    if CONVERSATION:
        master_parts.append("\n=== CONVERSATION GUIDELINES ===")
        master_parts.append(CONVERSATION[:800])
    
    # 3. Function Calling (already loaded as DND_FUNCTION)
    if DND_FUNCTION:
        master_parts.append("\n=== FUNCTION CALLING RULES ===")
        master_parts.append(DND_FUNCTION[:800])
    
    # 4. Key World Facts
    try:
        key_files = ['world_history', 'world_factions', 'terminology']
        for file in key_files:
            filepath = f'prompts/world_context/{file}.txt'
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    master_parts.append(f"\n=== {file.upper().replace('_', ' ')} ===")
                    master_parts.append(content[:500])
    except:
        pass
    
    # 5. Elara's Core Rules
    master_parts.append("\n=== ELARA'S CORE RULES ===")
    master_parts.append("""
    1. YES, AND / YES, BUT / ROLL FOR IT
    2. FAIL FORWARD - Complications, not dead ends
    3. SHOW, DON'T TELL - Describe results
    4. MAINTAIN MYSTERY
    5. WEAVE MECHANICS - Functions for game rules
    """)
    
    return "\n".join(master_parts)

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

    ]
    
    contexts = {}
    for file in context_files:
        try:
            with open(f'prompts/world_context/{file}', 'r',encoding="utf-8") as f:
                contexts[file.replace('.txt', '')] = f.read()
        except FileNotFoundError:
            print(f"Warning: {file} not found, skipping...")
            contexts[file.replace('.txt', '')] = ""
    
    return contexts

def load_world_rules():
    """Load all world rulesfiles"""
    context_files = [
        'dnd_function.txt',
        'dnd_master_tools.txt',
        'combat.txt',
        'loot.txt',
        'chac_creation.txt',
    ]
    
    contexts = {}
    for file in context_files:
        try:
            with open(f'prompts/world_context/{file}', 'r',encoding="utf-8") as f:
                contexts[file.replace('.txt', '')] = f.read()
        except FileNotFoundError:
            print(f"Warning: {file} not found, skipping...")
            contexts[file.replace('.txt', '')] = ""
    
    return contexts

def initialize_world_memory(world_user_id: str, max_chunk_size: int = 2000):
    """Load world context under SEPARATE user ID"""
  
    existing = m.search(query="", user_id=world_user_id, limit=1)
    if existing.get("results"):
        print(f"World already loaded in '{world_user_id}'")
        return []
    
    print(f"Loading world...")

    world = load_world_context()
    rules = load_world_rules()
    added_chunks = []
    total_chars = 0

    total_files = len([c for c in world.values() if c]) + len([c for c in rules.values() if c])
    print(f"   Found {total_files} Datasets to load")
    
    try:
        master_guide = dnd_guide()
        # Store under WORLD user ID
        m.add([{"role": "system", "content": master_guide}], 
              user_id=world_user_id,  # ← world_eorzea, not player_01
            )  # Skip fact extraction for speed
        print(f"Added Master Guide to {world_user_id} ({len(master_guide)} chars)")
        added_chunks.append("Master Guide")
        total_chars += len(master_guide)
    except Exception as e:
        print(f"Could not add Master Guide: {e}")
    
    # ==================== LOAD WORLD CONTENT ====================
    print("\n Loading world content (history, factions, cities)...")
    for key, content in world.items():
        if not content or len(content.strip()) == 0:
            continue
            
        section_title = f"=== {key.replace('_', ' ').title()} ===\n"
        
        if len(content) <= max_chunk_size:
            chunk = section_title + content
            try:
                m.add([{"role": "system", "content": chunk}], 
                      user_id=world_user_id)
                added_chunks.append(chunk)
                total_chars += len(chunk)
                print(f"Loaded Dataset: {key} ({len(content)} chars)")
            except Exception as e:
                print(f"Failed Dataset: {key}: {e}")
        else:
            content_chunks = split_content(content, max_chunk_size)
            for i, content_chunk in enumerate(content_chunks):
                chunk = section_title if i == 0 else ""
                chunk += content_chunk
                if i < len(content_chunks) - 1:
                    chunk += "\n[continued...]"
                    
                try:
                    m.add([{"role": "system", "content": chunk}], 
                          user_id=world_user_id)
                    added_chunks.append(chunk)
                    total_chars += len(chunk)
                    print(f"Loaded Dataset: {key} part {i+1}")
                except Exception as e:
                    print(f"Failed Dataset: {key} part {i+1}: {e}")
    
    # ==================== LOAD WORLD RULES ====================
    print("\n Loading world rules (combat, loot, magic)...")
    for key, content in rules.items():
        if not content or len(content.strip()) == 0:
            continue
            
        # Add prefix to identify as rules (reduces fact extraction attempts)
        section_title = f"=== GAME RULES: {key.replace('_', ' ').title()} ===\n"
        
        if len(content) <= max_chunk_size:
            chunk = section_title + content
            try:
                m.add([{"role": "system", "content": chunk}], 
                      user_id=world_user_id)
                added_chunks.append(chunk)
                total_chars += len(chunk)
                print(f"Loaded Dataset: {key} ({len(content)} chars)")
            except Exception as e:
                print(f"Failed Dataset: {key}: {e}")
        else:
            content_chunks = split_content(content, max_chunk_size)
            for i, content_chunk in enumerate(content_chunks):
                chunk = section_title if i == 0 else ""
                chunk += content_chunk
                if i < len(content_chunks) - 1:
                    chunk += "\n[continued...]"
                    
                try:
                    m.add([{"role": "system", "content": chunk}], 
                          user_id=world_user_id)
                    added_chunks.append(chunk)
                    total_chars += len(chunk)
                    print(f"Loaded Dataset: {key} part {i+1}")
                except Exception as e:
                    print(f"Failed Dataset: {key} part {i+1}: {e}")
    
    print(f"\n Loaded {len(added_chunks)} total chunks to {world_user_id} ({total_chars} chars)")
    return added_chunks

def split_content(content: str, chunk_size: int):
    """Split content intelligently at paragraph boundaries"""
    if not content:
        return []
    
    content = content.replace('\x00', '').strip()
    
    paragraphs = content.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # If adding this paragraph would exceed chunk size, save current chunk
        if len(current_chunk) + len(para) + 2 > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
        else:
            current_chunk += para + "\n\n"
    
    # Add the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def check_world_loaded():
    """Check if world context is already loaded in memory"""
    try:
        # Try to search for something world-related
        test_search = m.search(query="Eorzea", user_id=WORLD_USER_ID, limit=1)
        if test_search.get("results") and len(test_search["results"]) > 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"⚠ Error checking dataset: {e}")
        return False


def agent_workflow(user_input: str, player_user_id: str):
    print(f"\n[User Input]: {user_input}")

    # -------------------------------------------------
    # 1. Retrieval & World Status Check
    # -------------------------------------------------
    # use mem0 to get history context and world state, instead of the entire conversation
    # search_results = m.search(query=user_input, user_id=player_user_id, limit=15)

    # 解析检索结果
    history_context = ""
    world_status = ""
    world_context = ""
    # Search WORLD knowledge (world_master user)
    world_results = m.search(
        query=user_input, 
        user_id=WORLD_USER_ID,  # ← Fixed world ID
        limit=5
    )
    
    # Search PLAYER conversation (player_01 user)
    player_results = m.search(
        query=user_input, 
        user_id=player_user_id,  # ← Player's ID
        limit=10
    )

    # Parse WORLD results
    world_context = ""
    if "results" in world_results:
        for item in world_results["results"]:
            memory_text = item.get("memory", "")
            if memory_text:
                world_context += memory_text + "\n"

    # Parse PLAYER conversation results
    history_context = ""
    if "results" in player_results:
        for item in player_results["results"]:
            memory_text = item.get("memory", "")
            if memory_text:
                history_context += memory_text + "\n"
        # Get world status from player's graph relationships
    if "relations" in player_results:
        world_status = "\n".join([f"{r}" for r in player_results["relations"]])
        print(f"[World Status Relations Found]: {len(player_results['relations'])}")
    else:
        world_status = "No relations found yet."
        print("[World Status]: No relations yet")

    # if "results" in search_results:  # Vector database query result (History Mem)
    #     # Separate world context from conversation history
    #     for item in search_results["results"]:
    #         memory_text = item.get("memory", "")
    #         if "=== EORZEA WORLD CONTEXT ===" in memory_text:
    #             world_context = memory_text
    #         else:
    #             history_context += memory_text + "\n"

    # if "relations" in search_results:  # Graph database query result (World Status)
    #     # 例如：Player -- location --> Room A
    #     world_status = "\n".join(
    #         [f"{r}" for r in search_results["relations"]])
    
    function_help = DND_FUNCTION[:300] if DND_FUNCTION else ""
    conversation_help = CONVERSATION[:300] if CONVERSATION else ""

    print(f"[History]: {history_context}")
    print(f"[Current World Status]: {world_status}")

    # -------------------------------------------------
    # 2. Personality Processing
    # -------------------------------------------------
    # Construct the prompt

    full_prompt = f"""
    {AGENT_PERSONALITY}

    === World Function ===
    {function_help}

    === World Conmmunication ===
    {conversation_help}

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
    m.add(messages, user_id=player_user_id)
    
    print(f"[Agent Output]: {agent_output}")
    return agent_output

if __name__ == '__main__':
    print("=" * 60)
    print("ELARA MYSTARA - EORZEA")
    print("=" * 60)
    
    # Check if world is already loaded
    print("\n[DEBUG] Checking if world knowledge is already loaded...")
    is_loaded = check_world_loaded()
    print(f"[DEBUG] is_loaded = {is_loaded}")
    
    if is_loaded:
        print("✓ World knowledge already loaded (skipping)")
    else:
        print("✗ World knowledge not found, loading for the first time...")
        initialize_world_memory(WORLD_USER_ID)  # ← Load to world_eorzea
    
    # Clear ONLY player conversation (world stays intact)
    print(f"\n Starting new session for {PLAYER_USER_ID}...")
    m.delete_all(user_id=PLAYER_USER_ID)  # Only clears player chat
    
    # Play!
    print("\n" + "=" * 60)
    print("GAME START")
    print("=" * 60)
    agent_workflow("I enter a dark room, finding a rusty key on the floor.", PLAYER_USER_ID)
    agent_workflow("I pick up the key.", PLAYER_USER_ID)
    agent_workflow("What do I have?", PLAYER_USER_ID)