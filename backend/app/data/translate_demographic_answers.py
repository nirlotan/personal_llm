#!/usr/bin/env python3
"""
Read the stepwise demographic inference CSV and translate letter-based answers
into human-readable text. No LLM calls — uses the same option mappings defined
in the original questions.

Input:  backend/app/data/stepwise_demographic_inferences.pkl (gzip)
        OR any CSV output from the stepwise script with columns:
        screen_name, race_ethnicity, age, gender, education, income

Also joins the original persona description from persona_details_v2.pkl.

Input:  backend/app/data/stepwise_demographic_inferences.pkl (gzip)
        OR any CSV output from the stepwise script with columns:
        screen_name, race_ethnicity, age, gender, education, income
        backend/app/data/persona_details_v2.pkl (gzip) — for original description

Output: backend/app/data/stepwise_demographic_translated.csv
        Columns: screen_name, description, sythia_description
"""
import gzip
import pickle
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent

# ── Option mappings (mirrors the questions in stepwise_demographic_inference.py) ──

RACE_ETHNICITY = {
    "A": "American Indian or Alaska Native",
    "B": "Asian or Asian American",
    "C": "Black or African American",
    "D": "Hispanic or Latino/a",
    "E": "Middle Eastern or North African",
    "F": "Native Hawaiian or Other Pacific Islander",
    "G": "White or European",
    "H": "Other",
    "I": "Prefer not to answer",
}

AGE = {
    "A": "18-29",
    "B": "30-39",
    "C": "40-49",
    "D": "50-64",
    "E": "65 or Above",
    "F": "Prefer not to answer",
}

GENDER = {
    "A": "Male",
    "B": "Female",
    "C": "Other",
    "D": "Prefer not to answer",
}

EDUCATION = {
    "A": "Less than high school",
    "B": "High school graduate or equivalent",
    "C": "Some college, but no degree",
    "D": "Associate degree",
    "E": "Bachelor's degree",
    "F": "Professional degree",
    "G": "Master's degree",
    "H": "Doctoral degree",
    "I": "Prefer not to answer",
}

INCOME = {
    "A": "Less than $10,000",
    "B": "$10,000 to $19,999",
    "C": "$20,000 to $29,999",
    "D": "$30,000 to $39,999",
    "E": "$40,000 to $49,999",
    "F": "$50,000 to $59,999",
    "G": "$60,000 to $69,999",
    "H": "$70,000 to $79,999",
    "I": "$80,000 to $89,999",
    "J": "$90,000 to $99,999",
    "K": "$100,000 to $149,999",
    "L": "$150,000 to $199,999",
    "M": "$200,000 or more",
    "N": "Prefer not to answer",
}

FIELD_MAP = {
    "age": ("Age", AGE),
    "gender": ("Gender", GENDER),
    "education": ("Education", EDUCATION),
    "race_ethnicity": ("Race/Ethnicity", RACE_ETHNICITY),
    "income": ("Income", INCOME),
}


def load_dataframe(input_path: str | None = None) -> pd.DataFrame:
    """Try to load from the given path, or auto-detect."""
    if input_path:
        p = Path(input_path)
        print(f"Loading {p}...")
        if p.suffix == ".pkl":
            if str(p).endswith(".pkl.gz") or str(p).endswith(".pkl"):
                with gzip.open(p, "rb") as f:
                    return pickle.load(f)
        return pd.read_csv(p)

    pkl_path = DATA_DIR / "stepwise_demographic_inferences.pkl"
    csv_path = DATA_DIR / "stepwise_demographic_inferences.csv"

    if pkl_path.exists():
        print(f"Loading {pkl_path}...")
        with gzip.open(pkl_path, "rb") as f:
            return pickle.load(f)
    elif csv_path.exists():
        print(f"Loading {csv_path}...")
        return pd.read_csv(csv_path)
    else:
        # Try the test output as fallback
        for test_csv_name in ["stepwise_test_20samples.csv", "stepwise_test_20samples_4o.csv"]:
            test_csv = DATA_DIR / test_csv_name
            if test_csv.exists():
                print(f"No main output found. Loading test file {test_csv}...")
                return pd.read_csv(test_csv)
        raise FileNotFoundError(
            "No stepwise inference output found. Run stepwise_demographic_inference.py first."
        )


def translate_letter(letter: str, mapping: dict) -> str:
    """Translate a single letter answer to its textual form."""
    if letter is None or (isinstance(letter, float) and pd.isna(letter)):
        return "Unknown"
    letter = str(letter).strip().upper()
    # Handle cases where the answer might be "A" or "(A)" or contain extra text
    for key, value in mapping.items():
        if letter == key or letter == f"({key})":
            return value
    # If it starts with a known letter but has suffix, still try
    if letter and letter[0] in mapping:
        return mapping[letter[0]]
    return letter  # return as-is if unrecognized


def build_description(row: dict) -> str:
    """Build a readable description from the row's demographic answers."""
    parts = []
    for col, (label, mapping) in FIELD_MAP.items():
        raw = row.get(col)
        text = translate_letter(raw, mapping)
        parts.append(f"{label}: {text}")
    return "; ".join(parts)


def load_persona_details() -> pd.DataFrame:
    """Load original persona descriptions for joining."""
    pkl_path = DATA_DIR / "persona_details_v2.pkl"
    print(f"Loading original persona descriptions from {pkl_path}...")
    with gzip.open(pkl_path, "rb") as f:
        df = pickle.load(f)
    df_dedup = df.drop_duplicates(subset="screen_name", keep="first")
    return df_dedup[["screen_name", "description"]]


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", help="Input CSV/pkl file path (auto-detect if omitted)")
    parser.add_argument("--output", "-o", help="Output CSV path (defaults to stepwise_demographic_translated.csv)")
    args = parser.parse_args()

    # Load inference results
    df = load_dataframe(args.input)
    print(f"Loaded {len(df)} rows from inference output")

    # Load original persona descriptions and inner merge
    persona_df = load_persona_details()
    # Drop any existing description column from inference output to avoid collision
    cols_to_merge = [c for c in df.columns if c != "description"]
    merged = df[cols_to_merge].merge(persona_df, on="screen_name", how="inner")
    print(f"Merged with original descriptions: {len(merged)} rows (inner join)")

    # Verify expected columns exist
    expected_cols = list(FIELD_MAP.keys())
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        print(f"WARNING: Missing columns: {missing}. Available: {list(df.columns)}")
        # Try to work with whatever columns are available
        usable = {c: v for c, v in FIELD_MAP.items() if c in df.columns}
        if not usable:
            print("ERROR: No usable demographic columns found.", file=sys.stderr)
            sys.exit(1)
        field_map = usable
    else:
        field_map = FIELD_MAP

    descriptions = []
    for _, row in merged.iterrows():
        parts = []
        for col, (label, mapping) in field_map.items():
            raw = row.get(col)
            text = translate_letter(raw, mapping)
            parts.append(f"{label}: {text}")

        descriptions.append({
            "screen_name": row.get("screen_name", ""),
            "description": row.get("description", ""),
            "sythia_description": "; ".join(parts),
        })

    out_df = pd.DataFrame(descriptions)
    out_path = Path(args.output) if args.output else DATA_DIR / "stepwise_demographic_translated.csv"
    out_df.to_csv(out_path, index=False)
    print(f"Saved {len(out_df)} rows to {out_path}")

    print("\n--- Sample translations ---")
    for _, r in out_df.head(5).iterrows():
        print(f"\n  {r['screen_name']}:")
        print(f"  {r['sythia_description']}")


if __name__ == "__main__":
    main()
