# D&D AI Game Master

An AI-powered Dungeons & Dragons assistant that integrates memory systems with game mechanics to create persistent AI game masters.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Mem0](https://img.shields.io/badge/Memory-mem0ai-008CC1?style=for-the-badge)
![Local LLM](https://img.shields.io/badge/LLM-Local_Models-FF6B6B?style=for-the-badge)

## Features

* **Persistent Memory:** Custom memory implementations for consistent AI personalities across sessions
* **D&D Mechanics Integration:** Function calling for dice rolls, combat, and game state management
* **Local & Private:** All data stored locally with no external API dependencies
* **Multiple Experimental Implementations:** Various approaches to AI memory and game integration

## Tech Stack

* **Core Framework:** Python 3.12+
* **Memory Management:** mem0ai (customized local implementation)
* **Large Language Model:** Ollama with Qwen3:8B (local deployment)
* **Vector Database:** ChromaDB for semantic memory storage
* **Graph Database:** Neo4j for relationship and world-state tracking
* **Embedding Model:** Sentence Transformers (`multi-qa-MiniLM-L6-cos-v1`)
* **Prompt Engineering:** Structured templates for world-building and character consistency
* **API Interface:** OpenAI-compatible Ollama API wrapper




## System Architecture

A layered architecture supporting AI-driven Dungeons & Dragons gameplay:
- **Memory Layer:** mem0ai framework with ChromaDB vector storage for persistent character memory and world knowledge
- **AI Engine:** Ollama with Qwen3:8B model for narrative generation, enhanced with custom prompt templates for D&D-specific storytelling
- **Game Mechanics Layer:** Deterministic Python function calls for D&D rule enforcement (dice rolls, combat, character stats)
- **Persistence:** Dual storage system with ChromaDB for semantic memory and Neo4j for entity relationship graphs
- **Interface Layer:** Python-based conversation handler with tool-calling integration for dynamic gameplay

## Installation & Usage

### Prerequisites
Python=3.12
torch
Chromadb # as database backend
mem0ai # as memory layer
mem0ai[graph] (not using for now)
neo4j # as graph database backend (not using for now)

### Installation
* Clone the repository and install dependencies:
```bash
git clone https://github.com/chungs10/fire-suppression-line-verifier.git
cd fire-suppression-line-verifier
pip install -r requirements.txt
```

* Setup the neo4j with docker. [official document](https://neo4j.com/docs/operations-manual/current/docker/introduction/)
```bash
docker run \
    -p 7474:7474 -p 7687:7687 \
    --name neo4j-apoc \
    -e NEO4J_apoc_export_file_enabled=true \
    -e NEO4J_apoc_import_file_enabled=true \
    -e NEO4J_apoc_import_file_use__neo4j__config=true \
    -e NEO4J_PLUGINS=\[\"apoc\"\] \
    -e NEO4J_AUTH=neo4j/12345678 \
    neo4j:latest
```

* Install the Ollama model
```bash
ollama pull qwen3:8b
```


### Run the application:
1. Start the dependents
```bash
docker start neo4j
sudo systemctl start ollama
```

2. Start the application:
Use this for dungeon master
```bash
python try_mem0_dnd_eoz.py
```
Use this for dungeon master functions
```bash
python try_mem0_dnd_eoz_function.py
```

3. Access Neo4j for graph relationships
	Navigate to http://localhost:7474 and login using following credentials
	URL: neo4j://localhost:7687
	Username:neo4j
	Password:12345678


## Project Structure
```plaintext
dnd-ai/
├── LICENSE
├── README.md
├── requirements.txt
├── dnd-ai-env/
│ ├── README.md
│ ├── bin/
│ ├── include/
│ ├── lib/
│ ├── lib64 -> lib
│ ├── pyvenv.cfg
│ └── share/
├── models/
│ └── LLM/
├── src/
│ ├── check.py
│ ├── test.py
│ ├── tmp.py
│ ├── try_mem0.py
│ ├── try_mem0_dnd.py
│ ├── try_mem0_dnd_eoz.py
│ ├── try_mem0_dnd_eoz_function.py
│ ├── db/
│ ├── prompts/
│ ├── simpleMemory/
│ └── tools/
└── thirdparty/
└── mem0/
```plaintext

## Team & Contributions

This project was developed as part of a **school research project** exploring AI memory systems and game integration. It was a collaborative effort between two students.

**Student A (My Role):**
* **Prompt Engineering & World Building:** Designed and implemented the prompt loading system for AI personality, world context, and game rules
* **Database Integration:** Configured ChromaDB vector storage and ensured proper database detection and initialization

**Student B (Teammate):**
* **Function Creation:** Developed the D&D game mechanics functions (dice rolling, combat, character management)
* **Technology Integration:** Integrated Ollama, mem0ai, and other core technologies into a cohesive system
* **Tool Calling Implementation:** Built the function calling infrastructure for AI-triggered game actions


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Notes
* **Model Requirements:** The Qwen3:8B model must be downloaded separately via Ollama (`ollama pull qwen3:8b`) due to size constraints
* **Database Storage:** ChromaDB vector database files are stored locally in the `db/` directory
* **Memory Initialization:** World context only needs to be loaded once - subsequent runs will detect and use existing memory
* **Experimental Status:** This is a research project exploring AI memory systems - architecture and features may evolve
* **Local Development:** Designed for offline use with local LLMs; no external API dependencies required
* **Disclaimer:** Not affiliated with Wizards of the Coast or official Dungeons & Dragons franchise

### AI-Assisted Development
* **Development Support:** AI assisted with code debugging, generated specific functions (including text chunking algorithms), helped refine prompt templates, and provided coding guidance through questions about implementation approaches
* **Documentation Aid:** AI supported the creation of technical documentation
* **Human Direction:** All system architecture, design decisions, and final implementations were made by human developers