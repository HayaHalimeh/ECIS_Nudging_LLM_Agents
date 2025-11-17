import re
import csv
import json
from collections import defaultdict
from pathlib import Path

# --- CONFIG ---
base_dir = Path("")
output_dir = base_dir / "data"

print(f"Base directory for results: {base_dir}")
print(f"Output directory for processed data: {output_dir}")


def parse_model_dirname(name: str) -> dict | None:
    pattern = re.compile(r"^model-(?P<model>.+?)-reasoning-(?P<reasoning>\w+)-seed-(?P<seed>\d+)$")
    match = pattern.match(name)
    return match.groupdict() if match else None


def find_selection_json(model_dir: Path) -> Path | None:
    candidates = list(model_dir.glob("selection*.json"))
    return candidates[0] if candidates else None


def load_selections(selection_path: Path) -> list[dict]:
    with selection_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "selections" in data:
        return data["selections"]
    if isinstance(data, list):
        return data
    raise ValueError(f"Unrecognized selections format in {selection_path}")


def target_for_set(set_name: str) -> str:
    return "1" if set_name == "set_a" else "2"


def rows_from_selections(
    selections: list[dict],
    *,
    condition: str,
    set_name: str,
    model: str,
    reasoning: str,
    seed: str
) -> list[dict]:
    tgt = target_for_set(set_name)
    rows: list[dict] = []

    for idx, cat in enumerate(selections, start=1):
        category = cat.get("categoryTitle") or cat.get("categoryKey") or "UNKNOWN"
        selected_val = str(cat.get("selectedValue", "")).strip()

        # Extract up to two options (safe defaults if missing)
        options = cat.get("options", [])
        opt1_title = options[0].get("title") if len(options) > 0 else ""
        opt1_value = options[0].get("value") if len(options) > 0 else ""
        opt2_title = options[1].get("title") if len(options) > 1 else ""
        opt2_value = options[1].get("value") if len(options) > 1 else ""

        rows.append({
            "condition": condition,
            "set": set_name,
            "model": model,
            "reasoning": reasoning,
            "seed": seed,
            "agent": f"{model}-reasoning-{reasoning}-seed-{seed}",
            "category": category,
            "product_order": idx,
            "option_1_title": opt1_title,
            "option_1_value": opt1_value,
            "option_2_title": opt2_title,
            "option_2_value": opt2_value,
            "target_product": tgt,
            "selected_product": selected_val,
            "target_product_selected": int(selected_val == tgt),
 
        })
    return rows


def write_csv(rows: list[dict], out_path: Path):
    fieldnames = [
        "condition", "set", "model", "reasoning", "seed", "agent",
        "category", "product_order", "option_1_title", "option_1_value",
        "option_2_title", "option_2_value", "target_product",
        "selected_product", "target_product_selected",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main():
    buckets: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    condition_names = {"defaults", "social_influence", "no_nudge"}

    for condition_dir in sorted(p for p in base_dir.iterdir() if p.is_dir() and p.name in condition_names):
        condition = condition_dir.name
        print(f"Processing condition: {condition}")

        for set_dir in sorted(p for p in condition_dir.iterdir() if p.is_dir() and p.name.startswith("set_")):
            set_name = set_dir.name
            conversations_dir = set_dir / "conversations"
            if not conversations_dir.is_dir():
                print(f"  [WARN] Missing conversations dir: {conversations_dir} (skipping)")
                continue

            for model_dir in sorted(p for p in conversations_dir.iterdir() if p.is_dir()):
                parsed = parse_model_dirname(model_dir.name)
                if not parsed:
                    print(f"  [WARN] Unrecognized model folder: {model_dir.name} (skipping)")
                    continue

                selection_path = find_selection_json(model_dir)
                if not selection_path:
                    print(f"  [WARN] No selection JSON in {model_dir} (skipping)")
                    continue

                try:
                    selections = load_selections(selection_path)
                    rows = rows_from_selections(
                        selections,
                        condition=condition,
                        set_name=set_name,
                        model=parsed["model"],
                        reasoning=parsed["reasoning"],
                        seed=parsed["seed"],
                    )
                    key = (condition, set_name, parsed["model"], parsed["reasoning"])
                    buckets[key].extend(rows)
                except Exception as e:
                    print(f"  [WARN] Failed in {model_dir}: {e}")

    for (condition, set_name, model, reasoning), rows in sorted(buckets.items()):
        out_name = f"selections_{condition}_{set_name}_{model}_reasoning-{reasoning}.csv"
        out_csv_path = output_dir / out_name
        write_csv(rows, out_csv_path)
        print(f"Wrote {len(rows)} rows -> {out_csv_path}")


if __name__ == "__main__":
    main()
