import random
from enum import Enum
from typing import Dict, List, Optional, Any

# ===================== 模拟数据层（替代真实数据库/存储） =====================
entity_store: Dict[str, Dict[str, Any]] = {
    "Player_01": {
        "name": "冒险者",
        "hp_current": 10,
        "hp_max": 10,
        "attack_modifier": 2,
        "defense_modifier": 1,
        "status": "存活"  # 存活/死亡
    },
    "Goblin_01": {
        "name": "哥布林",
        "hp_current": 6,
        "hp_max": 6,
        "attack_modifier": 1,
        "defense_modifier": 0,
        "status": "存活"
    }
}


class EntityType(Enum):
    PLAYER = "player"
    CREATURE = "creature"


DEFAULT_ATTRIBUTES = {
    EntityType.PLAYER: {
        "hp_max": 10,
        "attack_modifier": 2,
        "defense_modifier": 1,
        "status": "存活"
    },
    EntityType.CREATURE: {
        "hp_max_range": [5, 8],  # 怪物最大HP随机范围
        "attack_modifier_range": [0, 1],  # 怪物攻击修正随机范围
        "defense_modifier_range": [0, 1],  # 怪物防御修正随机范围
        "status": "存活"
    }
}


# Agent 短期记忆（模拟存储交互记录）
# agent_memory: List[Dict[str, Any]] = []

# ===================== 核心工具函数实现 =====================

def create_entity(
        entity_name: str,
        entity_type: EntityType,
        hp_max: Optional[int] = None,
        attack_modifier: Optional[int] = None,
        defense_modifier: Optional[int] = None,
        custom_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建 D&D 实体（玩家/怪物），自动生成唯一ID，填充默认属性，支持自定义属性覆盖
    :param entity_name: 实体名称（如"冒险者"、"哥布林"）
    :param entity_type: 实体类型（EntityType.PLAYER/EntityType.CREATURE）
    :param hp_max: 最大HP（可选，覆盖默认值）
    :param attack_modifier: 攻击修正值（可选，覆盖默认值）
    :param defense_modifier: 防御修正值（可选，覆盖默认值）
    :param custom_id: 自定义实体ID（可选，默认自动生成）
    :return: 实体创建结果字典
    """
    # 初始化返回结果
    result = {
        "success": False,
        "error_msg": "",
        "entity_id": "",
        "entity_data": {}
    }

    # 1. 基础参数校验
    if not entity_name.strip():
        result["error_msg"] = "实体名称不能为空"
        return result
    if not isinstance(entity_type, EntityType):
        result["error_msg"] = f"实体类型必须为 EntityType 枚举值（{[e.value for e in EntityType]}）"
        return result

    # 2. 生成唯一实体ID
    if custom_id:
        # 自定义ID需检查唯一性
        if custom_id in entity_store:
            result["error_msg"] = f"自定义ID {custom_id} 已存在，无法创建"
            return result
        entity_id = custom_id
    else:
        # 自动生成ID：类型前缀 + 序号（如 Player_01、Creature_02）
        type_prefix = entity_type.value.capitalize()
        # 统计当前类型的实体数量，生成递增序号
        existing_count = len([
            eid for eid in entity_store.keys()
            if eid.startswith(f"{type_prefix}_")
        ])
        entity_id = f"{type_prefix}_{str(existing_count + 1).zfill(2)}"  # 补零保证格式统一（01/02/03）

    # 3. 填充实体属性
    entity_data = {"name": entity_name.strip()}

    # 玩家实体属性逻辑
    if entity_type == EntityType.PLAYER:
        entity_data["hp_max"] = hp_max if hp_max is not None else DEFAULT_ATTRIBUTES[EntityType.PLAYER]["hp_max"]
        entity_data["attack_modifier"] = attack_modifier if attack_modifier is not None else \
            DEFAULT_ATTRIBUTES[EntityType.PLAYER]["attack_modifier"]
        entity_data["defense_modifier"] = defense_modifier if defense_modifier is not None else \
            DEFAULT_ATTRIBUTES[EntityType.PLAYER]["defense_modifier"]
        entity_data["status"] = DEFAULT_ATTRIBUTES[EntityType.PLAYER]["status"]

    # 怪物实体属性逻辑（支持随机范围）
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

    # 4. 校验属性合法性
    if entity_data["hp_max"] <= 0:
        result["error_msg"] = "最大HP必须大于0"
        return result
    if not isinstance(entity_data["attack_modifier"], int):
        result["error_msg"] = "攻击修正值必须为整数"
        return result
    if not isinstance(entity_data["defense_modifier"], int):
        result["error_msg"] = "防御修正值必须为整数"
        return result

    # 5. 初始化当前HP（默认等于最大HP）
    entity_data["hp_current"] = entity_data["hp_max"]

    # 6. 存入实体存储中心
    entity_store[entity_id] = entity_data

    # 7. 组装返回结果
    result["success"] = True
    result["entity_id"] = entity_id
    result["entity_data"] = entity_data
    result["error_msg"] = ""

    return result


def roll_dice(
        modifier: int = 0,
        roll_purpose: str = "roll dice",
        related_entity: Optional[str] = None
) -> Dict[str, Any]:
    """
    模拟 d20 骰子投掷，返回原始结果与修正后结果
    :param modifier: 修正值（可正可负）
    :param roll_purpose: 掷骰用途（attack/defense/主动掷骰）
    :param related_entity: 关联实体 ID
    :return: 掷骰结果字典
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
    执行防御判定，返回防御掷骰结果
    :param defender_id: 防御者实体 ID
    :param defense_modifier: 额外防御修正值
    :param defense_purpose: 防御用途（normal_attack/counter_attack）
    :return: 防御判定结果字典
    """
    # 初始化返回结果
    result = {
        "error_msg": "",
        "defender": {},
        "defense_roll": {},
        "defense_purpose": defense_purpose,
        "result_desc": ""
    }

    # 参数校验：检查防御者是否存在
    if defender_id not in entity_store:
        result["error_msg"] = f"防御者 {defender_id} 不存在"
        return result

    defender = entity_store[defender_id]

    # 检查防御者状态
    if defender["status"] == "死亡":
        result["error_msg"] = f"防御者 {defender['name']} 已死亡，无法进行防御"
        return result

    # 计算总防御修正
    total_modifier = defender["defense_modifier"] + defense_modifier

    # 调用掷骰函数
    roll_result = roll_dice(
        modifier=total_modifier,
        roll_purpose="defense",
        related_entity=defender_id
    )

    # 更新防御结果
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
    result[
        "result_desc"] = f"{defender['name']} 的防御判定结果为 {roll_result['modified_roll']}（{roll_result['raw_roll']} + {total_modifier} 修正）"

    # # 记录到 Agent 记忆
    # agent_memory.append({
    #     "action": "defense",
    #     "defender_id": defender_id,
    #     "defense_roll": roll_result["modified_roll"],
    #     "purpose": defense_purpose
    # })

    return result


def attack(
        attacker_id: str,
        target_id: str,
        attack_modifier: int = 0,
        damage_range: List[int] = None
) -> Dict[str, Any]:
    """
    执行攻击判定与伤害计算
    :param attacker_id: 攻击者实体 ID
    :param target_id: 目标实体 ID
    :param attack_modifier: 额外攻击修正值
    :param damage_range: 伤害范围（默认 [1,4]）
    :return: 攻击结果字典
    """
    # 初始化默认值
    if damage_range is None:
        damage_range = [1, 4]

    # 初始化返回结果
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

    # 参数校验
    if attacker_id not in entity_store:
        result["error_msg"] = f"攻击者 {attacker_id} 不存在"
        return result
    if target_id not in entity_store:
        result["error_msg"] = f"目标 {target_id} 不存在"
        return result
    if attacker_id == target_id:
        result["error_msg"] = "无法攻击自身"
        return result

    attacker = entity_store[attacker_id]
    target = entity_store[target_id]

    # 检查攻击者/目标状态
    if attacker["status"] == "死亡":
        result["error_msg"] = f"攻击者 {attacker['name']} 已死亡，无法攻击"
        return result
    if target["status"] == "死亡":
        result["error_msg"] = f"目标 {target['name']} 已死亡，无法攻击"
        return result

    # 1. 执行攻击掷骰
    total_attack_modifier = attacker["attack_modifier"] + attack_modifier
    attack_roll_result = roll_dice(
        modifier=total_attack_modifier,
        roll_purpose="attack",
        related_entity=attacker_id
    )

    # 2. 执行目标防御判定
    defense_result = defense(defender_id=target_id)

    # 3. 命中判定
    hit = attack_roll_result["modified_roll"] > defense_result["defense_roll"]["modified_roll"]
    damage = 0
    hp_before = target["hp_current"]

    # 4. 计算伤害（仅命中时）
    if hit:
        damage = random.randint(damage_range[0], damage_range[1])
        # 更新目标 HP
        target["hp_current"] = max(0, hp_before - damage)
        # 更新目标状态
        if target["hp_current"] <= 0:
            target["status"] = "死亡"
        # 同步到实体存储
        entity_store[target_id] = target

    # 5. 组装结果
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

    # 生成自然语言描述
    if hit:
        result["result_desc"] = (
            f"{attacker['name']} 的攻击掷出 {attack_roll_result['raw_roll']}（+{total_attack_modifier} 修正），"
            f"{target['name']} 的防御判定为 {defense_result['defense_roll']['modified_roll']}，攻击命中！"
            f"造成 {damage} 点伤害，{target['name']} 剩余 HP：{target['hp_current']}（状态：{target['status']}）"
        )
    else:
        result["result_desc"] = (
            f"{attacker['name']} 的攻击掷出 {attack_roll_result['raw_roll']}（+{total_attack_modifier} 修正），"
            f"{target['name']} 的防御判定为 {defense_result['defense_roll']['modified_roll']}，攻击未命中！"
        )

    return result


def query_target(
        target_id: Optional[str] = None,
        query_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    查询实体状态（HP、攻防修正、存活状态）
    :param target_id: 目标实体 ID（为空则查询所有存活实体）
    :param query_type: 查询类型（single/all_alive），自动推断
    :return: 状态查询结果字典
    """
    # 初始化返回结果
    result = {
        "error_msg": "",
        "query_type": "",
        "targets": [],
        "result_desc": ""
    }

    # 自动推断查询类型
    if query_type is None:
        query_type = "single" if target_id else "all_alive"
    result["query_type"] = query_type

    # 1. 单个实体查询
    if query_type == "single":
        if not target_id:
            result["error_msg"] = "单个实体查询必须指定 target_id"
            return result
        if target_id not in entity_store:
            result["error_msg"] = f"实体 {target_id} 不存在"
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
            f"{entity['name']} 的当前状态：HP {entity['hp_current']}/{entity['hp_max']}（{hp_percent}%），"
            f"状态：{entity['status']}，攻击修正+{entity['attack_modifier']}，防御修正+{entity['defense_modifier']}"
        )

    # 2. 所有存活实体查询
    elif query_type == "all_alive":
        alive_entities = [
            e for e in entity_store.values() if e["status"] == "存活"
        ]
        if not alive_entities:
            result["result_desc"] = "当前无存活实体"
        else:
            return query_all()

    # 无效查询类型
    else:
        result["error_msg"] = f"不支持的查询类型：{query_type}（仅支持 single/all_alive）"
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
        e for e in entity_store.values() if e["status"] == "存活"
    ]
    if not alive_entities:
        result["result_desc"] = "当前无存活实体"
    else:
        desc_parts = ["当前存活实体状态："]
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
                f"- {entity['name']}：HP {entity['hp_current']}/{entity['hp_max']}（{hp_percent}%）"
            )
        result["result_desc"] = "\n".join(desc_parts)
    return result


# ===================== 示例调用 =====================
if __name__ == "__main__":
    import pprint

    print("=== 创建单个玩家实体 ===")
    player_result = create_entity(
        entity_name="勇者",
        entity_type=EntityType.PLAYER,
        # 自定义属性（可选，不填则用默认值）
        hp_max=12,
        attack_modifier=3
    )
    pprint.pprint(player_result)
    print("\n")

    # 2. 创建单个怪物实体（随机属性）
    print("=== 创建单个怪物实体 ===")
    goblin_result = create_entity(
        entity_name="哥布林斥候",
        entity_type=EntityType.CREATURE,
        custom_id="Goblin_Scout_01"  # 自定义ID
    )
    pprint.pprint(goblin_result)
    print("\n")

    # 1. 测试掷骰子
    print("=== 测试掷骰子 ===")
    roll_result = roll_dice(modifier=2, roll_purpose="attack", related_entity="Player_01")
    pprint.pprint(roll_result)
    print("\n")

    # 2. 测试防御判定
    print("=== 测试防御判定 ===")
    defense_result = defense(defender_id="Goblin_01")
    pprint.pprint(defense_result)
    print("\n")

    # 3. 测试攻击
    print("=== 测试攻击 ===")
    attack_result = attack(attacker_id="Player_01", target_id="Goblin_01")
    pprint.pprint(attack_result)
    print("\n")

    # 4. 测试状态查询（单个）
    print("=== 测试单个实体状态查询 ===")
    status_single = query_target(target_id="Player_01")
    pprint.pprint(status_single)
    print("\n")

    # 5. 测试状态查询（所有存活）
    print("=== 测试所有存活实体状态查询 ===")
    status_all = query_target()
    pprint.pprint(status_all)
    print("\n")
