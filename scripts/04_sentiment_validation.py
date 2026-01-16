#!/usr/bin/env python3
"""
Script 04: Sentiment Analysis & Corpus Validation (Hutto & Gilbert, 2014)

Analyzes sentiment intensity using VADER and validates internal consistency
of discourse features through statistical testing.

Theoretical Framework:
    - Hutto, C., & Gilbert, E. (2014). VADER: A parsimonious rule-based model
      for sentiment analysis of social media text. Proceedings of the International
      AAAI Conference on Web and Social Media.

      VADER is specifically designed and validated for social media text,
      incorporating:
      - Sentiment lexicon with intensity ratings
      - Emoticon/emoji sentiment mappings
      - Capitalization intensity amplification (GREAT vs great)
      - Punctuation intensity amplification (!!! vs !)
      - Negation handling
      - Contrast conjunctions (but, however)

    - Biber, D., Conrad, S., & Reppen, R. (1999). Corpus linguistics:
      Investigating language structure and use. Cambridge University Press.

      Validation procedures follow corpus linguistics standards for
      internal consistency and reliability checking.

Statistical Tests:
    1. Pearson correlation (r): Assesses linear relationship between continuous
       variables (e.g., PMI sum vs epistemic density)
    2. One-way ANOVA (F-test): Compares means across multiple groups
       (e.g., sentiment across chapters for register variation)
    3. Eta-squared (n2): Effect size for ANOVA, proportion of variance explained

APA 7th Edition Reporting:
    All statistical results formatted following APA guidelines with:
    - Test statistic, degrees of freedom, p-value, effect size
    - Interpretation of practical significance
    - Ready-to-use Methods section prose

Input Files (from Script 03):
    - data/analyzed/epistemic_analyzed.xlsx (15 sheets by chapter, enriched multimodal data)

Output Files:
    - data/analyzed/validated_corpus.xlsx (final enriched dataset, 15 sheets)
    - data/analyzed/validated_corpus.csv (flat file for external analysis)
    - data/analyzed/validation_report.txt (APA-ready stats and interpretations)

Reproducibility Note (APA 7th):
    VADER applied to preserved-cased text for intensity fidelity (Hutto & Gilbert, 2014).
    Stats computed with scipy.stats; chapter stratification ensures register variation
    analysis (Egbert & Biber, 2019).

Author: AAAL 2026 Pipeline
Date: January 2026
"""
import os
import sys
from datetime import datetime
import pandas as pd
import numpy as np
import yaml
from scipy import stats
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

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
    log_path = os.path.join(log_dir, f'04_sentiment_validation_{timestamp}.log')
    return log_path, timestamp


def log_message(log_path, message, also_print=True):
    """Write message to log file and optionally print (for reproducibility)."""
    with open(log_path, 'a') as f:
        f.write(f"{datetime.now().strftime('%H:%M:%S')} | {message}\n")
    if also_print:
        print(message)


def perform_statistical_tests(df, log_path):
    """
    Perform validation statistical tests (APA 7th formatted).

    Returns dict of results for reporting.
    """
    results = {}
    chapter_groups = df.groupby('chapter_code')

    # Pearson correlations
    r_pmi_epist, p_pmi_epist = stats.pearsonr(df['pmi_sum'], df['epistemic_density'])
    r_pmi_sent, p_pmi_sent = stats.pearsonr(df['pmi_sum'], df['sentiment_compound'])
    r_epist_sent, p_epist_sent = stats.pearsonr(df['epistemic_density'], df['sentiment_compound'])

    results['correlations'] = {
        'pmi_epist': (r_pmi_epist, p_pmi_epist),
        'pmi_sent': (r_pmi_sent, p_pmi_sent),
        'epist_sent': (r_epist_sent, p_epist_sent)
    }

    # One-way ANOVA for group differences (if >=3 groups)
    if len(chapter_groups) >= 3:
        # PMI across chapters
        pmi_groups = [group['pmi_sum'].values for name, group in chapter_groups if len(group) > 1]
        if len(pmi_groups) >= 3:
            f_pmi, p_pmi = stats.f_oneway(*pmi_groups)
            total_n = len(df)
            k = len(pmi_groups)
            eta2_pmi = f_pmi * (k - 1) / (f_pmi * (k - 1) + (total_n - k))
            results['pmi_anova'] = (f_pmi, p_pmi, k-1, total_n-k)
            results['pmi_eta_squared'] = eta2_pmi

        # Sentiment across chapters
        sent_groups = [group['sentiment_compound'].values for name, group in chapter_groups if len(group) > 1]
        if len(sent_groups) >= 3:
            f_sent, p_sent = stats.f_oneway(*sent_groups)
            eta2_sent = f_sent * (k - 1) / (f_sent * (k - 1) + (total_n - k))
            results['sentiment_anova'] = (f_sent, p_sent, k-1, total_n-k)
            results['sentiment_eta_squared'] = eta2_sent

    log_message(log_path, f"  Correlations computed: 3 pairs")
    log_message(log_path, f"  ANOVAs computed: {len(results) // 2 - 1}")
    log_message(log_path, "")

    return results


def main():
    """Main execution function."""
    print("=" * 60)
    print("SCRIPT 04: SENTIMENT ANALYSIS & VALIDATION")
    print("=" * 60)
    print()

    config = load_config()
    log_path, timestamp = setup_logging(config)

    log_message(log_path, "=" * 60)
    log_message(log_path, "AAAL 2026 SENTIMENT & VALIDATION")
    log_message(log_path, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message(log_path, "=" * 60)
    log_message(log_path, "")

    # =========================================================================
    # Step 1: Load Input Data (Multi-Sheet Excel from Script 03)
    # =========================================================================
    log_message(log_path, "STEP 1: LOADING INPUT DATA")
    log_message(log_path, "-" * 40)

    input_path = os.path.join(PROJECT_ROOT, config['paths']['analyzed_dir'], 'epistemic_analyzed.xlsx')

    if not os.path.exists(input_path):
        log_message(log_path, f"ERROR: Input file missing: {input_path}")
        return 1

    xl = pd.ExcelFile(input_path)
    df = pd.concat([pd.read_excel(xl, sheet_name=sheet) for sheet in xl.sheet_names], ignore_index=True)

    log_message(log_path, f"  Loaded {len(df)} rows from {input_path}")
    log_message(log_path, "")

    # =========================================================================
    # Step 2: Sentiment Analysis with VADER
    # =========================================================================
    log_message(log_path, "STEP 2: SENTIMENT ANALYSIS (VADER)")
    log_message(log_path, "-" * 40)

    analyzer = SentimentIntensityAnalyzer()
    df['sentiment_compound'] = 0.0
    df['sentiment_pos'] = 0.0
    df['sentiment_neg'] = 0.0
    df['sentiment_neu'] = 0.0

    positive_count = 0
    negative_count = 0
    neutral_count = 0
    compounds = []

    for idx, row in df.iterrows():
        text = str(row['tweet_text']) + ' ' + str(row.get('image_tweet_text', ''))
        scores = analyzer.polarity_scores(text)
        
        df.at[idx, 'sentiment_compound'] = scores['compound']
        df.at[idx, 'sentiment_pos'] = scores['pos']
        df.at[idx, 'sentiment_neg'] = scores['neg']
        df.at[idx, 'sentiment_neu'] = scores['neu']

        compounds.append(scores['compound'])

        if scores['compound'] > 0.05:
            positive_count += 1
        elif scores['compound'] < -0.05:
            negative_count += 1
        else:
            neutral_count += 1

    mean_compound = np.mean(compounds)
    std_compound = np.std(compounds)
    positive_pct = positive_count / len(df) * 100
    negative_pct = negative_count / len(df) * 100
    neutral_pct = neutral_count / len(df) * 100

    log_message(log_path, f"  Analyzed {len(df)} texts")
    log_message(log_path, f"  Mean compound: {mean_compound:.3f} (SD={std_compound:.3f})")
    log_message(log_path, f"  Distribution: +{positive_pct:.1f}% / -{negative_pct:.1f}% / ~{neutral_pct:.1f}%")
    log_message(log_path, "")

    # =========================================================================
    # Step 3: Statistical Validation
    # =========================================================================
    log_message(log_path, "STEP 3: STATISTICAL VALIDATION")
    log_message(log_path, "-" * 40)

    stats_results = perform_statistical_tests(df, log_path)

    # Chapter-level stats for report
    chapter_stats = []
    chapter_groups = df.groupby('chapter_code')
    for name, group in chapter_groups:
        chapter_stats.append({
            'chapter': name,
            'n': len(group),
            'pmi_mean': group['pmi_sum'].mean(),
            'epistemic_mean': group['epistemic_density'].mean(),
            'sentiment_mean': group['sentiment_compound'].mean(),
            'positive_pct': (group['sentiment_compound'] > 0.05).mean() * 100,
            'negative_pct': (group['sentiment_compound'] < -0.05).mean() * 100
        })

    log_message(log_path, f"  Chapter stats computed: {len(chapter_stats)} groups")
    log_message(log_path, "")

    # =========================================================================
    # Step 4: Save Validated Corpus
    # =========================================================================
    log_message(log_path, "STEP 4: SAVING VALIDATED CORPUS")
    log_message(log_path, "-" * 40)

    analyzed_dir = os.path.join(PROJECT_ROOT, config['paths']['analyzed_dir'])
    excel_path = os.path.join(analyzed_dir, 'validated_corpus.xlsx')
    csv_path = os.path.join(analyzed_dir, 'validated_corpus.csv')

    chapter_list = config['chapters']
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for chapter_full in chapter_list:
            chapter_code = chapter_full.replace('CHD_', '').rstrip('_')
            chapter_data = df[df['chapter_code'] == chapter_code]
            chapter_data.to_excel(writer, sheet_name=chapter_full, index=False)

    df.to_csv(csv_path, index=False)

    total_rows = len(df)
    log_message(log_path, f"  Excel saved: {excel_path} ({total_rows} rows, {len(chapter_list)} sheets)")
    log_message(log_path, f"  CSV saved: {csv_path} ({total_rows} rows)")
    log_message(log_path, "")

    # =========================================================================
    # Step 5: Generate Validation Report (APA 7th Ready)
    # =========================================================================
    log_message(log_path, "STEP 5: GENERATING VALIDATION REPORT")
    log_message(log_path, "-" * 40)

    report_path = os.path.join(analyzed_dir, 'validation_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("AAAL 2026 CORPUS VALIDATION REPORT\n")
        f.write(f"Generated: {timestamp}\n")
        f.write("=" * 60 + "\n\n")

        f.write("THEORETICAL FRAMEWORK:\n")
        f.write("  Hutto, C., & Gilbert, E. (2014). VADER: A parsimonious rule-based model\n")
        f.write("  for sentiment analysis of social media text. ICWSM.\n\n")
        f.write("  Biber, D., et al. (1999). Corpus linguistics: Investigating language\n")
        f.write("  structure and use. Cambridge University Press.\n\n")

        f.write("SENTIMENT SUMMARY:\n")
        f.write(f"  Mean compound: {mean_compound:.3f} (SD = {std_compound:.3f})\n")
        f.write(f"  Positive (>0.05): {positive_count} ({positive_pct:.1f}%)\n")
        f.write(f"  Negative (<-0.05): {negative_count} ({negative_pct:.1f}%)\n")
        f.write(f"  Neutral: {neutral_count} ({neutral_pct:.1f}%)\n\n")

        f.write("STATISTICAL VALIDATION (APA 7th Format):\n")
        f.write("  Pearson Correlations:\n")
        for key, (r, p) in stats_results.get('correlations', {}).items():
            sig = "p < .001" if p < 0.001 else f"p = {p:.3f}"
            f.write(f"    PMI sum and epistemic density were {'not ' if p >= 0.05 else ''}significantly correlated,\n")
            f.write(f"      r = {r:.2f}, {sig}.\n")
            f.write(f"    PMI sum and sentiment compound were {'not ' if p >= 0.05 else ''}significantly correlated,\n")
            f.write(f"      r = {r:.2f}, {sig}.\n")
            f.write(f"    Epistemic density and sentiment compound were {'not ' if p >= 0.05 else ''}significantly correlated,\n")
            f.write(f"      r = {r:.2f}, {sig}.\n\n")

        f.write("  One-Way ANOVA (Chapter Variation):\n")
        if 'pmi_anova' in stats_results:
            f_stat, p_val, df1, df2 = stats_results['pmi_anova']
            eta2 = stats_results['pmi_eta_squared']
            sig = "p < .001" if p_val < 0.001 else f"p = {p_val:.3f}"
            f.write(f"    A one-way ANOVA revealed {'no ' if p_val >= 0.05 else ''}significant differences in PMI sum\n")
            f.write(f"    across chapters, F({df1}, {df2}) = {f_stat:.2f}, {sig}, η² = {eta2:.2f}.\n\n")

        if 'sentiment_anova' in stats_results:
            f_stat, p_val, df1, df2 = stats_results['sentiment_anova']
            eta2 = stats_results['sentiment_eta_squared']
            sig = "p < .001" if p_val < 0.001 else f"p = {p_val:.3f}"
            f.write(f"    A one-way ANOVA revealed {'no ' if p_val >= 0.05 else ''}significant differences in sentiment\n")
            f.write(f"    across chapters, F({df1}, {df2}) = {f_stat:.2f}, {sig}, η² = {eta2:.2f}.\n\n")

        f.write("CHAPTER BREAKDOWN:\n")
        f.write(f"  {'Chapter':<12} {'N':>6} {'PMI':>8} {'Epist':>8} {'Sent':>8} {'Pos%':>6} {'Neg%':>6}\n")
        f.write(f"  {'-'*12} {'-'*6} {'-'*8} {'-'*8} {'-'*8} {'-'*6} {'-'*6}\n")
        for stat in sorted(chapter_stats, key=lambda x: x['chapter']):
            f.write(f"  {stat['chapter']:<12} {stat['n']:>6} {stat['pmi_mean']:>8.2f} "
                   f"{stat['epistemic_mean']:>8.2f} {stat['sentiment_mean']:>8.2f} "
                   f"{stat['positive_pct']:>6.1f} {stat['negative_pct']:>6.1f}\n")

        f.write("\nOUTPUT FILES:\n")
        f.write(f"  {excel_path}\n")
        f.write(f"    -> {total_rows} rows, {len(chapter_list)} sheets\n")
        f.write(f"  {csv_path}\n")
        f.write(f"    -> Flat file for external analysis\n")

    log_message(log_path, f"  Report saved: {report_path}")
    log_message(log_path, "")

    # =========================================================================
    # Final Summary
    # =========================================================================
    log_message(log_path, "=" * 60)
    log_message(log_path, "SCRIPT 04 COMPLETE - SENTIMENT & VALIDATION")
    log_message(log_path, "=" * 60)
    log_message(log_path, f"Total rows validated: {len(df)}")
    log_message(log_path, f"Mean sentiment: {mean_compound:.3f} (SD={std_compound:.3f})")
    log_message(log_path, f"Sentiment distribution: +{positive_pct:.1f}% / -{negative_pct:.1f}% / ~{neutral_pct:.1f}%")
    log_message(log_path, f"Output Excel: {excel_path}")
    log_message(log_path, f"Output CSV: {csv_path}")
    log_message(log_path, f"Log: {log_path}")
    log_message(log_path, f"Report: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
