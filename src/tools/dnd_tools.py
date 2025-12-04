# D&D Agent 工具调用配置（完全匹配 GET_WEATHER 模板格式）
DnD_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "roll_dice",
            "description": "Simulate rolling a d10 dice for D&D game. "
                           "In normal case, you can decide the progress of adventure based on the result. "
                           "In attack/defense case, you can add modifier for attack/defense judgment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "modifier": {
                        "type": "integer",
                        "description": "Modifier value for dice roll "
                                       "(can be positive/negative, e.g. attack modifier +2, dim light -1).",
                        "default": 0
                    },
                    "roll_purpose": {
                        "type": "string",
                        "description": "Description of the purpose of rolling dice for record.",
                        "default": "active_roll"
                    },
                    "related_entity": {
                        "type": "string",
                        "description": "ID of related entity (e.g. Player_01, Goblin_01) for record.",
                        "default": ""
                    }
                },
                "required": [],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "attack",
            "description": "Execute attack judgment and damage calculation in D&D game, "
                           "need attacker and target entity ID first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "attacker_id": {
                        "type": "string",
                        "description": "ID of attacker entity (e.g. Player_01, Goblin_01).",
                    },
                    "target_id": {
                        "type": "string",
                        "description": "ID of target entity (e.g. Goblin_01, Player_01).",
                    },
                    "attack_modifier": {
                        "type": "integer",
                        "description": "Additional attack modifier "
                                       "(priority over entity's default modifier, e.g. skill bonus +1).",
                        "default": 0
                    },
                    "damage_range": {
                        "type": "array",
                        "items": {
                            "type": "integer"
                        },
                        "description": "Range of damage value (default [1,4] in MVP version).",
                        "default": [1, 4]
                    }
                },
                "required": ["attacker_id", "target_id"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "defense",
            "description": "Execute defense judgment for entity in D&D game, "
                           "need defender entity ID first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "defender_id": {
                        "type": "string",
                        "description": "ID of defender entity (e.g. Player_01, Goblin_01).",
                    },
                    "defense_modifier": {
                        "type": "integer",
                        "description": "Additional defense modifier "
                                       "(e.g. equipment bonus +1, environment reduction -1).",
                        "default": 0
                    },
                    "defense_purpose": {
                        "type": "string",
                        "description": "Purpose of defense, optional values: 'normal_attack', 'counter_attack'.",
                        "default": "normal_attack"
                    }
                },
                "required": ["defender_id"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "status_query",
            "description": "Query core status of entity in D&D game (HP, attack/defense modifier, survival status).",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_id": {
                        "type": "string",
                        "description": "ID of target entity (leave empty to query all alive entities).",
                        "default": ""
                    },
                    "query_type": {
                        "type": "string",
                        "description": "Type of query, optional values: "
                                       "'single' (query single entity), "
                                       "'all_alive' (query all alive entities).",
                        "default": ""
                    }
                },
                "required": [],  # 无强制必填参数（自动推断查询类型）
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_entity",
            "description": "Create player/creature entity in D&D game with standardized attributes, "
                           "generate unique ID automatically if not specified.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_name": {
                        "type": "string",
                        "description": "Name of entity (e.g. Adventurer, Goblin Scout).",
                    },
                    "entity_type": {
                        "type": "string",
                        "description": "Type of entity, optional values: 'player', 'creature'.",
                    },
                    "hp_max": {
                        "type": "integer",
                        "description": "Max HP of entity (override default value if specified).",
                        "default": 0
                    },
                    "attack_modifier": {
                        "type": "integer",
                        "description": "Attack modifier of entity (override default value if specified).",
                        "default": 0
                    },
                    "defense_modifier": {
                        "type": "integer",
                        "description": "Defense modifier of entity (override default value if specified).",
                        "default": 0
                    },
                    "custom_id": {
                        "type": "string",
                        "description": "Custom unique ID for entity (auto-generate if empty).",
                        "default": ""
                    }
                },
                "required": ["entity_name", "entity_type"],
            },
        }
    }
]