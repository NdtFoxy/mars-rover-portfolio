"""
SKLEP Z ULEPSZENIAMI (Shop / Upgrades).

Łazik zarabia pieniądze ($) sprzedając minerały w Bazie Naukowej. Za pieniądze
ORAZ materiały (minerały) może kupować ulepszenia. Połączenie "pieniądze +
materiały" sprawia, że typy minerałów mają znaczenie i wzbogaca problem
plecakowy (część surowców trzeba zachować na ulepszenia, a nie sprzedać).

Kluczowe ulepszenie -- pojemność plecaka -- bezpośrednio zmienia rozmiar
problemu plecakowego (limit wagi W).
"""

from typing import Dict, List, Any, Optional
from .environment import MATERIAL_SPECS

# =====================================================================
# KATALOG ULEPSZEŃ
# Każde ulepszenie ma poziomy. Koszt poziomu = pieniądze ($) + materiały.
# "effect" opisuje, co zmienia kupno (stosowane w apply_effect na agencie).
# =====================================================================
SHOP_CATALOG: Dict[str, Dict[str, Any]] = {
    "backpack": {
        "name": "Plecak ładunkowy",
        "description": "Zwiększa pojemność plecaka (+8 kg za poziom).",
        "effect": "capacity",
        "bonus": 8.0,
        "levels": [
            {"money": 120.0, "materials": {"Hematite": 2}},
            {"money": 250.0, "materials": {"Hematite": 2, "Titanium": 1}},
            {"money": 450.0, "materials": {"Titanium": 3}},
        ],
    },
    "battery": {
        "name": "Ogniwo bateryjne",
        "description": "Zwiększa maksymalną pojemność baterii (+25% za poziom).",
        "effect": "max_battery",
        "bonus": 25.0,
        "levels": [
            {"money": 100.0, "materials": {"Water Ice": 2}},
            {"money": 220.0, "materials": {"Water Ice": 3, "Hematite": 1}},
            {"money": 400.0, "materials": {"Water Ice": 4, "Titanium": 1}},
        ],
    },
    "solar": {
        "name": "Panele słoneczne",
        "description": "Zwiększa moc ładowania słonecznego (+0.5x za poziom).",
        "effect": "solar_bonus",
        "bonus": 0.5,
        "levels": [
            {"money": 90.0, "materials": {"Hematite": 1}},
            {"money": 200.0, "materials": {"Hematite": 2, "Water Ice": 1}},
        ],
    },
    "motor": {
        "name": "Silnik napędowy",
        "description": "Zmniejsza koszt ruchu po terenie (-15% za poziom).",
        "effect": "motor_efficiency",
        "bonus": 0.85,  # mnożnik kosztu ruchu (0.85 = 15% taniej)
        "levels": [
            {"money": 130.0, "materials": {"Titanium": 1}},
            {"money": 280.0, "materials": {"Titanium": 2, "Hematite": 1}},
        ],
    },
}

# Kolejność auto-zakupów agenta: najpierw ulepszenia zwiększające przeżywalność
# (panele słoneczne -> silnik -> bateria), a na końcu plecak (pojemność).
# Dzięki temu zakupy realnie wydłużają życie i nakręcają pętlę ekonomiczną.
UPGRADE_ORDER: List[str] = ["solar", "motor", "battery", "backpack"]


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


def materials_needed_for(agent, upgrade_id: Optional[str]) -> Dict[str, int]:
    """Materiały wymagane na następny poziom danego ulepszenia (do rezerwacji)."""
    if upgrade_id is None:
        return {}
    cost = next_level_cost(upgrade_id, agent)
    return dict(cost["materials"]) if cost else {}


def next_target_upgrade(agent) -> Optional[str]:
    """
    Wybiera kolejny cel ulepszenia (wg priorytetu UPGRADE_ORDER), pomijając te
    już maksymalne. Agent będzie zbierał na nie pieniądze i rezerwował materiały.
    """
    for upgrade_id in UPGRADE_ORDER:
        if next_level_cost(upgrade_id, agent) is not None:
            return upgrade_id
    return None


def apply_effect(agent, upgrade_id: str) -> None:
    """Stosuje efekt ulepszenia na agencie (po udanym zakupie)."""
    upgrade = SHOP_CATALOG[upgrade_id]
    effect = upgrade["effect"]
    bonus = upgrade["bonus"]

    if effect == "capacity":
        agent.capacity += bonus
    elif effect == "max_battery":
        agent.max_battery += bonus
        agent.battery = min(agent.max_battery, agent.battery + bonus)  # mała premia
    elif effect == "solar_bonus":
        agent.solar_bonus += bonus
    elif effect == "motor_efficiency":
        agent.motor_efficiency *= bonus


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

    agent.upgrade_levels[upgrade_id] += 1
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
