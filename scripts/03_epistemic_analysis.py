#!/usr/bin/env python3
"""
Script 03: Epistemic Stance Analysis (Heritage 2012, Hyland 1998, Hinkel 2005)

Classifies epistemic stance using validated hedge and booster lexicons
from corpus linguistics research.

Theoretical Framework:
    - Heritage, J. (2012). Epistemic engine: Sequence organization and
      territories of knowledge. Research on Language and Social Interaction, 45(1), 30-52.

      Heritage's K+/K- framework analyzes how speakers position themselves
      regarding epistemic authority (rights to know):
      - K+ = High epistemic authority ("I know for certain")
      - K- = Lower epistemic authority ("I believe it might be")

    - Hyland, K. (1998). Hedging in scientific research articles.
      John Benjamins Publishing.

      Hyland identified hedges (uncertainty markers) and boosters (certainty
      markers) as key metadiscourse features in academic writing.

    - Hinkel, E. (2005). Hedging, inflating, and persuading in L2 academic writing.
      Applied Language Learning, 15(1&2), 29-53.

      Hinkel validated hedge/booster lexicons across multiple registers.

Classification Rules:
    - K+ (high certainty): Booster-dominant, >=2 boosters
    - K- (low certainty): Hedge-dominant, >=2 hedges
    - Mixed: Both hedge >=1 and booster >=1 present
    - Neutral: No epistemic markers detected

Threshold Rationale (min_for_stance = 2):
    One marker could be incidental or formulaic. Two or more markers
    suggest intentional epistemic positioning, reducing noise and
    increasing classification reliability.

Epistemic Density:
    Total markers per 100 words, following Biber et al. (1999) corpus
    linguistics normalization standard.

Input Files (from Script 02):
    - data/analyzed/pmi_analyzed.xlsx (15 sheets by chapter, enriched multimodal data)

Output Files:
    - data/analyzed/epistemic_analyzed.xlsx (15 sheets by chapter, with stance/density)
    - data/analyzed/epistemic_analysis_report.txt (summary stats and distribution)

Reproducibility Note (APA 7th):
    Hedge/booster lists loaded from config.yaml (validated sources: Hyland, 1998; Hinkel, 2005).
    Parameters configurable via config.yaml. Processes multimodal corpus only,
    preserving traceability for forensic discourse analysis.

Author: AAAL 2026 Pipeline
Date: January 2026
"""
import os
import sys
import re
from datetime import datetime
import pandas as pd
import yaml
from collections import defaultdict, Counter

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)


def load_config():
    """Load configuration from config.yaml with error handling."""
    config_path = os.path.join(PROJECT_ROOT, 'config', 'config.yaml')
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        raise ValueError(f"Config loading error: {e}")


def setup_logging(config):
    """Setup log file with timestamp."""
    log_dir = os.path.join(PROJECT_ROOT, config['paths']['log_dir'])
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(log_dir, f'03_epistemic_analysis_{timestamp}.log')
    return log_path, timestamp


def log_message(log_path, message, also_print=True):
    """Write message to log file and optionally print."""
    with open(log_path, 'a') as f:
        f.write(f"{datetime.now().strftime('%H:%M:%S')} | {message}\n")
    if also_print:
        print(message)


def count_markers(text, markers):
    """Count occurrences of markers in text (case-insensitive)."""
    count = 0
    text_lower = text.lower()
    for marker in markers:
        count += len(re.findall(r'\b' + re.escape(marker) + r'\b', text_lower))
    return count


def classify_stance(hedge_count, booster_count, min_threshold):
    """Classify epistemic stance based on counts."""
    if booster_count >= min_threshold and booster_count > hedge_count:
        return 'K+ (high certainty)'
    elif hedge_count >= min_threshold and hedge_count > booster_count:
        return 'K- (low certainty)'
    elif hedge_count >= 1 and booster_count >= 1:
        return 'Mixed'
    else:
        return 'Neutral'


def calculate_density(hedge_count, booster_count, word_count):
    """Calculate epistemic density (markers per 100 words)."""
    total_markers = hedge_count + booster_count
    return (total_markers / word_count * 100) if word_count > 0 else 0


def main():
    """Main execution function."""
    print("=" * 60)
    print("SCRIPT 03: EPISTEMIC STANCE ANALYSIS")
    print("=" * 60)
    print()

    config = load_config()
    log_path, timestamp = setup_logging(config)

    log_message(log_path, "=" * 60)
    log_message(log_path, "AAAL 2026 EPISTEMIC STANCE ANALYSIS")
    log_message(log_path, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message(log_path, "=" * 60)
    log_message(log_path, "")

    # =========================================================================
    # Step 1: Load Parameters from Config
    # =========================================================================
    log_message(log_path, "STEP 1: LOADING PARAMETERS")
    log_message(log_path, "-" * 40)

    hedges = [h.lower() for h in config['epistemic']['hedges']]
    boosters = [b.lower() for b in config['epistemic']['boosters']]
    min_threshold = config['epistemic']['classification']['min_for_stance']

    log_message(log_path, f"  Hedges: {len(hedges)} terms")
    log_message(log_path, f"  Boosters: {len(boosters)} terms")
    log_message(log_path, f"  Min threshold: {min_threshold}")
    log_message(log_path, "")

    # =========================================================================
    # Step 2: Load Input Data (Multi-Sheet Excel from Script 02)
    # =========================================================================
    log_message(log_path, "STEP 2: LOADING INPUT DATA")
    log_message(log_path, "-" * 40)

    input_path = os.path.join(PROJECT_ROOT, config['paths']['analyzed_dir'], 'pmi_analyzed.xlsx')

    if not os.path.exists(input_path):
        log_message(log_path, f"ERROR: Input file missing: {input_path}")
        return 1

    xl = pd.ExcelFile(input_path)
    df = pd.concat([pd.read_excel(xl, sheet_name=sheet) for sheet in xl.sheet_names], ignore_index=True)

    log_message(log_path, f"  Loaded {len(df)} rows from {input_path}")
    log_message(log_path, "")

    # =========================================================================
    # Step 3: Epistemic Analysis
    # =========================================================================
    log_message(log_path, "STEP 3: EPISTEMIC ANALYSIS")
    log_message(log_path, "-" * 40)

    df['hedge_count'] = 0
    df['booster_count'] = 0
    df['epistemic_stance'] = 'Neutral'
    df['epistemic_density'] = 0.0

    tweets_with_hedges = 0
    tweets_with_boosters = 0
    tweets_with_markers = 0
    densities = []
    stance_counts = defaultdict(int)
    chapter_stats = []
    all_hedges = Counter()
    all_boosters = Counter()

    for chapter in sorted(df['chapter_code'].unique()):
        chapter_data = df[df['chapter_code'] == chapter]
        chapter_hedges = 0
        chapter_boosters = 0
        chapter_densities = []
        chapter_k_plus = 0
        chapter_k_minus = 0

        for idx, row in chapter_data.iterrows():
            text = str(row['tweet_text']) + ' ' + str(row.get('image_tweet_text', ''))
            word_count = len(re.findall(r'\b\w+\b', text))

            hedge_count = count_markers(text, hedges)
            booster_count = count_markers(text, boosters)

            if hedge_count > 0:
                tweets_with_hedges += 1
                all_hedges.update(re.findall(r'\b(' + '|'.join(hedges) + r')\b', text.lower()))
            if booster_count > 0:
                tweets_with_boosters += 1
                all_boosters.update(re.findall(r'\b(' + '|'.join(boosters) + r')\b', text.lower()))

            if hedge_count > 0 or booster_count > 0:
                tweets_with_markers += 1

            stance = classify_stance(hedge_count, booster_count, min_threshold)
            stance_counts[stance] += 1
            if stance == 'K+ (high certainty)':
                chapter_k_plus += 1
            elif stance == 'K- (low certainty)':
                chapter_k_minus += 1

            density = calculate_density(hedge_count, booster_count, word_count)
            densities.append(density)
            chapter_densities.append(density)

            df.at[idx, 'hedge_count'] = hedge_count
            df.at[idx, 'booster_count'] = booster_count
            df.at[idx, 'epistemic_stance'] = stance
            df.at[idx, 'epistemic_density'] = density

            chapter_hedges += hedge_count
            chapter_boosters += booster_count

        chapter_stats.append({
            'chapter': chapter,
            'rows': len(chapter_data),
            'k_plus': chapter_k_plus,
            'k_minus': chapter_k_minus,
            'density_mean': sum(chapter_densities) / len(chapter_densities) if chapter_densities else 0
        })

        log_message(log_path, f"  {chapter}: {len(chapter_data)} rows, hedges={chapter_hedges}, boosters={chapter_boosters}")

    mean_density = sum(densities) / len(densities) if densities else 0
    log_message(log_path, f"  Tweets with hedges: {tweets_with_hedges}")
    log_message(log_path, f"  Tweets with boosters: {tweets_with_boosters}")
    log_message(log_path, "")

    # =========================================================================
    # Step 4: Save Enriched Output (Multi-Sheet by Chapter)
    # =========================================================================
    log_message(log_path, "STEP 4: SAVING ENRICHED OUTPUT")
    log_message(log_path, "-" * 40)

    output_path = os.path.join(PROJECT_ROOT, config['paths']['analyzed_dir'], 'epistemic_analyzed.xlsx')
    chapter_list = config['chapters']

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for chapter_full in chapter_list:
            chapter_code = chapter_full.replace('CHD_', '').rstrip('_')
            chapter_data = df[df['chapter_code'] == chapter_code]
            chapter_data.to_excel(writer, sheet_name=chapter_full, index=False)

    log_message(log_path, f"  Saved: {output_path} ({len(df)} rows, {len(chapter_list)} sheets)")
    log_message(log_path, "")

    # =========================================================================
    # Step 5: Generate Epistemic Analysis Report
    # =========================================================================
    log_message(log_path, "STEP 5: GENERATING EPISTEMIC ANALYSIS REPORT")
    log_message(log_path, "-" * 40)

    report_path = os.path.join(PROJECT_ROOT, config['paths']['analyzed_dir'], 'epistemic_analysis_report.txt')
    hedge_freq = all_hedges.most_common()
    booster_freq = all_boosters.most_common()

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("AAAL 2026 EPISTEMIC STANCE ANALYSIS REPORT\n")
        f.write(f"Generated: {timestamp}\n")
        f.write("=" * 60 + "\n\n")

        f.write("THEORETICAL FRAMEWORK:\n")
        f.write("  Heritage, J. (2012). Epistemic engine: Sequence organization\n")
        f.write("  and territories of knowledge. Research on Language and Social\n")
        f.write("  Interaction, 45(1), 30-52.\n\n")
        f.write("  Hyland, K. (1998). Hedging in scientific research articles.\n")
        f.write("  John Benjamins Publishing.\n\n")
        f.write("  Hinkel, E. (2005). Hedging, inflating, and persuading in L2\n")
        f.write("  academic writing. Applied Language Learning, 15(1&2), 29-53.\n\n")

        f.write("PARAMETERS:\n")
        f.write(f"  Hedge markers: {len(hedges)} terms\n")
        f.write(f"  Booster markers: {len(boosters)} terms\n")
        f.write(f"  Min threshold for stance: {min_threshold}\n\n")

        f.write("CORPUS SUMMARY:\n")
        f.write(f"  Total rows analyzed: {len(df)}\n")
        f.write(f"  Tweets with hedges: {tweets_with_hedges} ({tweets_with_hedges/len(df)*100:.1f}%)\n")
        f.write(f"  Tweets with boosters: {tweets_with_boosters} ({tweets_with_boosters/len(df)*100:.1f}%)\n")
        f.write(f"  Tweets with any markers: {tweets_with_markers} ({tweets_with_markers/len(df)*100:.1f}%)\n")
        f.write(f"  Mean epistemic density: {mean_density:.3f} per 100 words\n\n")

        f.write("STANCE DISTRIBUTION:\n")
        for stance, count in sorted(stance_counts.items()):
            pct = count / len(df) * 100
            f.write(f"  {stance}: {count} ({pct:.1f}%)\n")

        f.write("\nCHAPTER BREAKDOWN:\n")
        f.write(f"  {'Chapter':<12} {'Rows':>8} {'K+':>6} {'K-':>6} {'Density':>10}\n")
        f.write(f"  {'-'*12} {'-'*8} {'-'*6} {'-'*6} {'-'*10}\n")
        for stat in chapter_stats:
            f.write(f"  {stat['chapter']:<12} {stat['rows']:>8} {stat['k_plus']:>6} "
                   f"{stat['k_minus']:>6} {stat['density_mean']:>10.3f}\n")

        f.write("\nTOP HEDGE MARKERS (Corpus-Wide):\n")
        if all_hedges:
            for marker, count in hedge_freq[:15]:
                f.write(f"  {marker}: {count}\n")

        f.write("\nTOP BOOSTER MARKERS (Corpus-Wide):\n")
        if all_boosters:
            for marker, count in booster_freq[:15]:
                f.write(f"  {marker}: {count}\n")

        f.write("\nOUTPUT FILES:\n")
        f.write(f"  {output_path}\n")
        f.write(f"    -> {len(df)} rows, {len(chapter_list)} sheets\n")

    log_message(log_path, f"  Report saved: {report_path}")
    log_message(log_path, "")

    # =========================================================================
    # Final Summary
    # =========================================================================
    log_message(log_path, "=" * 60)
    log_message(log_path, "SCRIPT 03 COMPLETE - EPISTEMIC STANCE ANALYSIS")
    log_message(log_path, "=" * 60)
    log_message(log_path, f"Total rows analyzed: {len(df)}")
    log_message(log_path, f"Tweets with epistemic markers: {tweets_with_markers} ({tweets_with_markers/len(df)*100:.1f}%)")
    log_message(log_path, f"Mean epistemic density: {mean_density:.3f} per 100 words")
    log_message(log_path, f"Stance distribution: K+={stance_counts.get('K+ (high certainty)', 0)}, "
               f"K-={stance_counts.get('K- (low certainty)', 0)}, "
               f"Mixed={stance_counts.get('Mixed', 0)}, "
               f"Neutral={stance_counts.get('Neutral', 0)}")
    log_message(log_path, f"Output: {output_path}")
    log_message(log_path, f"Log: {log_path}")
    log_message(log_path, f"Report: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
