#!/usr/bin/env python3
"""
Convert нийт.xlsx → data/stock.json
Run: python scripts/build_data.py
"""

import pandas as pd
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXCEL = ROOT / "data" / "нийт.xlsx"
OUT   = ROOT / "data" / "stock.json"

BRANCH_MAP = {
    "Очир салбар": {
        "Жижиг бараа": ["Очир хотхон", "Очир том сэлбэг"],
        "Том бараа":   ["Очир хотхон том"],
    },
    "25 салбар": {
        "Жижиг бараа": ["25 салбар", "25 том сэлбэг"],
        "Том бараа":   ["25 салбар том"],
    },
    "Д1000 салбар": {
        "Жижиг бараа": ["Дэнжийн1000 салбар", "Дэнж1000 том сэлбэг"],
        "Том бараа":   ["Дэнжийн 1000 том", "Дэнж 1000 том хуучин"],
    },
    "Мишээл салбар": {
        "Жижиг бараа": ["Мишээл салбар"],
        "Том бараа":   ["Мишээл том"],
    },
    "Алтан-Орд салбар": {
        "Жижиг бараа": ["Алтан орд"],
        "Том бараа":   ["Altanord tom"],
    },
    "Чулуун овоо салбар": {
        "Жижиг бараа": ["Салбар нарантуул"],
        "Том бараа":   ["Чулуун овоо том"],
    },
}

WAREHOUSE_MAP = {
    "Жижиг бараа": ["Агуулах", "Агуулах - 2", "Агуулах жижиг 4", "Агуулах-3"],
    "Том бараа":   ["агуулах tom 1", "Агуулах том  2", "Нөөц агуулах"],
}

TYPE_KEY = {"Жижиг бараа": "жижиг", "Том бараа": "том"}


def load_df():
    print(f"Reading {EXCEL} …")
    df = pd.read_excel(EXCEL)
    df["Тоо"]        = pd.to_numeric(df["Тоо"], errors="coerce").fillna(0)
    df["Барааны код"] = df["Барааны код"].fillna("").astype(str).str.strip()
    df["Барааны нэр"] = df["Барааны нэр"].fillna("Тодорхойгүй").astype(str).str.strip()
    df["Салбар"]      = df["Салбар"].astype(str).str.strip()
    return df


def build_missing(df):
    result = {}
    for item_type_mn, type_key in TYPE_KEY.items():
        result[type_key] = {}
        type_df = df[df["Байршил"] == item_type_mn]
        wh_names = WAREHOUSE_MAP[item_type_mn]
        wh_df = type_df[type_df["Салбар"].isin(wh_names)]
        wh_agg = (
            wh_df.groupby(["Барааны код", "Барааны нэр"])["Тоо"]
            .sum()
            .reset_index()
            .rename(columns={"Тоо": "агуулах"})
        )
        wh_items = set(wh_agg[wh_agg["агуулах"] > 0]["Барааны код"])

        for branch_name, branch_data in BRANCH_MAP.items():
            raw_names = branch_data.get(item_type_mn, [])
            branch_df = type_df[type_df["Салбар"].isin(raw_names)]
            branch_agg = (
                branch_df.groupby(["Барааны код", "Барааны нэр"])["Тоо"]
                .sum()
                .reset_index()
                .rename(columns={"Тоо": "салбар_тоо"})
            )
            branch_items = set(branch_agg[branch_agg["салбар_тоо"] > 0]["Барааны код"])
            missing_codes = wh_items - branch_items
            missing = wh_agg[wh_agg["Барааны код"].isin(missing_codes)].copy()
            missing = missing.rename(columns={"Барааны код": "код", "Барааны нэр": "нэр"})
            result[type_key][branch_name] = missing.to_dict("records")
            print(f"  {type_key} / {branch_name}: {len(missing)} missing items")

    return result


def build_imbalance(df):
    result = {}
    for item_type_mn, type_key in TYPE_KEY.items():
        type_df = df[df["Байршил"] == item_type_mn]
        wh_raw = WAREHOUSE_MAP[item_type_mn]
        all_items = (
            type_df[["Барааны код", "Барааны нэр"]]
            .drop_duplicates()
            .query("`Барааны код` != ''")
        )

        rows = []
        for _, item_row in all_items.iterrows():
            code = item_row["Барааны код"]
            name = item_row["Барааны нэр"]
            item_df = type_df[type_df["Барааны код"] == code]

            branch_stocks = {}
            total_branch = 0
            for branch_name, branch_data in BRANCH_MAP.items():
                raw_names = branch_data.get(item_type_mn, [])
                qty = float(item_df[item_df["Салбар"].isin(raw_names)]["Тоо"].sum())
                branch_stocks[branch_name] = qty
                total_branch += qty

            wh_stock = float(item_df[item_df["Салбар"].isin(wh_raw)]["Тоо"].sum())
            total = total_branch + wh_stock
            if total == 0:
                continue

            is_imbalanced = False
            if total_branch > 1:
                for qty in branch_stocks.values():
                    if qty / total_branch > 0.70:
                        is_imbalanced = True
                        break

            if is_imbalanced:
                rows.append({"код": code, "нэр": name, **branch_stocks,
                              "агуулах": wh_stock, "нийт": total})

        result[type_key] = rows
        print(f"  {type_key} imbalanced: {len(rows)} items")

    return result


def main():
    if not EXCEL.exists():
        print(f"ERROR: {EXCEL} not found", file=sys.stderr)
        sys.exit(1)

    df = load_df()
    print("Building missing-items data …")
    missing = build_missing(df)
    print("Building imbalance data …")
    imbalance = build_imbalance(df)

    payload = {
        "missing":   missing,
        "imbalance": imbalance,
        "branches":  list(BRANCH_MAP.keys()),
        "generated": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
    }

    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    print(f"\n✅  Written {OUT}  ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
