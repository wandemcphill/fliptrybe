"""
=====================================================
FLIPTRYBE SEGMENT 75
LOGISTICS & SUPPLY CHAIN CORE
=====================================================
Responsibilities:
1. Warehouse registry
2. Inventory ledger
3. Stock forecasting
4. Reorder automation
5. Fulfillment routing
6. Batch picking
7. Supplier portal
8. Purchase orders
9. IoT telemetry ingest
10. Shrinkage audits
=====================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List
import uuid
import random


# =====================================================
# MODELS
# =====================================================

@dataclass
class Warehouse:
    id: str
    name: str
    location: str


@dataclass
class StockItem:
    sku: str
    quantity: int
    warehouse_id: str


@dataclass
class PurchaseOrder:
    id: str
    sku: str
    quantity: int
    supplier: str
    status: str = "open"


@dataclass
class Telemetry:
    sku: str
    warehouse_id: str
    temperature: float
    humidity: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


# =====================================================
# STORES
# =====================================================

WAREHOUSES: Dict[str, Warehouse] = {}
INVENTORY: Dict[str, StockItem] = {}
PURCHASE_ORDERS: Dict[str, PurchaseOrder] = {}
TELEMETRY_LOGS: List[Telemetry] = []


# =====================================================
# WAREHOUSE
# =====================================================

def register_warehouse(name: str, location: str):

    wid = str(uuid.uuid4())

    WAREHOUSES[wid] = Warehouse(wid, name, location)
    return WAREHOUSES[wid]


# =====================================================
# INVENTORY
# =====================================================

def sync_inventory(sku: str, qty: int, warehouse_id: str):

    key = f"{sku}:{warehouse_id}"

    INVENTORY[key] = StockItem(sku, qty, warehouse_id)
    return INVENTORY[key]


# =====================================================
# FORECAST
# =====================================================

def forecast_demand(sku: str):

    base = random.randint(5, 50)
    return base


# =====================================================
# REORDER
# =====================================================

def auto_reorder(sku: str, warehouse_id: str, threshold=10):

    key = f"{sku}:{warehouse_id}"

    item = INVENTORY.get(key)

    if not item:
        return None

    if item.quantity < threshold:

        po = PurchaseOrder(
            id=str(uuid.uuid4()),
            sku=sku,
            quantity=threshold * 3,
            supplier="DefaultSupplier",
        )

        PURCHASE_ORDERS[po.id] = po
        return po


# =====================================================
# ROUTING
# =====================================================

def route_fulfillment(sku: str):

    choices = [
        i for i in INVENTORY.values()
        if i.sku == sku and i.quantity > 0
    ]

    return max(choices, key=lambda x: x.quantity) if choices else None


# =====================================================
# BATCH PICKING
# =====================================================

def create_pick_batch(order_skus: List[str]):

    batch = []

    for sku in order_skus:
        src = route_fulfillment(sku)
        if src:
            batch.append(src)

    return batch


# =====================================================
# IOT INGEST
# =====================================================

def ingest_telemetry(sku, warehouse_id, temperature, humidity):

    t = Telemetry(
        sku=sku,
        warehouse_id=warehouse_id,
        temperature=temperature,
        humidity=humidity,
    )

    TELEMETRY_LOGS.append(t)
    return t


# =====================================================
# SHRINKAGE
# =====================================================

def audit_shrinkage():

    flagged = []

    for i in INVENTORY.values():
        if i.quantity < 0:
            flagged.append(i)

    return flagged


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    w = register_warehouse("Lagos Hub", "NG")

    sync_inventory("SKU1", 8, w.id)

    po = auto_reorder("SKU1", w.id)

    print("REORDER:", po)

    print("FORECAST:", forecast_demand("SKU1"))