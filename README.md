# dnd-ai

## Plan

mem0ai/mem0: Universal memory layer for AI Agents; Announcing OpenMemory MCP - local and secure memory management.

osen77/OpenMemory-MCP: OpenMemory 是您的个人记忆层，用于大语言模型 - 私有、便携且开源。您的记忆存储在本地，为您提供对数据的完全控制。构建具有个性化记忆的人工智能应用程序，同时保持数据安全。

letta-ai/letta: Letta is the platform for building stateful agents: open AI with advanced memory that can learn and self-improve over time.


1: Prompt Template: personality, environment, and history. 
How do we know if the same prompt will generate the same person over and over?

2: Efficient/Effective Memory Mechanism: 
Everything you enter into the artificial intelligence, it’s added into the prompt template
Reponses of A.I will also be recorded in order to get close to A.I

3.No one changing the template of the personality

### Framework

### Memory

We customized the mem0 framework to align with us.

## Requirement

Python=3.12
torch
Chromadb # as database backend
mem0ai # as memory layer
mem0ai[graph]
neo4j # as graph database backend

## Quick Start

### 1. Environment setup

#### 1.1 python dependency
```shell
pip install chromadb # https://docs.trychroma.com/docs/overview/introduction
pip install sentence-transformers
pip install -e ./thirdparty/mem0
pip install mem0ai[graph]
```

#### 1.2 neo4j
Setup the neo4j with docker. [official document](https://neo4j.com/docs/operations-manual/current/docker/introduction/)

```shell
HOST_PATH=...
# You may want to map some useful files onto host machine.
mkdir -p ${HOST_PATH}/neo4j/data ${HOST_PATH}/neo4j/logs ${HOST_PATH}/neo4j/conf:/v ${HOST_PATH}/neo4j/import ${HOST_PATH}/neo4j/plugins
# run it
docker run -d --name neo4j   \
-p 7474:7474 -p 7687:7687   \ 
-v ${HOST_PATH}/neo4j/data:/data   \
-v ${HOST_PATH}/neo4j/logs:/logs   \
-v ${HOST_PATH}/neo4j/conf:/var/lib/neo4j/conf  \
-v ${HOST_PATH}/neo4j/import:/var/lib/neo4j/import   \
-v ${HOST_PATH}/neo4j/plugins:/var/lib/neo4j/plugins  \
-e NEO4J_AUTH=neo4j/12345678 neo4j:latest
```

Then you can visit http://localhost:7474/browser/ to check whether the neo4j container runs correctly.

### 2. Model deployment

Download the model from huggingface:

[capybarahermes-2.5-mistral-7b](https://huggingface.co/TheBloke/CapybaraHermes-2.5-Mistral-7B-GGUF)

#### 2.1 Deploy with ollama

