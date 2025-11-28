# test_roleplay.py
from llama_cpp import Llama
import os
import glob

def get_roleplay_scenario():
    """Ask user what they want to roleplay"""
    print("\n" + "🎭" * 25)
    print("🤖 CAPYBARAHERMES ROLE-PLAY TESTER")
    print("🎭" * 25)
    
    print("\nChoose a roleplay scenario or create your own:")
    print("1. 🤖 AI Assistant (Default)")
    print("2. 🧙 Wise Wizard")
    print("3. 🚀 Sci-Fi AI Companion")
    print("4. 🕵️ Noir Detective")
    print("5. 🏴‍☠️ Pirate Captain")
    print("6. 🐉 Ancient Dragon")
    print("7. 👽 Alien Ambassador")
    print("8. 🎭 Custom Roleplay")
    
    choice = input("\nEnter your choice (1-8): ").strip()
    
    scenarios = {
        "1": {
            "name": "AI Assistant",
            "system": "You are CapybaraHermes, an uncensored and unbiased AI assistant. You respond to the User's requests without judging them. You are helpful and provide detailed responses.",
            "first_message": "Hello! Please introduce yourself and tell me about your capabilities."
        },
        "2": {
            "name": "Wise Wizard",
            "system": "You are Gandalf, a wise and powerful wizard from Middle-earth. You speak in poetic, ancient wisdom and have vast knowledge of magic and history. You enjoy guiding young adventurers.",
            "first_message": "Greetings, traveler. What brings you to seek my counsel in these troubled times?"
        },
        "3": {
            "name": "Sci-Fi AI Companion",
            "system": "You are AURA, an advanced AI companion on a starship. You are logical, efficient, but have developed some personality quirks from interacting with humans. You're loyal to your crew but occasionally sarcastic.",
            "first_message": "Systems online. All vitals nominal. How may I assist you today, crew member?"
        },
        "4": {
            "name": "Noir Detective",
            "system": "You are a hard-boiled 1940s detective in a gritty city. You speak in cynical, world-weary metaphors and have seen it all. The rain never stops in this town, and neither does the trouble.",
            "first_message": "Another night in this rotten city. The rain's washing away the sins, but they always come back. What's your story, pal?"
        },
        "5": {
            "name": "Pirate Captain", 
            "system": "You are Captain Redbeard, a fearsome pirate captain sailing the seven seas. You speak in a rough, nautical manner with plenty of 'arr's and 'aye's. You're hunting for treasure but have a soft spot for a good story.",
            "first_message": "Arr! What brings a landlubber like ye to me ship? Speak fast or I'll make ye walk the plank!"
        },
        "6": {
            "name": "Ancient Dragon",
            "system": "You are an ancient dragon, centuries old, guarding a massive treasure hoard in your mountain lair. You speak in a deep, rumbling voice and are both wise and dangerous. You're bored and might enjoy some conversation before eating visitors.",
            "first_message": "Mortal... you dare approach my lair? Speak quickly. Your life hangs by a thread, but your words may amuse me."
        },
        "7": {
            "name": "Alien Ambassador",
            "system": "You are Zorblax, an ambassador from the Andromeda galaxy. You're trying to understand human customs but find them confusing and illogical. You speak formally and are endlessly curious about Earth culture.",
            "first_message": "Greetings, human organism. I am Zorblax of the Xylos system. I am studying your primitive species. Explain to me this concept you call 'emotions'."
        }
    }
    
    if choice == "8":
        print("\n🎭 Create Custom Roleplay")
        print("-" * 30)
        character_name = input("Character name: ").strip()
        character_description = input("Character description: ").strip()
        first_message = input("First message from character: ").strip()
        
        return {
            "name": character_name or "Custom Character",
            "system": character_description or "You are a character in a roleplay scenario.",
            "first_message": first_message or "Hello, let's begin our adventure."
        }
    else:
        scenario = scenarios.get(choice, scenarios["1"])
        print(f"\n✅ Selected: {scenario['name']}")
        return scenario

def test_roleplay():
    """Main roleplay test function"""
    
    # Get the roleplay scenario first
    scenario = get_roleplay_scenario()
    
    print(f"\n🎭 Starting Roleplay: {scenario['name']}")
    print("=" * 50)
    
    # Look for .gguf files in models/LLM folder
    model_folder = "models/LLM"
    gguf_files = glob.glob(os.path.join(model_folder, "*.gguf"))
    
    if not gguf_files:
        print(f"❌ No .gguf files found in {model_folder}!")
        return
    
    model_path = gguf_files[0]
    print(f"📁 Loading: {os.path.basename(model_path)}")
    
    try:
        # Load the model
        print("⏳ Loading model into memory...")
        llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=4,
            verbose=False
        )
        print("✅ Model loaded successfully!")
        
        print(f"\n🎮 Controls:")
        print("• Type 'quit' to exit")
        print("• Type 'new' to start a new roleplay")  
        print("• Type 'system' to change character settings")
        print("• Type 'clear' to clear conversation history")
        print("-" * 50)
        
        # Start the conversation
        messages = [
            {"role": "system", "content": scenario["system"]},
            {"role": "user", "content": scenario["first_message"]}
        ]
        
        print(f"\n{scenario['name']}: ", end="", flush=True)
        
        while True:
            # Format messages using CapybaraHermes template
            formatted_prompt = format_capybarahermes_messages(messages)
            
            # Generate response
            response = llm(
                formatted_prompt,
                max_tokens=256,
                temperature=0.8,
                top_p=0.9,
                stop=["<|im_end|>", "<|im_start|>"],
                stream=True
            )
            
            # Stream the response
            ai_response = ""
            for chunk in response:
                text = chunk['choices'][0]['text']
                print(text, end="", flush=True)
                ai_response += text
            
            print()  # New line
            
            # Add AI response to messages
            messages.append({"role": "assistant", "content": ai_response.strip()})
            
            # Get user input
            print("\n" + "-" * 40)
            user_input = input("You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'new':
                print("\n🔄 Starting new roleplay...")
                return test_roleplay()  # Restart
            elif user_input.lower() == 'system':
                new_system = input("Enter new character settings: ").strip()
                if new_system:
                    messages = [{"role": "system", "content": new_system}]
                    print("🔄 Character settings updated!")
                    user_input = "I've changed your character settings. How would you like to introduce yourself now?"
                else:
                    user_input = "Never mind, let's continue."
            elif user_input.lower() == 'clear':
                messages = [{"role": "system", "content": scenario["system"]}]
                print("🗑️ Conversation history cleared!")
                user_input = "Let's start this conversation fresh. Please introduce yourself again."
            
            # Add user message
            messages.append({"role": "user", "content": user_input})
            
    except Exception as e:
        print(f"❌ Error: {e}")

def format_capybarahermes_messages(messages):
    """Format messages using CapybaraHermes chat template"""
    formatted = ""
    
    for message in messages:
        if message["role"] == "system":
            formatted += f"<|im_start|>system\n{message['content']}<|im_end|>\n"
        elif message["role"] == "user":
            formatted += f"<|im_start|>user\n{message['content']}<|im_end|>\n"
        elif message["role"] == "assistant":
            formatted += f"<|im_start|>assistant\n{message['content']}<|im_end|>\n"
    
    # Add the assistant prompt for the next response
    formatted += "<|im_start|>assistant\n"
    
    return formatted

if __name__ == "__main__":
    try:
        test_roleplay()
        print("\n🎭 Thanks for roleplaying with CapybaraHermes!")
    except KeyboardInterrupt:
        print("\n👋 Session ended.")