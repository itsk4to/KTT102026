from __future__ import annotations
from game.content.dao_paths import DAO_PATHS, DAO_STAGE_NAMES, DAO_STAGE_THRESHOLD

def stage_from_insight(insight:int)->int: return min(len(DAO_STAGE_NAMES)-1, insight//DAO_STAGE_THRESHOLD)
def stage_name(stage:int)->str: return DAO_STAGE_NAMES[stage] if 0<=stage<len(DAO_STAGE_NAMES) else "?"
def dao_combat_mods(dao_type:str,stage:int)->dict:
    path=DAO_PATHS.get(dao_type,{})
    scale=1.0+stage*0.03
    return {"atk":path.get("atk",1.0)*scale,"def":path.get("def",1.0)*scale,"acc":path.get("acc",1.0),"hp":path.get("hp",1.0),"spirit":path.get("spirit",1.0)*(1+stage*0.02),"crit":path.get("crit",1.0)+stage*0.01}
