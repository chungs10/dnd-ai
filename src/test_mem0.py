import os
from openai import OpenAI
from mem0 import Memory

os.environ["OPENAI_API_KEY"] = "api"
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
MODEL_NAME = "capybarahermes"

memory_config = {
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
        "provider": "ollama",
        "config": {
            "model": f"{MODEL_NAME}",
            "temperature": 0.1,
            "max_tokens": 2000,
            "ollama_base_url": "http://127.0.0.1:11434"
        }
    }
}

openai_client = OpenAI(
    base_url='http://127.0.0.1:11434/v1'
)
m = Memory.from_config(memory_config)

def chat_with_memories(message: str, user_id: str = "default_user") -> str:
    # Retrieve relevant memories
    relevant_memories = m.search(query=message, user_id=user_id, limit=3)
    memories_str = "\n".join(f"- {entry['memory']}" for entry in relevant_memories["results"])

    # Generate Assistant response
    system_prompt = f"You are a helpful AI. Answer the question based on query and memories.\nUser Memories:\n{memories_str}"
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}]
    response = openai_client.chat.completions.create(model=MODEL_NAME, messages=messages)
    assistant_response = response.choices[0].message.content

    # Create new memories from the conversation
    messages.append({"role": "assistant", "content": assistant_response})
    m.add(messages, user_id=user_id)

    return assistant_response

def main():
    print("Chat with AI (type 'exit' to quit)")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        print(f"AI: {chat_with_memories(user_input)}")

if __name__ == "__main__":
    main()