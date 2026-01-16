#!/usr/bin/env python3
"""
Script 05: Exemplar Extraction (Composite Scoring)

Selects top 10 most theoretically salient multimodal tweets per chapter
using multi-dimensional composite scoring.

Theoretical Framework:
    - Biber, D. (1988). Variation across speech and writing. Cambridge University Press.

      Biber's multi-dimensional analysis combines multiple linguistic features
      to identify text types and register variation. Composite scoring allows
      identification of prototypical instances based on theoretically relevant
      dimensions.

    - Egbert, J., & Biber, D. (2019). Register variation online. Cambridge University Press.

      Multi-feature selection for corpus analysis, balancing multiple discourse
      dimensions to identify exemplary texts.

    - Church, K. W., & Hanks, P. (1990). Word association norms, mutual
      information, and lexicography. Computational Linguistics, 16(1), 22-29.

      PMI methodology for identifying salient lexical associations.

Composite Scoring (0-8 scale per config.yaml):
    1. PMI lexical association (0-3 points): Normalized to 15.0 cap
       - Rationale: Identifies salient vaccine-related collocations
       - Theoretical basis: Church & Hanks (1990) PMI methodology

    2. Epistemic marker density (0-3 points): Normalized to 20.0 cap (markers per 100 words)
       - Rationale: Identifies intense certainty/uncertainty expression
       - Theoretical basis: Heritage (2012) epistemic stancetaking

    3. Sentiment intensity (0-2 points): Absolute VADER compound score
       - Rationale: Identifies strong affective/evaluative positioning
       - Theoretical basis: Hutto & Gilbert (2014) VADER

Selection Criteria:
    - Top 10 per chapter (N = 150 total across 15 chapters)
    - Multimodal only (verified from prior scripts)
    - Highest composite scores = most prototypical of CHD discourse patterns
    - Balanced across state chapters for geographic representation

Input Files (from Script 04):
    - data/analyzed/validated_corpus.csv (enriched multimodal data)

Output Files:
    - data/analyzed/selected_exemplars.xlsx (150 rows, 15 sheets by chapter)
    - data/analyzed/selected_exemplars.csv (flat file)
    - outputs/exemplars/{chapter}/*.png (copied PNGs for selected exemplars)
    - data/analyzed/exemplar_extraction_report.txt (summary and distribution)

Reproducibility Note (APA 7th):
    Scoring parameters configurable via config.yaml. Inductive normalization
    based on corpus stats ensures principled selection (Biber, 1988).
    Exemplars copied from multimodal_data_snaps/ for qualitative coding (Script 06).

Author: AAAL 2026 Pipeline
Date: January 2026
"""
import os
import sys
import shutil
from datetime import datetime
import pandas as pd
import yaml

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)


def load_config():
    """Load configuration from config.yaml with error handling (APA reproducibility)."""
    config_path = os.path.join(PROJECT_ROOT, 'config', 'config.yaml')
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        raise ValueError(f"Config loading error: {e}")


def setup_logging(config):
    """Setup log file with timestamp (Biber et al., 1999, for corpus audit trails)."""
    log_dir = os.path.join(PROJECT_ROOT, config['paths']['log_dir'])
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(log_dir, f'05_exemplar_extraction_{timestamp}.log')
    return log_path, timestamp


def log_message(log_path, message, also_print=True):
    """Write message to log file and optionally print."""
    with open(log_path, 'a') as f:
        f.write(f"{datetime.now().strftime('%H:%M:%S')} | {message}\n")
    if also_print:
        print(message)


def calculate_selection_score(row, weights, caps):
    """
    Calculate composite selection score (0-8 scale).

    Normalizes each feature to cap, then applies weights.
    """
    pmi_norm = min(row['pmi_sum'], caps['pmi']) / caps['pmi'] * weights['pmi_sum']
    epist_norm = min(row['epistemic_density'], caps['epistemic']) / caps['epistemic'] * weights['epistemic_density']
    sent_norm = min(abs(row['sentiment_compound']), 1.0) * weights['sentiment_intensity']

    return pmi_norm + epist_norm + sent_norm


def main():
    """Main execution function."""
    print("=" * 60)
    print("SCRIPT 05: EXEMPLAR EXTRACTION")
    print("=" * 60)
    print()

    config = load_config()
    log_path, timestamp = setup_logging(config)

    log_message(log_path, "=" * 60)
    log_message(log_path, "AAAL 2026 EXEMPLAR EXTRACTION")
    log_message(log_path, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message(log_path, "=" * 60)
    log_message(log_path, "")

    # =========================================================================
    # Step 1: Load Parameters from Config
    # =========================================================================
    log_message(log_path, "STEP 1: LOADING PARAMETERS")
    log_message(log_path, "-" * 40)

    target_per_chapter = config['selection']['target_per_chapter']
    weights = config['selection']['weights']
    caps = {
        'pmi': config['selection']['pmi_cap'],
        'epistemic': config['selection']['epistemic_cap']
    }

    log_message(log_path, f"  Target per chapter: {target_per_chapter}")
    log_message(log_path, f"  Weights: PMI={weights['pmi_sum']}, Epistemic={weights['epistemic_density']}, Sentiment={weights['sentiment_intensity']}")
    log_message(log_path, f"  Caps: PMI={caps['pmi']}, Epistemic={caps['epistemic']}")
    log_message(log_path, "")

    # =========================================================================
    # Step 2: Load Input Data (Flat CSV from Script 04)
    # =========================================================================
    log_message(log_path, "STEP 2: LOADING INPUT DATA")
    log_message(log_path, "-" * 40)

    input_path = os.path.join(PROJECT_ROOT, config['paths']['analyzed_dir'], 'validated_corpus.csv')

    if not os.path.exists(input_path):
        log_message(log_path, f"ERROR: Input file missing: {input_path}")
        return 1

    df = pd.read_csv(input_path, low_memory=False)
    df['sentiment_abs'] = abs(df['sentiment_compound'])

    log_message(log_path, f"  Loaded {len(df)} rows from {input_path}")
    log_message(log_path, "")

    # =========================================================================
    # Step 3: Calculate Composite Scores
    # =========================================================================
    log_message(log_path, "STEP 3: CALCULATING COMPOSITE SCORES")
    log_message(log_path, "-" * 40)

    df['selection_score'] = df.apply(
        lambda row: calculate_selection_score(row, weights, caps), axis=1
    )

    log_message(log_path, f"  Scores range: {df['selection_score'].min():.3f} - {df['selection_score'].max():.3f}")
    log_message(log_path, "")

    # =========================================================================
    # Step 4: Select Exemplars (Top N per Chapter)
    # =========================================================================
    log_message(log_path, "STEP 4: SELECTING EXEMPLARS")
    log_message(log_path, "-" * 40)

    exemplars_df = pd.DataFrame()
    chapter_list = sorted(df['chapter_code'].unique())

    for chapter in chapter_list:
        chapter_data = df[df['chapter_code'] == chapter]
        top_n = chapter_data.nlargest(target_per_chapter, 'selection_score')
        exemplars_df = pd.concat([exemplars_df, top_n])

        log_message(log_path, f"  {chapter}: Selected {len(top_n)} exemplars (mean score: {top_n['selection_score'].mean():.3f})")

    exemplars_df = exemplars_df.sort_values(['chapter_code', 'selection_score'], ascending=[True, False])
    log_message(log_path, f"  Total exemplars: {len(exemplars_df)}")
    log_message(log_path, "")

    # =========================================================================
    # Step 5: Copy Exemplar PNGs
    # =========================================================================
    log_message(log_path, "STEP 5: COPYING EXEMPLAR PNGs")
    log_message(log_path, "-" * 40)

    png_source = os.path.join(PROJECT_ROOT, 'outputs', 'multimodal_data_snaps')
    png_dest = os.path.join(PROJECT_ROOT, config['paths']['output_dir'], 'exemplars')
    os.makedirs(png_dest, exist_ok=True)

    copy_stats = {'copied': 0, 'missing': 0, 'errors': 0}

    for _, row in exemplars_df.iterrows():
        src_path = os.path.join(png_source, row['chapter_code'], f"{row['data_snap_source']}.png")
        if not os.path.exists(src_path):
            copy_stats['missing'] += 1
            continue

        try:
            chapter_dir = os.path.join(png_dest, row['chapter_code'])
            os.makedirs(chapter_dir, exist_ok=True)
            dest_path = os.path.join(chapter_dir, f"{row['data_snap_source']}.png")
            shutil.copy(src_path, dest_path)
            copy_stats['copied'] += 1
        except Exception as e:
            copy_stats['errors'] += 1
            log_message(log_path, f"  Error copying {row['data_snap_source']}: {e}")

    log_message(log_path, f"  PNG copy stats: {copy_stats}")
    log_message(log_path, "")

    # =========================================================================
    # Step 6: Save Exemplars Output
    # =========================================================================
    log_message(log_path, "STEP 6: SAVING EXEMPLARS OUTPUT")
    log_message(log_path, "-" * 40)

    analyzed_dir = os.path.join(PROJECT_ROOT, config['paths']['analyzed_dir'])
    excel_path = os.path.join(analyzed_dir, 'selected_exemplars.xlsx')
    csv_path = os.path.join(analyzed_dir, 'selected_exemplars.csv')

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for chapter_full in config['chapters']:
            chapter_code = chapter_full.replace('CHD_', '').rstrip('_')
            chapter_exemplars = exemplars_df[exemplars_df['chapter_code'] == chapter_code]
            chapter_exemplars.to_excel(writer, sheet_name=chapter_full, index=False)

    exemplars_df.to_csv(csv_path, index=False)

    total_exemplars = len(exemplars_df)
    total_sheets = len(config['chapters'])
    log_message(log_path, f"  Excel saved: {excel_path} ({total_exemplars} rows, {total_sheets} sheets)")
    log_message(log_path, f"  CSV saved: {csv_path} ({total_exemplars} rows)")
    log_message(log_path, "")

    # =========================================================================
    # Step 7: Generate Exemplar Extraction Report
    # =========================================================================
    log_message(log_path, "STEP 7: GENERATING EXTRACTION REPORT")
    log_message(log_path, "-" * 40)

    report_path = os.path.join(analyzed_dir, 'exemplar_extraction_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("AAAL 2026 EXEMPLAR EXTRACTION REPORT\n")
        f.write(f"Generated: {timestamp}\n")
        f.write("=" * 60 + "\n\n")

        f.write("THEORETICAL FRAMEWORK:\n")
        f.write("  Biber, D. (1988). Variation across speech and writing.\n")
        f.write("  Cambridge University Press.\n\n")
        f.write("  Egbert, J., & Biber, D. (2019). Register variation online.\n")
        f.write("  Cambridge University Press.\n\n")

        f.write("SELECTION PARAMETERS:\n")
        f.write(f"  Target per chapter: {target_per_chapter}\n")
        f.write(f"  Weights: PMI={weights['pmi_sum']}, Epistemic={weights['epistemic_density']}, Sentiment={weights['sentiment_intensity']}\n")
        f.write(f"  Caps: PMI={caps['pmi']}, Epistemic={caps['epistemic']}\n\n")

        f.write("CORPUS SUMMARY:\n")
        f.write(f"  Total exemplars selected: {total_exemplars} ({target_per_chapter * len(chapter_list)} target)\n")
        f.write(f"  Mean score: {exemplars_df['selection_score'].mean():.3f}\n")
        f.write(f"  Score range: {exemplars_df['selection_score'].min():.3f} - {exemplars_df['selection_score'].max():.3f}\n\n")

        f.write("CHAPTER BREAKDOWN:\n")
        f.write(f"  {'Chapter':<12} {'N':>4} {'Mean':>8} {'Min':>8} {'Max':>8}\n")
        f.write(f"  {'-'*12} {'-'*4} {'-'*8} {'-'*8} {'-'*8}\n")
        for chapter in sorted(chapter_list):
            chapter_code = chapter.replace('CHD_', '').rstrip('_')
            chapter_exemplars = exemplars_df[exemplars_df['chapter_code'] == chapter_code]
            if len(chapter_exemplars) > 0:
                c_mean = chapter_exemplars['selection_score'].mean()
                c_min = chapter_exemplars['selection_score'].min()
                c_max = chapter_exemplars['selection_score'].max()
                f.write(f"  {chapter:<12} {len(chapter_exemplars):>4} {c_mean:>8.3f} {c_min:>8.3f} {c_max:>8.3f}\n")

        f.write("\nTOP 10 EXEMPLARS (Corpus-Wide):\n")
        f.write(f"  {'ID':<12} {'Chapter':<8} {'Score':>6} {'PMI':>6} {'Epist':>6} {'Sent':>6}\n")
        f.write(f"  {'-'*12} {'-'*8} {'-'*6} {'-'*6} {'-'*6} {'-'*6}\n")
        top_10 = exemplars_df.nlargest(10, 'selection_score')
        for _, row in top_10.iterrows():
            f.write(f"  {row['data_snap_source']:<12} {row['chapter_code']:<8} "
                   f"{row['selection_score']:>6.2f} {row.get('pmi_sum', 0):>6.2f} "
                   f"{row.get('epistemic_density', 0):>6.2f} {row.get('sentiment_abs', 0):>6.2f}\n")

        f.write("\nPNG COPY STATS:\n")
        f.write(f"  Copied: {copy_stats['copied']}\n")
        f.write(f"  Missing: {copy_stats['missing']}\n")
        f.write(f"  Errors: {copy_stats['errors']}\n")
        f.write(f"  Destination: {png_dest}\n\n")

        f.write("OUTPUT FILES:\n")
        f.write(f"  {excel_path}\n")
        f.write(f"    -> {total_exemplars} exemplars, {total_sheets} sheets\n")
        f.write(f"  {csv_path}\n")
        f.write(f"    -> Flat file for external analysis\n")
        f.write(f"  {png_dest}/\n")
        f.write(f"    -> {copy_stats['copied']} exemplar PNGs\n")

    log_message(log_path, f"  Report saved: {report_path}")
    log_message(log_path, "")

    # =========================================================================
    # Final Summary
    # =========================================================================
    log_message(log_path, "=" * 60)
    log_message(log_path, "SCRIPT 05 COMPLETE - EXEMPLAR EXTRACTION")
    log_message(log_path, "=" * 60)
    log_message(log_path, f"Total exemplars: {total_exemplars} (target: {target_per_chapter * len(chapter_list)})")
    log_message(log_path, f"Mean score: {exemplars_df['selection_score'].mean():.3f}")
    log_message(log_path, f"Score range: {exemplars_df['selection_score'].min():.3f} - {exemplars_df['selection_score'].max():.3f}")
    log_message(log_path, f"PNGs copied: {copy_stats['copied']}")
    log_message(log_path, f"Output Excel: {excel_path}")
    log_message(log_path, f"Output CSV: {csv_path}")
    log_message(log_path, f"Log: {log_path}")
    log_message(log_path, f"Report: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
