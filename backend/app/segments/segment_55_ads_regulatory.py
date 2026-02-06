"""
=====================================================
FLIPTRYBE SEGMENT 55
ADS REGULATORY & TAX REPORTING
=====================================================
Produces:
monthly advertiser statements,
VAT calculations,
audit exports,
regulator-ready CSV feeds.
=====================================================
"""

import csv
import time
from pathlib import Path
from typing import Dict, List

from app.segments.segment_50_ads_billing import INVOICES, WALLETS


ROOT = Path.cwd() / "regulatory_exports"
ROOT.mkdir(exist_ok=True)


VAT_RATE = 0.075  # Nigeria VAT


# =====================================================
# MONTHLY STATEMENT
# =====================================================

def monthly_statement(merchant_id: int, month: int, year: int):

    rows = []

    for inv in INVOICES.values():

        t = time.localtime(inv.created_ts)

        if (
            inv.merchant_id == merchant_id
            and t.tm_mon == month
            and t.tm_year == year
        ):

            rows.append(inv)

    subtotal = sum(r.amount for r in rows)
    vat = subtotal * VAT_RATE
    total = subtotal + vat

    return {
        "merchant_id": merchant_id,
        "month": month,
        "year": year,
        "subtotal": subtotal,
        "vat": vat,
        "total": total,
        "count": len(rows),
    }


# =====================================================
# EXPORT CSV
# =====================================================

def export_csv(merchant_id: int, month: int, year: int):

    statement = monthly_statement(merchant_id, month, year)

    fname = ROOT / f"ads_statement_{merchant_id}_{month}_{year}.csv"

    with open(fname, "w", newline="") as f:

        writer = csv.writer(f)

        writer.writerow(
            [
                "merchant_id",
                "month",
                "year",
                "subtotal",
                "vat",
                "total",
                "invoice_count",
            ]
        )

        writer.writerow(
            [
                statement["merchant_id"],
                statement["month"],
                statement["year"],
                statement["subtotal"],
                statement["vat"],
                statement["total"],
                statement["count"],
            ]
        )

    return fname


# =====================================================
# REGULATOR BULK EXPORT
# =====================================================

def regulator_export(month: int, year: int):

    fname = ROOT / f"ads_regulator_{month}_{year}.csv"

    with open(fname, "w", newline="") as f:

        writer = csv.writer(f)

        writer.writerow(
            [
                "merchant_id",
                "subtotal",
                "vat",
                "total",
            ]
        )

        merchants = {
            inv.merchant_id
            for inv in INVOICES.values()
            if time.localtime(inv.created_ts).tm_mon == month
        }

        for mid in merchants:

            s = monthly_statement(mid, month, year)

            writer.writerow(
                [
                    mid,
                    s["subtotal"],
                    s["vat"],
                    s["total"],
                ]
            )

    return fname


# =====================================================
# AUDIT SUMMARY
# =====================================================

def audit_summary():

    total_spend = sum(inv.amount for inv in INVOICES.values())

    vat_total = total_spend * VAT_RATE

    return {
        "invoice_count": len(INVOICES),
        "gross": total_spend,
        "vat": vat_total,
        "net": total_spend - vat_total,
    }


# =====================================================
# TEST HARNESS
# =====================================================

if __name__ == "__main__":

    from app.segments.segment_50_ads_billing import fund_wallet, debit_for_click
    from app.segments.segment_49_ads_engine import AdCampaign

    fund_wallet(8, 10000)

    camp = AdCampaign(
        campaign_id=91,
        merchant_id=8,
        listing_id=77,
        max_cpc=200,
        daily_budget=5000,
        geo_targets=["ibadan"],
        categories=["furniture"],
    )

    for _ in range(5):
        debit_for_click(campaign=camp, cpc=150)

    print(monthly_statement(8, time.localtime().tm_mon, time.localtime().tm_year))
    print(export_csv(8, time.localtime().tm_mon, time.localtime().tm_year))