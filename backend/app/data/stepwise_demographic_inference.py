#!/usr/bin/env python3
"""
Multi-step demographic inference using OpenAI prompt caching.

For each persona, asks 5 demographic questions in sequence, leveraging
the LLM's cache (identical shared context across steps) so each step
only pays for the new question + answer tokens.

Reads:  backend/app/data/persona_details_v2.pkl (gzip)
Writes: backend/app/data/stepwise_demographic_inferences.pkl (gzip)

Output columns:
  screen_name, race_ethnicity, age, gender, education, income, description
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
OUTPUT_FILE = DATA_DIR / "stepwise_demographic_inferences_v2.pkl"
CHECKPOINT_FILE = DATA_DIR / ".stepwise_checkpoint.pkl"

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.1")

# Parallelism
BATCH_SIZE = 10
PAUSE_BETWEEN_BATCHES = 1.0

# ── Background context (shared across all 5 steps) ─────────────────────────
# This is the same for every question.  The LLM cache will store it once.
BUILDER_SYSTEM_PROMPT = (
    "You are an expert in computational social science. You will be given "
    "information about a social media user. Your task is to infer a single "
    "demographic attribute at a time. Answer ONLY with the letter of the "
    "chosen option — nothing else, no explanation, no punctuation."
)

def build_background_context(screen_name: str, description: str) -> str:
    """Build the shared context that is identical for all 5 questions about a user."""
    return (
        f"The person calls themselves: {screen_name}\n"
        f'The person self-description is: "{description}"'
    )


# ── Per-step question / answer-choices ─────────────────────────────────────
STEPS = [
    {
        "col": "race_ethnicity",
        "question": "Which of the following racial or ethnic groups do you identify with?",
        "options": (
            "(A) American Indian or Alaska Native\n"
            "(B) Asian or Asian American\n"
            "(C) Black or African American\n"
            "(D) Hispanic or Latino/a\n"
            "(E) Middle Eastern or North African\n"
            "(F) Native Hawaiian or Other Pacific Islander\n"
            "(G) White or European\n"
            "(H) Other\n"
#            "(I) Prefer not to answer"
        ),
    },
    {
        "col": "age",
        "question": "What is your age?",
        "options": (
            "(A) 18-29\n"
            "(B) 30-39\n"
            "(C) 40-49\n"
            "(D) 50-64\n"
            "(E) 65 or Above\n"
#           "(F) Prefer not to answer"
        ),
    },
    {
        "col": "gender",
        "question": "What is your gender?",
        "options": (
            "(A) Male\n"
            "(B) Female\n"
            "(C) Other (e.g., non-binary, trans)\n"
#            "(D) Prefer not to answer"
        ),
    },
    {
        "col": "education",
        "question": "What is the highest level of education you have completed?",
        "options": (
            "(A) Less than high school\n"
            "(B) High school graduate or equivalent (e.g., GED)\n"
            "(C) Some college, but no degree\n"
            "(D) Associate degree\n"
            "(E) Bachelor's degree\n"
            "(F) Professional degree (e.g., JD, MD)\n"
            "(G) Master's degree\n"
            "(H) Doctoral degree\n"
#            "(I) Prefer not to answer"
        ),
    },
    {
        "col": "income",
        "question": "What is your annual household income?",
        "options": (
            "(A) Less than $10,000\n"
            "(B) $10,000 to $19,999\n"
            "(C) $20,000 to $29,999\n"
            "(D) $30,000 to $39,999\n"
            "(E) $40,000 to $49,999\n"
            "(F) $50,000 to $59,999\n"
            "(G) $60,000 to $69,999\n"
            "(H) $70,000 to $79,999\n"
            "(I) $80,000 to $89,999\n"
            "(J) $90,000 to $99,999\n"
            "(K) $100,000 to $149,999\n"
            "(L) $150,000 to $199,999\n"
            "(M) $200,000 or more\n"
#            "(N) Prefer not to answer"
        ),
    },
]


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


def ask_step(client: OpenAI, background: str, step: dict) -> str:
    """Ask a single demographic question, relying on the background context
    being cached by the LLM from prior steps."""
    user_prompt = (
        f"{background}\n\n"
        f"{step['question']}\n\n"
        f"{step['options']}\n\n"
        "Answer only with the letter of the chosen option (e.g., A, B, C...)."
    )
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": BUILDER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_completion_tokens=10,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"ERROR: {e}"


def compile_description(row_result: dict) -> str:
    """Compile the final human-readable description from all demographic answers."""
    race = row_result.get("race_ethnicity", "Unknown")
    age = row_result.get("age", "Unknown")
    gender = row_result.get("gender", "Unknown")
    edu = row_result.get("education", "Unknown")
    income = row_result.get("income", "Unknown")
    return (
        f"Race/Ethnicity: {race}; Age: {age}; Gender: {gender}; "
        f"Education: {edu}; Income: {income}"
    )


def process_one_persona(client: OpenAI, idx: int, sn: str, description: str):
    """Run all 5 steps for a single persona."""
    background = build_background_context(sn, description)
    results = {"screen_name": sn}
    for step in STEPS:
        answer = ask_step(client, background, step)
        results[step["col"]] = answer
    results["description"] = compile_description(results)
    return idx, results


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

    df_dedup = df.drop_duplicates(subset="screen_name", keep="first")
    print(f"Persona details: {len(df)} rows, deduplicated: {len(df_dedup)} rows")

    # ── Parse optional --max arg ──────────────────────────────────────
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=None, help="Max personas to process")
    args, _ = parser.parse_known_args()

    # ── Build work queue ───────────────────────────────────────────────
    work = []
    for _, row in df_dedup.iterrows():
        sn = row["screen_name"]
        desc = row.get("description", "")
        if pd.isna(desc) or not desc:
            work.append((sn, None))
            continue
        work.append((sn, desc))

    total = len(work)
    if args.max:
        total = min(total, args.max)
        work = work[:total]
    print(f"\nProcessing {total} personas with {OPENAI_MODEL} (5 steps each)...")
    t0 = time.time()

    # ── Checkpoint recovery ────────────────────────────────────────────
    checkpoint_processed = 0
    all_results: dict[str, dict] = {}
    if CHECKPOINT_FILE.exists():
        print(f"Found checkpoint at {CHECKPOINT_FILE}, loading...")
        with gzip.open(CHECKPOINT_FILE, "rb") as f:
            checkpoint = pickle.load(f)
        processed_sns = set(checkpoint.keys())
        # Filter out already-processed users
        work = [(sn, desc) for (sn, desc) in work if sn not in processed_sns]
        checkpoint_processed = len(processed_sns)
        print(f"Recovery: {checkpoint_processed} already done, {len(work)} remaining")

    total_remaining = len(work)
    log_interval = max(1, total // 50)  # print roughly every ~100 users

    # ── Run in parallel batches ─────────────────────────────────────────
    with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
        for batch_num, start in enumerate(range(0, total_remaining, BATCH_SIZE)):
            batch = work[start : start + BATCH_SIZE]
            futures = []
            for sn, desc in batch:
                if desc is None:
                    all_results[sn] = {
                        "screen_name": sn,
                        "race_ethnicity": None,
                        "age": None,
                        "gender": None,
                        "education": None,
                        "income": None,
                        "description": None,
                    }
                    continue
                futures.append(
                    executor.submit(process_one_persona, client, start, sn, desc)
                )

            for future in as_completed(futures):
                _, results = future.result()
                sn = results["screen_name"]
                all_results[sn] = results
                done_sofar = checkpoint_processed + len(all_results)
                if done_sofar % log_interval == 0 or done_sofar == total:
                    elapsed = time.time() - t0
                    print(
                        f"[{done_sofar}/{total}] {sn} — "
                        f"race={results['race_ethnicity']} "
                        f"age={results['age']} "
                        f"gender={results['gender']} "
                        f"edu={results['education']} "
                        f"income={results['income']} "
                        f"({elapsed:.0f}s)"
                    )

            # ── Save checkpoint after each batch ────────────────────────
            checkpoint_data: dict = {}
            if CHECKPOINT_FILE.exists():
                with gzip.open(CHECKPOINT_FILE, "rb") as f:
                    checkpoint_data = pickle.load(f)
            checkpoint_data.update(all_results)
            with gzip.open(str(CHECKPOINT_FILE) + ".tmp", "wb") as f:
                pickle.dump(checkpoint_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            (CHECKPOINT_FILE.parent / (CHECKPOINT_FILE.name + ".tmp")).rename(CHECKPOINT_FILE)
            print(f"  ⏺ [batch {batch_num+1}] Checkpoint saved ({len(checkpoint_data)}/{total} users)")

            if start + BATCH_SIZE < total_remaining:
                time.sleep(PAUSE_BETWEEN_BATCHES)

    # ── Build output DataFrame (preserve original ordering) ────────────
    checkpoint_data = {}
    if CHECKPOINT_FILE.exists():
        with gzip.open(CHECKPOINT_FILE, "rb") as f:
            checkpoint_data = pickle.load(f)
    # Restore original df_dedup order
    sn_order = list(df_dedup["screen_name"])
    result_rows = [checkpoint_data[sn] for sn in sn_order if sn in checkpoint_data]
    result_df = pd.DataFrame(result_rows)

    print(f"\nSaving {len(result_df)} results to {OUTPUT_FILE}")
    with gzip.open(OUTPUT_FILE, "wb") as f:
        pickle.dump(result_df, f, protocol=pickle.HIGHEST_PROTOCOL)
    # Clean up checkpoint
    CHECKPOINT_FILE.unlink(missing_ok=True)

    total_steps = total * len(STEPS)
    success_def = result_df["description"].notna().sum()
    failed_def = result_df["description"].isna().sum()
    print(
        f"Done! Success: {success_def}, Failed: {failed_def} "
        f"({(time.time() - t0)/60:.1f} min, ~{total_steps} API calls)"
    )

    print("\n--- Sample results ---")
    sample = result_df[result_df["description"].notna()].head(5)
    for _, r in sample.iterrows():
        print(f"\n{r['screen_name']}:\n  {r['description']}")
        print(f"  [raw] race={r['race_ethnicity']} age={r['age']} "
              f"gender={r['gender']} edu={r['education']} income={r['income']}")


if __name__ == "__main__":
    main()
