"""
=====================================================
FLIPTRYBE SEGMENT 58
DISPATCH NEGOTIATION & PRICING ENGINE
=====================================================
Manages:
counter-offers,
price floors,
vehicle-based benchmarks,
timeouts,
fair clearing prices.
=====================================================
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# =====================================================
# BENCHMARK TABLE (NG Cities)
# =====================================================

CITY_BASE = {
    "lagos": {"bike": 800, "sedan": 2000, "van": 3500, "truck": 6000},
    "abuja": {"bike": 700, "sedan": 1800, "van": 3200, "truck": 5800},
    "ibadan": {"bike": 600, "sedan": 1500, "van": 2800, "truck": 5200},
}


# =====================================================
# NEGOTIATION STATE
# =====================================================

@dataclass
class Negotiation:

    negotiation_id: str
    order_id: int
    buyer_offer: float
    city: str
    vehicle: str

    min_floor: float
    max_counter_rounds: int = 2

    driver_counter_rounds: int = 0
    current_offer: float = 0.0

    started_ts: float = field(default_factory=time.time)
    timeout_sec: int = 300


# =====================================================
# FLOOR CALC
# =====================================================

def calculate_floor(city: str, vehicle: str, distance_km: float):

    base = CITY_BASE.get(city.lower(), CITY_BASE["lagos"])[vehicle]

    return base + (distance_km * 120)


# =====================================================
# START NEGOTIATION
# =====================================================

def start_negotiation(
    *,
    negotiation_id: str,
    order_id: int,
    buyer_offer: float,
    city: str,
    vehicle: str,
    distance_km: float,
):

    floor = calculate_floor(city, vehicle, distance_km)

    return Negotiation(
        negotiation_id=negotiation_id,
        order_id=order_id,
        buyer_offer=buyer_offer,
        city=city,
        vehicle=vehicle,
        min_floor=floor,
        current_offer=buyer_offer,
    )


# =====================================================
# DRIVER COUNTER
# =====================================================

def driver_counter(
    negotiation: Negotiation,
    amount: float,
):

    if time.time() - negotiation.started_ts > negotiation.timeout_sec:
        return {"status": "expired"}

    if negotiation.driver_counter_rounds >= negotiation.max_counter_rounds:
        return {"status": "limit_reached"}

    if amount < negotiation.min_floor:
        amount = negotiation.min_floor

    negotiation.driver_counter_rounds += 1
    negotiation.current_offer = amount

    return {
        "status": "countered",
        "amount": amount,
        "round": negotiation.driver_counter_rounds,
    }


# =====================================================
# BUYER RESPONDS
# =====================================================

def buyer_response(
    negotiation: Negotiation,
    accept: bool,
):

    if accept:
        return {
            "status": "accepted",
            "final_price": negotiation.current_offer,
        }

    return {"status": "rejected"}


# =====================================================
# PRICE GUIDANCE
# =====================================================

def guidance(city: str, vehicle: str, distance_km: float):

    floor = calculate_floor(city, vehicle, distance_km)

    return {
        "suggested_min": round(floor * 1.05),
        "suggested_mid": round(floor * 1.25),
        "suggested_high": round(floor * 1.5),
    }


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    n = start_negotiation(
        negotiation_id="N-44",
        order_id=12,
        buyer_offer=2500,
        city="lagos",
        vehicle="sedan",
        distance_km=8,
    )

    print("GUIDE:", guidance("lagos", "sedan", 8))

    print(driver_counter(n, 4000))
    print(driver_counter(n, 3800))
    print(driver_counter(n, 3600))

    print(buyer_response(n, True))