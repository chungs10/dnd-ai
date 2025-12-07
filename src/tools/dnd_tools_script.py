import random
from enum import Enum
from typing import Dict, List, Optional, Any

entity_store: Dict[str, Dict[str, Any]] = {
    "Player_01": {
        "name": "Adventurer",
        "hp_current": 10,
        "hp_max": 10,
        "attack_modifier": 2,
        "defense_modifier": 1,
        "status": "alive"  # alive/dead
    },
}


class EntityType(Enum):
    PLAYER = "player"
    CREATURE = "creature"


DEFAULT_ATTRIBUTES = {
    EntityType.PLAYER: {
        "hp_max": 10,
        "attack_modifier": 2,
        "defense_modifier": 1,
        "status": "alive"
    },
    EntityType.CREATURE: {
        "hp_max_range": [5, 8],  # Creature max HP random range
        "attack_modifier_range": [0, 1],  # Creature attack modifier random range
        "defense_modifier_range": [0, 1],  # Creature defense modifier random range
        "status": "alive"
    }
}

def create_entity(
        entity_name: str,
        entity_type: EntityType,
        hp_max: Optional[int] = None,
        attack_modifier: Optional[int] = None,
        defense_modifier: Optional[int] = None,
        custom_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a D&D entity (player/creature), generate a unique ID, fill in default attributes, and support custom attribute overrides
    :param entity_name: Entity name (e.g., "Adventurer", "Goblin")
    :param entity_type: Entity type (EntityType.PLAYER/EntityType.CREATURE)
    :param hp_max: Maximum HP (optional, overrides default value)
    :param attack_modifier: Attack modifier (optional, overrides default value)
    :param defense_modifier: Defense modifier (optional, overrides default value)
    :param custom_id: Custom entity ID (optional, defaults to auto-generated)
    :return: Entity creation result dictionary
    """
    # Initialize return result
    result = {
        "success": False,
        "error_msg": "",
        "entity_id": "",
        "entity_data": {}
    }

    # 1. Basic parameter validation
    if not entity_name.strip():
        result["error_msg"] = "Entity name cannot be empty"
        return result
    if not isinstance(entity_type, EntityType):
        result["error_msg"] = f"Entity type must be an EntityType enum value ({[e.value for e in EntityType]})"
        return result

    # 2. Generate a unique entity ID
    if custom_id:
        # Custom ID must be checked for uniqueness
        if custom_id in entity_store:
            result["error_msg"] = f"Custom ID {custom_id} already exists and cannot be created"
            return result
        entity_id = custom_id
    else:
        # Auto-generate ID: Type prefix + sequence number (e.g., Player_01, Creature_02)
        type_prefix = entity_type.value.capitalize()
        # Count the number of existing entities of this type to generate an incremental sequence number
        existing_count = len([
            eid for eid in entity_store.keys()
            if eid.startswith(f"{type_prefix}_")
        ])
        entity_id = f"{type_prefix}_{str(existing_count + 1).zfill(2)}"  # Zero-pad to ensure uniform format (01/02/03)

    # 3. Populate entity attributes
    entity_data = {"name": entity_name.strip()}

    # Player entity attribute logic
    if entity_type == EntityType.PLAYER:
        entity_data["hp_max"] = hp_max if hp_max is not None else DEFAULT_ATTRIBUTES[EntityType.PLAYER]["hp_max"]
        entity_data["attack_modifier"] = attack_modifier if attack_modifier is not None else \
            DEFAULT_ATTRIBUTES[EntityType.PLAYER]["attack_modifier"]
        entity_data["defense_modifier"] = defense_modifier if defense_modifier is not None else \
            DEFAULT_ATTRIBUTES[EntityType.PLAYER]["defense_modifier"]
        entity_data["status"] = DEFAULT_ATTRIBUTES[EntityType.PLAYER]["status"]

    # Creature entity attribute logic (supports random ranges)
    elif entity_type == EntityType.CREATURE:
        entity_data["hp_max"] = hp_max if hp_max is not None else random.randint(
            DEFAULT_ATTRIBUTES[EntityType.CREATURE]["hp_max_range"][0],
            DEFAULT_ATTRIBUTES[EntityType.CREATURE]["hp_max_range"][1]
        )
        entity_data["attack_modifier"] = attack_modifier if attack_modifier is not None else random.randint(
            DEFAULT_ATTRIBUTES[EntityType.CREATURE]["attack_modifier_range"][0],
            DEFAULT_ATTRIBUTES[EntityType.CREATURE]["attack_modifier_range"][1]
        )
        entity_data["defense_modifier"] = defense_modifier if defense_modifier is not None else random.randint(
            DEFAULT_ATTRIBUTES[EntityType.CREATURE]["defense_modifier_range"][0],
            DEFAULT_ATTRIBUTES[EntityType.CREATURE]["defense_modifier_range"][1]
        )
        entity_data["status"] = DEFAULT_ATTRIBUTES[EntityType.CREATURE]["status"]

    # 4. Validate attribute legality
    if entity_data["hp_max"] <= 0:
        result["error_msg"] = "Maximum HP must be greater than 0"
        return result
    if not isinstance(entity_data["attack_modifier"], int):
        result["error_msg"] = "Attack modifier must be an integer"
        return result
    if not isinstance(entity_data["defense_modifier"], int):
        result["error_msg"] = "Defense modifier must be an integer"
        return result

    # 5. Initialize current HP (default equals maximum HP)
    entity_data["hp_current"] = entity_data["hp_max"]

    # 6. Store in the entity storage center
    entity_store[entity_id] = entity_data

    # 7. Assemble return result
    result["success"] = True
    result["entity_id"] = entity_id
    result["entity_data"] = entity_data
    result["error_msg"] = ""

    return result


# def update_entity(
#     entity_id: str,
#     update_description: Optional[str] = None,
#     name: Optional[str] = None,
#     hp_current: Optional[int] = None,
#     hp_max: Optional[int] = None,
#     status: Optional[str] = None,
# ) -> Dict[str, Any]:
#     """
#     Update any mutable field of an existing entity.
#
#     Parameters
#     ----------
#     entity_id : str
#         The ID of the entity to update.
#     update_description : str, optional
#         Describe the update reasons and details.
#     hp_current : int, optional
#         New current HP (will be clamped to 0..hp_max).
#     hp_max : int, optional
#         New maximum HP.  If this is lowered below the current HP,
#         current HP is clamped to the new maximum.
#     status : {"alive", "dead"}, optional
#         New status string.
#
#     Returns
#     -------
#     dict
#         {
#             "success": bool,
#             "error_msg": str,
#             "entity_id": str,
#             "entity_data": dict   # updated entity snapshot
#         }
#     """
#     result = {
#         "success": False,
#         "update_description": update_description,
#         "error_msg": "",
#         "entity_id": entity_id,
#         "entity_data": {}
#     }
#
#     # 1. Entity existence check
#     if entity_id not in entity_store:
#         result["error_msg"] = f"Entity {entity_id} does not exist"
#         return result
#
#     ent = entity_store[entity_id]  # live reference
#
#     # 2. Validate and apply each supplied field
#     if name is not None:
#         if not str(name).strip():
#             result["error_msg"] = "Name cannot be empty"
#             return result
#         ent["name"] = str(name).strip()
#
#     if hp_max is not None:
#         if hp_max <= 0:
#             result["error_msg"] = "hp_max must be greater than 0"
#             return result
#         ent["hp_max"] = int(hp_max)
#         # Clamp current HP to new maximum
#         ent["hp_current"] = min(ent["hp_current"], ent["hp_max"])
#
#     if hp_current is not None:
#         hp = int(hp_current)
#         if hp < 0:
#             result["error_msg"] = "hp_current cannot be negative"
#             return result
#         ent["hp_current"] = min(hp, ent["hp_max"])
#
#     if status is not None:
#         if status not in {"alive", "dead"}:
#             result["error_msg"] = "status must be 'alive' or 'dead'"
#             return result
#         ent["status"] = status
#
#     # 3. Sync status if HP hit 0
#     if ent["hp_current"] <= 0:
#         ent["status"] = "dead"
#
#     # 4. Build success response
#     result["success"] = True
#     result["entity_data"] = ent.copy()
#     return result

def roll_dice(
        modifier: int = 0,
        roll_purpose: str = "roll dice",
        related_entity: Optional[str] = None
) -> Dict[str, Any]:
    """
    Simulate a d20 dice roll, returning the raw result and the modified result
    :param modifier: Modifier (can be positive or negative)
    :param roll_purpose: Purpose of the roll (attack/defense/initiative)
    :param related_entity: Related entity ID
    :return: Roll result dictionary
    """
    result = {
        "raw_roll": 0,
        "modifier": modifier,
        "modified_roll": 0,
        "roll_purpose": roll_purpose,
        "related_entity": related_entity
    }

    raw_roll = random.randint(1, 20)
    modified_roll = raw_roll + modifier

    result["raw_roll"] = raw_roll
    result["modified_roll"] = modified_roll

    return result


def defense(
        defender_id: str,
        defense_modifier: int = 0,
        defense_purpose: str = "normal_attack"
) -> Dict[str, Any]:
    """
    Perform a defense check, returning the defense roll result
    :param defender_id: Defender entity ID
    :param defense_modifier: Additional defense modifier
    :param defense_purpose: Purpose of the defense (normal_attack/counter_attack)
    :return: Defense check result dictionary
    """
    # Initialize return result
    result = {
        "error_msg": "",
        "defender": {},
        "defense_roll": {},
        "defense_purpose": defense_purpose,
        "result_desc": ""
    }

    # Parameter validation: Check if the defender exists
    if defender_id not in entity_store:
        result["error_msg"] = f"Defender {defender_id} does not exist"
        return result

    defender = entity_store[defender_id]

    # Check defender status
    if defender["status"] == "dead":
        result["error_msg"] = f"Defender {defender['name']} is already dead and cannot defend"
        return result

    # Calculate total defense modifier
    total_modifier = defender["defense_modifier"] + defense_modifier

    # Call the roll dice function
    roll_result = roll_dice(
        modifier=total_modifier,
        roll_purpose="defense",
        related_entity=defender_id
    )

    # Update defense result
    result["defender"] = {
        "id": defender_id,
        "name": defender["name"],
        "defense_modifier": defender["defense_modifier"]
    }
    result["defense_roll"] = {
        "raw_roll": roll_result["raw_roll"],
        "modified_roll": roll_result["modified_roll"],
        "total_modifier": total_modifier
    }
    result["result_desc"] = (
        f"{defender['name']}'s defense roll result is {roll_result['modified_roll']} "
        f"({roll_result['raw_roll']} + {total_modifier} modifier)"
    )

    return result


def attack(
        attacker_id: str,
        target_id: str,
        attack_modifier: int = 0,
        damage_range: List[int] = None
) -> Dict[str, Any]:
    """
    Perform an attack check and damage calculation
    :param attacker_id: Attacker entity ID
    :param target_id: Target entity ID
    :param attack_modifier: Additional attack modifier
    :param damage_range: Damage range (default [1,4])
    :return: Attack result dictionary
    """
    # Initialize default values
    if damage_range is None:
        damage_range = [1, 4]

    # Initialize return result
    result = {
        "error_msg": "",
        "attacker": {},
        "target": {},
        "attack_roll": {},
        "defense_roll": {},
        "hit": False,
        "damage": 0,
        "result_desc": ""
    }

    # Parameter validation
    if attacker_id not in entity_store:
        result["error_msg"] = f"Attacker {attacker_id} does not exist"
        return result
    if target_id not in entity_store:
        result["error_msg"] = f"Target {target_id} does not exist"
        return result
    if attacker_id == target_id:
        result["error_msg"] = "Cannot attack self"
        return result

    attacker = entity_store[attacker_id]
    target = entity_store[target_id]

    # Check attacker/target status
    if attacker["status"] == "dead":
        result["error_msg"] = f"Attacker {attacker['name']} is already dead and cannot attack"
        return result
    if target["status"] == "dead":
        result["error_msg"] = f"Target {target['name']} is already dead and cannot be attacked"
        return result

    # 1. Perform attack roll
    total_attack_modifier = attacker["attack_modifier"] + attack_modifier
    attack_roll_result = roll_dice(
        modifier=total_attack_modifier,
        roll_purpose="attack",
        related_entity=attacker_id
    )

    # 2. Perform target defense check
    defense_result = defense(defender_id=target_id)

    # 3. Hit determination
    hit = attack_roll_result["modified_roll"] > defense_result["defense_roll"]["modified_roll"]
    damage = 0
    hp_before = target["hp_current"]

    # 4. Calculate damage (only if hit)
    if hit:
        damage = random.randint(damage_range[0], damage_range[1])
        # Update target HP
        target["hp_current"] = max(0, hp_before - damage)
        # Update target status
        if target["hp_current"] <= 0:
            target["status"] = "dead"
        # Sync to entity storage
        entity_store[target_id] = target

    # 5. Assemble results
    result["attacker"] = {
        "id": attacker_id,
        "name": attacker["name"]
    }
    result["target"] = {
        "id": target_id,
        "name": target["name"],
        "hp_before": hp_before,
        "hp_after": target["hp_current"],
        "status": target["status"]
    }
    result["attack_roll"] = {
        "raw_roll": attack_roll_result["raw_roll"],
        "modified_roll": attack_roll_result["modified_roll"],
        "modifier": total_attack_modifier
    }
    result["defense_roll"] = defense_result["defense_roll"]
    result["hit"] = hit
    result["damage"] = damage

    # Generate natural language description
    if hit:
        result["result_desc"] = (
            f"{attacker['name']}'s attack roll is {attack_roll_result['raw_roll']} "
            f"(+{total_attack_modifier} modifier), {target['name']}'s defense roll is "
            f"{defense_result['defense_roll']['modified_roll']}, hit! Dealt {damage} damage, "
            f"{target['name']}'s remaining HP: {target['hp_current']} (Status: {target['status']})"
        )
    else:
        result["result_desc"] = (
            f"{attacker['name']}'s attack roll is {attack_roll_result['raw_roll']} "
            f"(+{total_attack_modifier} modifier), {target['name']}'s defense roll is "
            f"{defense_result['defense_roll']['modified_roll']}, miss!"
        )

    return result


def query_target(
        target_id: Optional[str] = None,
        query_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query entity status (HP, attack/defense modifiers, alive status)
    :param target_id: Target entity ID (empty to query all alive entities)
    :param query_type: Query type (single/all_alive), inferred automatically
    :return: Status query result dictionary
    """
    # Initialize return result
    result = {
        "error_msg": "",
        "query_type": "",
        "targets": [],
        "result_desc": ""
    }

    # Automatically infer query type
    if query_type is None:
        query_type = "single" if target_id else "all_alive"
    result["query_type"] = query_type

    # 1. Single entity query
    if query_type == "single":
        if not target_id:
            result["error_msg"] = "Single entity query must specify target_id"
            return result
        if target_id not in entity_store:
            result["error_msg"] = f"Entity {target_id} does not exist"
            return result

        entity = entity_store[target_id]
        hp_percent = round((entity["hp_current"] / entity["hp_max"]) * 100, 1)

        target_info = {
            "id": target_id,
            "name": entity["name"],
            "hp_current": entity["hp_current"],
            "hp_max": entity["hp_max"],
            "hp_percent": hp_percent,
            "status": entity["status"],
            "attack_modifier": entity["attack_modifier"],
            "defense_modifier": entity["defense_modifier"]
        }
        result["targets"].append(target_info)
        result["result_desc"] = (
            f"{entity['name']}'s current status: HP {entity['hp_current']}/{entity['hp_max']} "
            f"({hp_percent}%), Status: {entity['status']}, Attack modifier +{entity['attack_modifier']}, "
            f"Defense modifier +{entity['defense_modifier']}"
        )

    # 2. Query all alive entities
    elif query_type == "all_alive":
        alive_entities = [
            e for e in entity_store.values() if e["status"] == "alive"
        ]
        if not alive_entities:
            result["result_desc"] = "No alive entities currently"
        else:
            return query_all()

    # Unsupported query type
    else:
        result["error_msg"] = f"Unsupported query type: {query_type} (only single/all_alive are supported)"
        return result

    return result


def query_all():
    result = {
        "error_msg": "",
        "query_type": "",
        "targets": [],
        "result_desc": ""
    }

    alive_entities = [
        e for e in entity_store.values() if e["status"] == "alive"
    ]
    if not alive_entities:
        result["result_desc"] = "No alive entities currently"
    else:
        desc_parts = ["Current status of alive entities:"]
        for entity in alive_entities:
            hp_percent = round((entity["hp_current"] / entity["hp_max"]) * 100, 1)
            target_info = {
                "id": next(k for k, v in entity_store.items() if v["name"] == entity["name"]),
                "name": entity["name"],
                "hp_current": entity["hp_current"],
                "hp_max": entity["hp_max"],
                "hp_percent": hp_percent,
                "status": entity["status"],
                "attack_modifier": entity["attack_modifier"],
                "defense_modifier": entity["defense_modifier"]
            }
            result["targets"].append(target_info)
            desc_parts.append(
                f"- {entity['name']}: HP {entity['hp_current']}/{entity['hp_max']} ({hp_percent}%)"
            )
        result["result_desc"] = "\n".join(desc_parts)
    return result


# ===================== Example Calls =====================
if __name__ == "__main__":
    import pprint

    print("=== Create a single player entity ===")
    player_result = create_entity(
        entity_name="Hero",
        entity_type=EntityType.PLAYER,
        # Custom attributes (optional, default values used if not provided)
        hp_max=12,
        attack_modifier=3
    )
    pprint.pprint(player_result)
    print("\n")

    # 2. Create a single creature entity (random attributes)
    print("=== Create a single creature entity ===")
    goblin_result = create_entity(
        entity_name="Goblin Scout",
        entity_type=EntityType.CREATURE,
        custom_id="Goblin_Scout_01"  # Custom ID
    )
    pprint.pprint(goblin_result)
    print("\n")

    # 1. Test dice roll
    print("=== Test dice roll ===")
    roll_result = roll_dice(modifier=2, roll_purpose="attack", related_entity="Player_01")
    pprint.pprint(roll_result)
    print("\n")

    # 2. Test defense check
    print("=== Test defense check ===")
    defense_result = defense(defender_id="Goblin_01")
    pprint.pprint(defense_result)
    print("\n")

    # 3. Test attack
    print("=== Test attack ===")
    attack_result = attack(attacker_id="Player_01", target_id="Goblin_01")
    pprint.pprint(attack_result)
    print("\n")

    # 4. Test status query (single)
    print("=== Test single entity status query ===")
    status_single = query_target(target_id="Player_01")
    pprint.pprint(status_single)
    print("\n")

    # 5. Test status query (all alive)
    print("=== Test all alive entities status query ===")
    status_all = query_target()
    pprint.pprint(status_all)
    print("\n")