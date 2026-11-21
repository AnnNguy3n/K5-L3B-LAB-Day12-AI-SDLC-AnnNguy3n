"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

Kiểm cấu trúc fixture tại đây. QuanSim kiểm giữ chỗ và món sau khi nạp kho.
"""

import json
import math

from .errors import BadInput
from .inventory import validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung")
FISH_KINDS = ("ca_linh", "ca_loc")
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if mode == "day":
        if not isinstance(data, dict) or set(data) - {"gather", "quan", "day"}:
            raise BadInput("scenario day cần các khối gather, quan hoặc day")
        for part in ("gather", "quan"):
            validate_block(data.get(part, {}), part, tuning)
        if {"stock", "reputation"} & data.get("quan", {}).keys():
            raise BadInput("day nhận kho từ gather và uy tín từ day")
        return data
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    return validate_block(data.get(mode, {}), mode, tuning)


def validate_block(block, mode, tuning):
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    if mode == "gather" and "freshness" in tuning:
        allowed = allowed | {"monsters"}
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)
    return block


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _fields(row, allowed):
    if set(row) - set(allowed):
        raise BadInput(f"trường lạ: {sorted(set(row) - set(allowed))}")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        allowed_kinds = list(g["fish_yield"]) + [n["kind"] for n in g["nodes"]]
        h = b["hold"]
        if "freshness" in tuning:
            from .sim.fresh import Pantry
            pantry = Pantry(h, tuning, "hold")
            h = [kind for kind, _ in pantry.data.values()]
        if not isinstance(h, list) or any(k not in allowed_kinds for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] >= g["choke_interval_ticks"]:
            raise BadInput("player.zero_oxy_ticks phải nhỏ hơn chu kỳ ngạt")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    if "monsters" in b:
        _check_ids("monsters", b["monsters"])
        for m in b["monsters"]:
            _fields(m, ("id","kind","pos","waypoints","target_idx","state","state_ticks_left","recoil_dir"))
            if m.get("kind") != "ca_sau":
                raise BadInput("loài thủy quái ngoài danh mục")
            region = dict(bounds, d=g["monsters"]["species"]["ca_sau"]["depths"])
            _pos("monsters.pos", m.get("pos"), region)
            points = m.get("waypoints")
            if not isinstance(points, list) or len(points) != 2:
                raise BadInput("cần hai điểm tuần tra")
            for point in points:
                _pos("waypoint", point, region)
            state = m.get("state", "patrol")
            ticks = m.get("state_ticks_left", 0)
            _nonneg_int("state_ticks_left", ticks)
            if state not in ("patrol","chase","recoil") or (state == "recoil") != (ticks > 0):
                raise BadInput("trạng thái tuần tra mâu thuẫn")
            vec = m.get("recoil_dir")
            if state == "recoil":
                if not isinstance(vec,list) or len(vec)!=2 or not all(_num(x) for x in vec) or not math.isclose(math.hypot(*vec),1):
                    raise BadInput("hướng lùi cần là vector đơn vị")
            elif vec is not None:
                raise BadInput("chỉ thủy quái đang lùi mới có hướng lùi")
    for n in b.get("nodes", []):
        _fields(n, ("id","kind","pos","regrow_ticks"))
        if n.get("kind") not in [e["kind"] for e in g["nodes"]]:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        fields = {"id", "kind", "pos", "heading_deg"}
        if "freshness" in tuning:
            fields.add("age_ticks")
            _nonneg_int("age_ticks", f.get("age_ticks", 0))
        _fields(f, fields)
        if f.get("kind") not in g["fish_yield"]:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")


def _validate_quan(b, tuning):
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        if "freshness" in tuning:
            from .sim.fresh import Pantry
            Pantry(b["stock"], tuning, "stock")
        else:
            validate_items(b["stock"])
    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    qb = tuning["quan"]["bounds"]
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")
    for group in ("tables", "stoves"):
        for entity in b.get(group, []):
            _fields(entity, ("id","pos") if group == "tables" else ("id","pos","state","dish","cook_ticks_left","ready_ticks"))
            if "pos" in entity:
                _pos(f"{group}.{entity['id']}.pos", entity["pos"], qb, axes=("x", "z"))
    table_ids = [c.get("table_id") for c in b.get("customers", [])]
    known = {t["id"] for t in tuning["quan"]["tables"]} | {t.get("id") for t in b.get("tables", [])}
    for c in b.get("customers", []):
        _fields(c, ("id","table_id","dish_id","order_tick","state","patience_ticks_left","eat_ticks_left","order_status","reserved","base_price","tip"))
        _nonneg_int("order_tick", c.get("order_tick", 0))
        if not isinstance(c.get("table_id"), str) or c["table_id"] not in known:
            raise BadInput(f"customers.{c['id']}: table_id phải là bàn có thật")
    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")
