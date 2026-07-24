#!/usr/bin/env python3
"""
Run demographic inference on each persona row using OpenAI - parallel batch version.

Reads: backend/app/data/persona_details_v2.pkl (gzip)
       backend/app/data/persona_v2_accounts_they_follow.pkl
Writes: backend/app/data/demographic_inferences_v2.pkl (gzip)
"""
import gzip
import os
import pickle
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from openai import OpenAI

# ── Config ──────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).resolve().parent
PERSONA_FILE = DATA_DIR / "persona_details_v2.pkl"
ACCOUNTS_FILE = DATA_DIR / "persona_v2_accounts_they_follow.pkl"
OUTPUT_FILE = DATA_DIR / "demographic_inferences_v2.pkl"

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")

# Parallelism
BATCH_SIZE = 10  # concurrent requests per batch
PAUSE_BETWEEN_BATCHES = 1.0  # seconds pause between batches

# ── System Prompt ──────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are an expert in computational social science. Your task is to analyze "
    "the provided user data (self-description, location, and followed accounts) "
    "and infer their foundational sociodemographic attributes to create a demographic-only persona.\n\n"
    "You must completely anonymize the user and output **only** a structured demographic "
    "attribute vector formatted as a single semicolon-separated string. Do not include any "
    "narrative text, psychological traits, or explanations.\n\n"
    "Use the following exact format and fill in the inferred details with the most plausible categories:\n\n"
    "Select Your Age: [Age Range]; Gender: [Gender]; Education: [Education Level]; "
    "Occupation: [Occupation]; Country: [Country]; Race/Ethnicity: [Race/Ethnicity]; "
    "Nationality: [Nationality]; Relationship: [Relationship Status]; "
    "Political Orientation: [Political Orientation]; Income Category: [Income Range]; "
    "Religion: [Religion]."
)


def build_user_message(screen_name: str, description: str, followed_str: str) -> str:
    return (
        f"- **The person calls themselves:** {screen_name}\n"
        f'- **The person self-description is:** "{description}"\n'
        f"- **The list of accounts that the person follows include:** {followed_str}"
    )


def format_accounts(account_list) -> str:
    if not account_list or (isinstance(account_list, float) and pd.isna(account_list)):
        return "None"
    if isinstance(account_list, str):
        try:
            account_list = eval(account_list)
        except Exception:
            pass
    if not isinstance(account_list, (list, tuple)):
        account_list = [str(account_list)]
    sample = list(account_list)[:30]
    return ", ".join(str(a) for a in sample)


def get_api_key() -> str:
    k = os.environ.get("OPENAI_API_KEY", "")
    if not k:
        env_file = DATA_DIR.parents[1] / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("OPENAI_API_KEY="):
                        k = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    return k


def call_llm(client: OpenAI, idx: int, sn: str, user_msg: str):
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.0,
            max_tokens=300,
        )
        result = resp.choices[0].message.content.strip()
        return idx, sn, result, True
    except Exception as e:
        print(f"\n  ERROR [{idx}] {sn}: {e}", file=sys.stderr)
        return idx, sn, None, False


def main():
    api_key = get_api_key()
    if not api_key:
        print("ERROR: No OPENAI_API_KEY found.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # ── Load data ──────────────────────────────────────────────────────
    print("Loading persona details (gzipped pickle)...")
    with gzip.open(PERSONA_FILE, "rb") as f:
        df = pickle.load(f)

    print("Loading accounts they follow (pickle)...")
    with open(ACCOUNTS_FILE, "rb") as f:
        accounts_df = pickle.load(f)

    print(f"Persona details: {len(df)} rows")
    print(f"Accounts file: {len(accounts_df)} rows")

    df_dedup = df.drop_duplicates(subset="screen_name", keep="first")
    print(f"Deduplicated persona details: {len(df_dedup)} rows")

    merged = accounts_df.merge(
        df_dedup[["screen_name", "description"]],
        on="screen_name",
        how="left",
    )
    print(f"Merged: {len(merged)} rows, missing descriptions: {merged['description'].isna().sum()}")

    # ── Build prompt list ──────────────────────────────────────────────
    rows = []
    for _, row in merged.iterrows():
        sn = row["screen_name"]
        desc = row.get("description", "")
        if pd.isna(desc) or not desc:
            rows.append((sn, None, None))
            continue
        user_msg = build_user_message(sn, desc, format_accounts(row["account"]))
        rows.append((sn, user_msg, None))

    total = len(rows)
    print(f"\nProcessing {total} personas with model {OPENAI_MODEL}...")
    t0 = time.time()

    # ── Run inference in parallel batches ──────────────────────────────
    with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
        for start in range(0, total, BATCH_SIZE):
            batch = rows[start : start + BATCH_SIZE]
            futures = []
            for offset, (sn, user_msg, _) in enumerate(batch):
                idx = start + offset
                if user_msg is None:
                    print(f"[{idx+1}/{total}] {sn} — SKIP (no description)")
                    continue
                futures.append(executor.submit(call_llm, client, idx, sn, user_msg))

            for future in as_completed(futures):
                idx, sn, result, success = future.result()
                rows[idx] = (sn, rows[idx][1], result)
                elapsed = time.time() - t0
                status = "OK" if success else "FAILED"
                print(f"[{idx+1}/{total}] {sn}... {status}  ({elapsed:.0f}s)")

            # Brief pause between batches
            if start + BATCH_SIZE < total:
                time.sleep(PAUSE_BETWEEN_BATCHES)

    # ── Save results ───────────────────────────────────────────────────
    result_df = pd.DataFrame(
        [(sn, result) for sn, _, result in rows],
        columns=["screen_name", "demographic_inference"],
    )

    print(f"\nSaving {len(result_df)} results to {OUTPUT_FILE}")
    with gzip.open(OUTPUT_FILE, "wb") as f:
        pickle.dump(result_df, f, protocol=pickle.HIGHEST_PROTOCOL)

    success = result_df["demographic_inference"].notna().sum()
    failed = result_df["demographic_inference"].isna().sum()
    print(f"Done! Success: {success}, Failed: {failed} ({(time.time() - t0)/60:.1f} min)")

    print("\n--- Sample results ---")
    sample = result_df[result_df["demographic_inference"].notna()].head(5)
    for _, r in sample.iterrows():
        print(f"\n{r['screen_name']}:\n  {r['demographic_inference']}")


if __name__ == "__main__":
    main()
