"""
SKLEP Z ULEPSZENIAMI (Shop / Upgrades).

Łazik zarabia pieniądze ($) sprzedając minerały w Bazie Naukowej. Za pieniądze
ORAZ materiały (minerały) może kupować ulepszenia. Część ulepszeń ma DEBUFF
(kompromis) -- poprawiają jedno, pogarszając coś innego.

Atrybuty agenta modyfikowane przez sklep:
  capacity         -- limit wagi plecaka (kg)
  volume_capacity  -- limit objętości plecaka (l)
  max_battery      -- pojemność baterii
  solar_bonus      -- mnożnik ładowania słonecznego
  motor_efficiency -- mnożnik kosztu ruchu (mniej = taniej)
  volume_factor    -- mnożnik objętości przenoszonych minerałów (mniej = lepiej)
  sell_bonus       -- premia do ceny sprzedaży minerałów
"""

from typing import Dict, List, Any, Optional

# Globalny przełącznik sklepu. False -> łazik NIE kupuje ulepszeń
# (np. do porównania misji z/bez sklepu). Domyślnie sklep aktywny.
SHOP_ENABLED: bool = True

# =====================================================================
# KATALOG ULEPSZEŃ. Koszt poziomu = pieniądze ($) + materiały.
# "(−)" w opisie oznacza DEBUFF (kompromis).
# =====================================================================
SHOP_CATALOG: Dict[str, Dict[str, Any]] = {
    "solar": {
        "name": "Panele słoneczne",
        "description": "+0.6x ładowanie słoneczne. (−) −3 l pojemności plecaka.",
        "levels": [
            {"money": 90.0,  "materials": {"Hematite": 1}},
            {"money": 200.0, "materials": {"Hematite": 2, "Water Ice": 1}},
        ],
    },
    "compressor": {
        "name": "Kompresor ładunku",
        "description": "Minerały zajmują −15% objętości (więcej zmieści się objętościowo).",
        "levels": [
            {"money": 90.0,  "materials": {"Hematite": 1}},
            {"money": 200.0, "materials": {"Hematite": 2, "Water Ice": 1}},
        ],
    },
    "cargo": {
        "name": "Ładownia",
        "description": "+8 kg i +6 l pojemności plecaka (większy problem plecakowy).",
        "levels": [
            {"money": 120.0, "materials": {"Hematite": 2}},
            {"money": 250.0, "materials": {"Hematite": 2, "Titanium": 1}},
            {"money": 450.0, "materials": {"Titanium": 3}},
        ],
    },
    "motor": {
        "name": "Silnik napędowy",
        "description": "−15% kosztu ruchu. (−) −10 maks. baterii.",
        "levels": [
            {"money": 130.0, "materials": {"Titanium": 1}},
            {"money": 280.0, "materials": {"Titanium": 2, "Hematite": 1}},
        ],
    },
    "battery": {
        "name": "Ogniwo bateryjne",
        "description": "+30 maks. baterii. (−) +5% kosztu ruchu (cięższa).",
        "levels": [
            {"money": 110.0, "materials": {"Water Ice": 2}},
            {"money": 240.0, "materials": {"Water Ice": 3, "Hematite": 1}},
            {"money": 420.0, "materials": {"Water Ice": 4, "Titanium": 1}},
        ],
    },
    "drill": {
        "name": "Wiertło wydobywcze",
        "description": "+15% ceny sprzedaży minerałów. (−) +8% kosztu ruchu.",
        "levels": [
            {"money": 150.0, "materials": {"Titanium": 1, "Hematite": 1}},
            {"money": 320.0, "materials": {"Titanium": 2, "Water Ice": 2}},
        ],
    },
}

# Kolejność auto-zakupów agenta (najpierw przeżywalność i pojemność, na końcu zysk).
UPGRADE_ORDER: List[str] = ["solar", "compressor", "cargo", "motor", "battery", "drill"]


def _inventory_counts(agent) -> Dict[str, int]:
    """Zlicza materiały w plecaku agenta według typu."""
    counts: Dict[str, int] = {}
    for item in agent.inventory:
        counts[item] = counts.get(item, 0) + 1
    return counts


def next_level_cost(upgrade_id: str, agent) -> Optional[Dict[str, Any]]:
    """Zwraca koszt następnego poziomu ulepszenia lub None, jeśli osiągnięto maks."""
    upgrade = SHOP_CATALOG.get(upgrade_id)
    if not upgrade:
        return None
    level = agent.upgrade_levels.get(upgrade_id, 0)
    if level >= len(upgrade["levels"]):
        return None
    return upgrade["levels"][level]


def can_afford(agent, upgrade_id: str) -> bool:
    """Czy agent ma dość pieniędzy ORAZ materiałów na następny poziom?"""
    cost = next_level_cost(upgrade_id, agent)
    if cost is None:
        return False
    if agent.money < cost["money"]:
        return False
    counts = _inventory_counts(agent)
    for mat, qty in cost["materials"].items():
        if counts.get(mat, 0) < qty:
            return False
    return True


def next_target_upgrade(agent) -> Optional[str]:
    """Kolejny cel ulepszenia wg priorytetu UPGRADE_ORDER (pomija maksymalne)."""
    for upgrade_id in UPGRADE_ORDER:
        if next_level_cost(upgrade_id, agent) is not None:
            return upgrade_id
    return None


def apply_effect(agent, upgrade_id: str) -> None:
    """Stosuje efekt ulepszenia (wraz z ewentualnym debuffem) na agencie."""
    if upgrade_id == "solar":
        agent.solar_bonus += 0.6
        agent.volume_capacity = max(4.0, agent.volume_capacity - 3.0)   # debuff
    elif upgrade_id == "compressor":
        agent.volume_factor *= 0.85
    elif upgrade_id == "cargo":
        agent.capacity += 8.0
        agent.volume_capacity += 6.0
    elif upgrade_id == "motor":
        agent.motor_efficiency *= 0.85
        agent.max_battery = max(60.0, agent.max_battery - 10.0)          # debuff
        agent.battery = min(agent.battery, agent.max_battery)
    elif upgrade_id == "battery":
        agent.max_battery += 30.0
        agent.battery = min(agent.max_battery, agent.battery + 30.0)
        agent.motor_efficiency *= 1.05                                   # debuff
    elif upgrade_id == "drill":
        agent.sell_bonus += 0.15
        agent.motor_efficiency *= 1.08                                   # debuff


def purchase_upgrade(agent, upgrade_id: str) -> Dict[str, Any]:
    """
    Próba zakupu następnego poziomu ulepszenia. Pobiera pieniądze i materiały
    z plecaka, podnosi poziom i stosuje efekt. Zwraca słownik z wynikiem.
    """
    if upgrade_id not in SHOP_CATALOG:
        return {"success": False, "message": f"Nieznane ulepszenie: {upgrade_id}"}

    cost = next_level_cost(upgrade_id, agent)
    if cost is None:
        return {"success": False, "message": "Ulepszenie osiągnęło maksymalny poziom."}

    if not can_afford(agent, upgrade_id):
        return {"success": False, "message": "Za mało pieniędzy lub materiałów."}

    # Pobranie zapłaty: pieniądze
    agent.money -= cost["money"]
    # Pobranie zapłaty: materiały (usuwamy z plecaka dokładnie tyle, ile trzeba)
    for mat, qty in cost["materials"].items():
        removed = 0
        while removed < qty and mat in agent.inventory:
            agent.inventory.remove(mat)
            removed += 1

    agent.upgrade_levels[upgrade_id] = agent.upgrade_levels.get(upgrade_id, 0) + 1
    apply_effect(agent, upgrade_id)

    return {
        "success": True,
        "message": f"Kupiono: {SHOP_CATALOG[upgrade_id]['name']} "
                   f"(poziom {agent.upgrade_levels[upgrade_id]}).",
        "upgrade_id": upgrade_id,
        "new_level": agent.upgrade_levels[upgrade_id],
    }


def get_shop_state(agent) -> List[Dict[str, Any]]:
    """Pełny stan sklepu dla API/UI: katalog + aktualne poziomy + dostępność."""
    state = []
    for upgrade_id in UPGRADE_ORDER:
        upgrade = SHOP_CATALOG[upgrade_id]
        level = agent.upgrade_levels.get(upgrade_id, 0)
        max_level = len(upgrade["levels"])
        cost = next_level_cost(upgrade_id, agent)
        state.append({
            "id": upgrade_id,
            "name": upgrade["name"],
            "description": upgrade["description"],
            "level": level,
            "max_level": max_level,
            "is_maxed": cost is None,
            "next_cost_money": cost["money"] if cost else None,
            "next_cost_materials": cost["materials"] if cost else None,
            "affordable": can_afford(agent, upgrade_id),
        })
    return state
