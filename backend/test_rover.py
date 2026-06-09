# -*- coding: utf-8 -*-
"""
Zestaw testów regresyjnych łazika (bez treningu sieci -- szybki).

Uruchomienie z katalogu backend/:
    python3 test_rover.py

Sprawdza: problem plecakowy (DP/GA, dopuszczalność, przypadki brzegowe),
sklep (zakupy, debuffy, limity), niezmienniki agenta (waga/objętość/pieniądze),
brak zakleszczeń (sitting) oraz regenerację stacji ładujących.
"""

import random
import traceback

from app.core.environment import Environment, Mineral, ChargingStation, MATERIAL_SPECS, MINERAL_TYPES
from app.core.agent import Agent, MIN_MINERAL_WEIGHT, MIN_MINERAL_VOLUME
from app.core.knapsack import (
    KnapsackItem, solve_knapsack_dp, solve_knapsack_ga, compare_knapsack,
)
from app.core import shop

PROJECT_ITEMS = lambda n: [
    KnapsackItem(t := random.choice(MINERAL_TYPES),
                 MATERIAL_SPECS[t]["weight"], MATERIAL_SPECS[t]["volume"], MATERIAL_SPECS[t]["value"])
    for _ in range(n)
]


# =====================================================================
# PROBLEM PLECAKOWY
# =====================================================================
def test_dp_feasible():
    random.seed(1)
    for _ in range(30):
        items = PROJECT_ITEMS(12)
        chosen, val, w, v = solve_knapsack_dp(items, 20, 16)
        assert w <= 20 + 1e-9, f"DP przekroczył wagę: {w}"
        assert v <= 16 + 1e-9, f"DP przekroczył objętość: {v}"
        assert abs(val - sum(i.value for i in chosen)) < 1e-6, "DP wartość != suma wybranych"


def test_ga_feasible():
    random.seed(2)
    for _ in range(30):
        items = PROJECT_ITEMS(12)
        chosen, val, w, v = solve_knapsack_ga(items, 20, 16)
        assert w <= 20 + 1e-9, f"GA przekroczył wagę: {w}"
        assert v <= 16 + 1e-9, f"GA przekroczył objętość: {v}"


def test_ga_matches_dp():
    random.seed(3)
    hits = 0
    trials = 25
    for _ in range(trials):
        items = PROJECT_ITEMS(12)
        r = compare_knapsack(items, 20, 16)
        if r["ga_optimal"]:
            hits += 1
    assert hits >= trials - 2, f"GA trafił w optimum tylko {hits}/{trials} (oczekiwano >= {trials-2})"


def test_volume_constraint_binds():
    # Lód: lekki (3 kg) ale objętościowy (6 l). Limit objętości 6 => zmieści się tylko 1.
    items = [KnapsackItem("Water Ice", 3, 6, 50) for _ in range(5)]
    chosen, val, w, v = solve_knapsack_dp(items, 100, 6)
    assert len(chosen) == 1 and v <= 6, f"Objętość nie ogranicza: wybrano {len(chosen)} (v={v})"


def test_knapsack_edge_cases():
    assert solve_knapsack_dp([], 20, 16) == ([], 0.0, 0.0, 0.0)
    assert solve_knapsack_ga([], 20, 16) == ([], 0.0, 0.0, 0.0)
    # zerowa pojemność
    items = PROJECT_ITEMS(5)
    c, val, w, v = solve_knapsack_dp(items, 0, 0)
    assert c == [] and val == 0.0
    # przedmiot za duży
    big = [KnapsackItem("Titanium", 8, 2, 100)]
    c, val, w, v = solve_knapsack_dp(big, 5, 16)  # waga 8 > 5
    assert c == [] and val == 0.0


# =====================================================================
# SKLEP
# =====================================================================
def test_shop_purchase_deducts():
    a = Agent(0, 0)
    a.money = 1000.0
    a.inventory = ["Hematite", "Hematite"]   # solar L1 = $90 + 1 Hematite
    res = shop.purchase_upgrade(a, "solar")
    assert res["success"], res
    assert a.money == 910.0, f"pieniądze nie odjęte: {a.money}"
    assert a.inventory.count("Hematite") == 1, "materiał nie odjęty"
    assert a.upgrade_levels["solar"] == 1


def test_shop_cannot_afford():
    a = Agent(0, 0)
    a.money = 0.0
    a.inventory = []
    res = shop.purchase_upgrade(a, "solar")
    assert not res["success"]
    assert a.upgrade_levels["solar"] == 0
    assert a.money == 0.0


def test_shop_max_level():
    a = Agent(0, 0)
    # wymuś maksymalny poziom kompresora (2 poziomy)
    a.upgrade_levels["compressor"] = 2
    assert shop.next_level_cost("compressor", a) is None
    res = shop.purchase_upgrade(a, "compressor")
    assert not res["success"], "kupiono ponad maksimum!"


def test_shop_debuffs_and_floors():
    a = Agent(0, 0)
    a.money = 99999.0
    base_vol_cap = a.volume_capacity
    # solar debuff: -3 l objętości (z podłogą 4)
    a.inventory = ["Hematite"]
    shop.purchase_upgrade(a, "solar")
    assert a.volume_capacity == base_vol_cap - 3, "debuff paneli (objętość) nie zadziałał"
    assert a.solar_bonus > 1.0
    # motor debuff: -10 max baterii (podłoga 60)
    a.inventory = ["Titanium"]
    before_batt = a.max_battery
    shop.purchase_upgrade(a, "motor")
    assert a.max_battery == before_batt - 10 and a.motor_efficiency < 1.0
    # battery debuff: +5% koszt ruchu
    a.inventory = ["Water Ice", "Water Ice"]
    me = a.motor_efficiency
    shop.purchase_upgrade(a, "battery")
    assert a.motor_efficiency > me, "debuff baterii (koszt ruchu) nie zadziałał"
    # compressor: objętość minerałów < 1.0
    a.inventory = ["Hematite"]
    shop.purchase_upgrade(a, "compressor")
    assert a.volume_factor < 1.0
    # drill: premia sprzedaży + debuff ruchu
    a.inventory = ["Titanium", "Hematite"]
    shop.purchase_upgrade(a, "drill")
    assert a.sell_bonus > 0.0


def test_shop_floors_hard():
    a = Agent(0, 0)
    a.money = 99999.0
    # kup solar do maksa wiele razy -> objętość nie spadnie poniżej 4
    for _ in range(5):
        a.inventory = ["Hematite", "Hematite", "Water Ice"]
        shop.purchase_upgrade(a, "solar")
    assert a.volume_capacity >= 4.0, f"objętość spadła poniżej podłogi: {a.volume_capacity}"
    for _ in range(5):
        a.inventory = ["Titanium", "Titanium", "Hematite"]
        shop.purchase_upgrade(a, "motor")
    assert a.max_battery >= 60.0, f"max bateria poniżej podłogi: {a.max_battery}"


def test_all_maxed_no_crash():
    a = Agent(0, 0)
    for uid in shop.UPGRADE_ORDER:
        a.upgrade_levels[uid] = len(shop.SHOP_CATALOG[uid]["levels"])
    assert shop.next_target_upgrade(a) is None
    assert a._get_valid_target_upgrade() is None
    a.money = 500.0
    a.inventory = ["Titanium"]
    a._do_base_economy()   # nie może rzucić wyjątku; sprzedaje resztę
    assert a.money >= 500.0


# =====================================================================
# AGENT -- niezmienniki w długiej symulacji (bez sieci)
# =====================================================================
def test_agent_invariants_longrun():
    random.seed(7)
    env = Environment(20, 15)
    sx, sy = env.reset()
    a = Agent(sx, sy)
    max_same = same = 0
    last = None
    died_at = None
    for step in range(2000):
        if a.status == "DEAD":
            died_at = step
            break
        a.follow_plan_or_search(env, None, None, None)
        a.interact_and_recharge(env)
        env.update_time_and_weather()
        # niezmienniki
        assert a.current_weight() <= a.capacity + 1e-6, f"przeciążenie wagi {a.current_weight()}>{a.capacity}"
        assert a.current_volume() <= a.volume_capacity + 1e-6, f"przeciążenie objętości {a.current_volume()}>{a.volume_capacity}"
        assert a.money >= 0.0, f"ujemne pieniądze: {a.money}"
        assert a.battery <= a.max_battery + 1e-6, f"bateria > max: {a.battery}>{a.max_battery}"
        assert a.battery > -5.0, f"bateria mocno ujemna: {a.battery}"
        for uid, lvl in a.upgrade_levels.items():
            assert lvl <= len(shop.SHOP_CATALOG[uid]["levels"]), f"poziom {uid} ponad maks"
        for m in a.inventory:
            assert m in MINERAL_TYPES, f"nieprawidłowy minerał w plecaku: {m}"
        # zakleszczenie (sitting) -- liczone tylko gdy żyje
        pos = (a.x, a.y)
        same = same + 1 if pos == last else 1
        last = pos
        max_same = max(max_same, same)
    assert max_same < 60, f"łazik utknął na jednym polu na {max_same} kroków (sitting)"
    # raport informacyjny (nie assert)
    test_agent_invariants_longrun.info = f"max_same={max_same} died_at={died_at} money=${a.money:.0f} upg={sum(a.upgrade_levels.values())}"


def test_charger_regen():
    env = Environment(20, 15)
    env.reset()
    ch = next(o for o in env.objects if o.type == "ChargingStation")
    ch.energy_pool = 0.0
    ch.is_active = False
    env._regenerate_chargers()
    assert ch.energy_pool > 0.0, "regeneracja nie dodała energii"
    assert ch.is_active, "rozładowana stacja nie reaktywowała się"
    # nie przekracza limitu
    ch.energy_pool = 499.0
    env._regenerate_chargers()
    assert ch.energy_pool <= 500.0, f"energia ponad limit: {ch.energy_pool}"


def test_pickup_respects_both_limits():
    env = Environment(20, 15)
    env.reset()
    a = Agent(0, 0)
    # zapełnij prawie po objętości: 2x Water Ice = 12 l (limit 16)
    a.inventory = ["Water Ice", "Water Ice"]
    env.objects = [Mineral("Water Ice", a.x, a.y)]  # +6 l -> 18 > 16
    a.interact_and_recharge(env)
    assert a.current_volume() <= a.volume_capacity, "podniósł minerał mimo braku objętości"
    assert env.objects[0].is_active, "minerał zniknął mimo odmowy podniesienia"


# =====================================================================
# TEST PEŁNEGO STOSU Z SIECIĄ (wolny -- trenuje CNN). Uruchom: python3 test_rover.py --nn
# =====================================================================
def test_nn_integration():
    import asyncio
    import app.api as api  # import trenuje sieć CNN+MLP
    survived_full = 0
    for _ in range(3):
        api.env.reset()
        sx, sy = api.env._get_free_sand_position()
        api.agent = Agent(sx, sy)
        a = api.agent
        for _ in range(1500):
            if a.status == "DEAD":
                break
            a.follow_plan_or_search(api.env, api.trained_nn, api.scaler, api.reverse_mapping)
            a.interact_and_recharge(api.env)
            api.env.update_time_and_weather()
            assert a.current_weight() <= a.capacity + 1e-6
            assert a.current_volume() <= a.volume_capacity + 1e-6
        if a.status != "DEAD":
            survived_full += 1
    # Uwaga: po podniesieniu trudności śmierć jest dopuszczalna -- testujemy POPRAWNOŚĆ
    # (niezmienniki + brak wyjątków + serializacja), a nie samą przeżywalność.
    gs = asyncio.run(api.get_current_state())
    assert gs.agent.volume_capacity > 0 and len(gs.shop) == 6, "zła serializacja /state"
    k = asyncio.run(api.knapsack_compare())
    assert "ga_optimal" in k, "zła odpowiedź /knapsack"
    buy = asyncio.run(api.buy_upgrade("solar"))
    assert "success" in buy, "zła odpowiedź /shop/buy"
    test_nn_integration.info = f"survived_full={survived_full}/3 | shop={len(gs.shop)} | knapsack GA=${k['ga']['value']} DP=${k['dp']['value']}"


# =====================================================================
# RUNNER
# =====================================================================
def main():
    import sys
    with_nn = "--nn" in sys.argv
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)
             and (with_nn or k != "test_nn_integration")]
    passed = failed = 0
    print("=" * 64)
    print(f"  TESTY ŁAZIKA — {len(tests)} przypadków")
    print("=" * 64)
    for fn in tests:
        name = fn.__name__
        try:
            fn()
            info = getattr(fn, "info", "")
            print(f"  [PASS] {name}" + (f"   ({info})" if info else ""))
            passed += 1
        except Exception:
            print(f"  [FAIL] {name}")
            print("        " + traceback.format_exc().strip().replace("\n", "\n        "))
            failed += 1
    print("=" * 64)
    print(f"  WYNIK: {passed} PASS / {failed} FAIL")
    print("=" * 64)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
