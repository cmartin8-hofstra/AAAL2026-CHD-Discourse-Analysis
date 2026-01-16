#!/usr/bin/env python3
"""
Script 02: PMI Analysis (Church & Hanks, 1990)

Calculates pointwise mutual information for vaccine-related collocations
to identify lexical association patterns in CHD discourse.

Theoretical Framework:
    Church, K. W., & Hanks, P. (1990). Word association norms, mutual
    information, and lexicography. Computational Linguistics, 16(1), 22-29.

    Egbert, J., & Biber, D. (2019). Incorporating text dispersion into
    keyword analyses. Corpora, 14(2), 131-170.

PMI Formula:
    PMI(x,y) = log2(P(x,y) / (P(x) * P(y)))

    Interpretation: PMI measures how much more likely words co-occur than
    expected by chance. High PMI indicates strong lexical association.

Parameters (from config.yaml):
    - Window size: +/-3 words (captures local context)
    - Minimum frequency: 2 (filters noise)
    - Anchor terms: 27 vaccine-related terms (harmonized list)

Multiword Normalization:
    Applied BEFORE tokenization to capture compound vaccine terms as single
    tokens (e.g., "covid vaccine" -> "covidvaccine").

Stopword Exclusion:
    Hardcoded English stopwords (based on standard NLTK list) to filter function
    words, reducing sparse data bias in small corpora (Egbert & Biber, 2019).

Input Files (from Script 01):
    - outputs/tweet_reorganized_standardized.xlsx (15 sheets by chapter)
    - outputs/image_reorganized_standardized.xlsx (15 sheets by chapter)

Output Files:
    - data/analyzed/pmi_analyzed.xlsx (15 sheets by chapter, with PMI scores)
    - data/analyzed/pmi_corpus_statistics.csv (corpus-level word/cooccurrence stats)

Reproducibility Note (APA 7th):
    All paths and parameters are configurable via config.yaml. Code preserves
    original casing for downstream intensity analysis (e.g., VADER in Script 04).
    Stratification by chapter_code enables register variation analysis.

Author: AAAL 2026 Pipeline
Date: January 2026
"""
import os
import sys
import re
import math
from datetime import datetime
from collections import Counter, defaultdict
import pandas as pd
import yaml

# Hardcoded stopwords for exclusion (English, based on NLTK; Egbert & Biber, 2019)
# Filtering function words reduces sparse data bias in small corpora
STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers',
    'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if',
    'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
    'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't",
    'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn',
    "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't",
    'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't",
    'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
}

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
        # Validate required PMI parameters exist
        if not config.get('pmi', {}).get('anchor_terms'):
            raise ValueError("Anchor terms missing in config.yaml pmi section")
        return config
    except Exception as e:
        raise ValueError(f"Config loading error: {e}")


def setup_logging(config):
    """Setup log file with timestamp."""
    log_dir = os.path.join(PROJECT_ROOT, config['paths']['log_dir'])
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(log_dir, f'02_pmi_analysis_{timestamp}.log')
    return log_path, timestamp


def log_message(log_path, message, also_print=True):
    """Write message to log file and optionally print."""
    with open(log_path, 'a') as f:
        f.write(f"{datetime.now().strftime('%H:%M:%S')} | {message}\n")
    if also_print:
        print(message)


def normalize_multiwords(text, normalization_rules):
    """
    Normalize multiword expressions BEFORE tokenization.

    Replaces spaces with underscores in specified phrases to treat as single tokens.
    """
    for pattern, replacement in normalization_rules:
        text = re.sub(re.escape(' '.join(pattern)), replacement, text, flags=re.IGNORECASE)
    return text


def tokenize_text(text):
    """Tokenize text with basic regex (preserves casing for VADER)."""
    return re.findall(r'\w+|[^\w\s]', text.lower())


def calculate_pmi(word_counts, cooccurrence, total_words, anchor, word, min_freq):
    """
    Calculate PMI with frequency check.

    Returns 0 if below min_freq to filter noise (Egbert & Biber, 2019).
    """
    freq_anchor = word_counts.get(anchor, 0)
    freq_word = word_counts.get(word, 0)
    freq_cooccur = cooccurrence.get((anchor, word), 0)

    if freq_cooccur < min_freq or freq_anchor < min_freq or freq_word < min_freq:
        return 0

    p_xy = freq_cooccur / total_words if total_words > 0 else 0
    p_x = freq_anchor / total_words if total_words > 0 else 0
    p_y = freq_word / total_words if total_words > 0 else 0

    if p_x == 0 or p_y == 0 or p_xy == 0:
        return 0

    return math.log2(p_xy / (p_x * p_y))


def process_text(text, anchor_terms, window_size, min_freq, normalization_rules):
    """
    Process single text for PMI calculation.

    Returns dict of (anchor, word): pmi scores.
    """
    text = normalize_multiwords(text, normalization_rules)
    tokens = tokenize_text(text)

    word_counts = Counter(tokens)
    cooccurrence = defaultdict(int)
    pmi_scores = {}

    total_words = len(tokens)

    for i, token in enumerate(tokens):
        if token in anchor_terms:
            start = max(0, i - window_size)
            end = min(len(tokens), i + window_size + 1)
            window = tokens[start:end]
            for w in window:
                if w != token and w not in STOPWORDS:
                    cooccurrence[(token, w)] += 1

    for (anchor, word), count in cooccurrence.items():
        pmi = calculate_pmi(word_counts, cooccurrence, total_words, anchor, word, min_freq)
        if pmi > 0:
            pmi_scores[(anchor, word)] = pmi

    return pmi_scores


def main():
    """Main execution function."""
    print("=" * 60)
    print("SCRIPT 02: PMI ANALYSIS")
    print("=" * 60)
    print()

    config = load_config()
    log_path, timestamp = setup_logging(config)

    log_message(log_path, "=" * 60)
    log_message(log_path, "AAAL 2026 PMI ANALYSIS")
    log_message(log_path, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message(log_path, "=" * 60)
    log_message(log_path, "")

    # =========================================================================
    # Step 1: Load Parameters from Config
    # =========================================================================
    log_message(log_path, "STEP 1: LOADING PARAMETERS")
    log_message(log_path, "-" * 40)

    anchor_terms = set(term.lower() for term in config['pmi']['anchor_terms'])
    window_size = config['pmi']['window_size']
    min_freq = config['pmi']['min_frequency']
    normalization_rules = config.get('multiword_normalization', [])

    log_message(log_path, f"  Anchor terms: {len(anchor_terms)}")
    log_message(log_path, f"  Window size: +/-{window_size}")
    log_message(log_path, f"  Min frequency: {min_freq}")
    log_message(log_path, f"  Normalization rules: {len(normalization_rules)}")
    log_message(log_path, "")

    # =========================================================================
    # Step 2: Load Input Data (Multi-Sheet Excel from Script 01)
    # =========================================================================
    log_message(log_path, "STEP 2: LOADING INPUT DATA")
    log_message(log_path, "-" * 40)

    tweet_path = os.path.join(PROJECT_ROOT, 'outputs', 'tweet_reorganized_standardized.xlsx')
    image_path = os.path.join(PROJECT_ROOT, 'outputs', 'image_reorganized_standardized.xlsx')

    if not os.path.exists(tweet_path) or not os.path.exists(image_path):
        log_message(log_path, f"ERROR: Input files missing: {tweet_path} or {image_path}")
        return 1

    # Load tweet data (text focus for PMI)
    xl_tweet = pd.ExcelFile(tweet_path)
    df_tweet = pd.concat([pd.read_excel(xl_tweet, sheet_name=sheet) for sheet in xl_tweet.sheet_names], ignore_index=True)

    # Load image data (for multimodal enrichment)
    xl_image = pd.ExcelFile(image_path)
    df_image = pd.concat([pd.read_excel(xl_image, sheet_name=sheet) for sheet in xl_image.sheet_names], ignore_index=True)

    # Merge on data_snap_source for full multimodal corpus
    df = pd.merge(df_tweet, df_image, on=['data_snap_source', 'tweet_date', 'user_name'], how='inner')
    df['chapter_code'] = df['data_snap_source'].apply(lambda x: str(x).split('_')[0])

    log_message(log_path, f"  Loaded tweets: {len(df_tweet)} rows")
    log_message(log_path, f"  Loaded images: {len(df_image)} rows")
    log_message(log_path, f"  Merged multimodal: {len(df)} rows")
    log_message(log_path, "")

    # =========================================================================
    # Step 3: PMI Calculation (Stratified by Chapter)
    # =========================================================================
    log_message(log_path, "STEP 3: PMI CALCULATION (STRATIFIED)")
    log_message(log_path, "-" * 40)

    all_pmi_scores = {}  # {chapter: {ds_source: {(anchor, word): pmi}}}
    total_words_dict = {}
    word_counts_dict = {}
    cooccurrence_dict = {}
    tweets_with_pmi = 0
    pmi_sums = []

    for chapter in sorted(df['chapter_code'].unique()):
        chapter_data = df[df['chapter_code'] == chapter]
        chapter_pmi = {}  # {ds_source: {(anchor, word): pmi}}
        chapter_total_words = 0
        chapter_word_counts = Counter()
        chapter_cooccurrence = defaultdict(int)

        for _, row in chapter_data.iterrows():
            text = str(row['tweet_text']) + ' ' + str(row.get('image_tweet_text', ''))
            pmi_scores = process_text(text, anchor_terms, window_size, min_freq, normalization_rules)

            if pmi_scores:
                tweets_with_pmi += 1
                sum_pmi = sum(pmi_scores.values())
                pmi_sums.append(sum_pmi)
                chapter_pmi[row['data_snap_source']] = pmi_scores

            # Update chapter stats
            tokens = tokenize_text(text)
            chapter_total_words += len(tokens)
            chapter_word_counts.update(tokens)
            # Update cooccurrence (full for stats)
            for i, token in enumerate(tokens):
                if token in anchor_terms:
                    start = max(0, i - window_size)
                    end = min(len(tokens), i + window_size + 1)
                    window = tokens[start:end]
                    for w in window:
                        if w != token and w not in STOPWORDS:
                            chapter_cooccurrence[(token, w)] += 1

        all_pmi_scores[chapter] = chapter_pmi
        total_words_dict[chapter] = chapter_total_words
        word_counts_dict[chapter] = chapter_word_counts
        cooccurrence_dict[chapter] = chapter_cooccurrence

        log_message(log_path, f"  {chapter}: {len(chapter_data)} rows, PMI pairs: {sum(len(scores) for scores in chapter_pmi.values())}")

    pmi_mean = sum(pmi_sums) / len(pmi_sums) if pmi_sums else 0
    pmi_max = max(pmi_sums) if pmi_sums else 0
    log_message(log_path, f"  Total tweets with PMI: {tweets_with_pmi}")
    log_message(log_path, "")

    # =========================================================================
    # Step 4: Enrich DataFrame with PMI
    # =========================================================================
    log_message(log_path, "STEP 4: ENRICHING DATAFRAME WITH PMI")
    log_message(log_path, "-" * 40)

    df['pmi_scores'] = ''
    df['pmi_sum'] = 0.0

    for chapter, chapter_pmi in all_pmi_scores.items():
        for ds_source, scores in chapter_pmi.items():
            mask = (df['chapter_code'] == chapter) & (df['data_snap_source'] == ds_source)
            if mask.any():
                df.loc[mask, 'pmi_scores'] = str(scores)
                df.loc[mask, 'pmi_sum'] = sum(scores.values())

    log_message(log_path, f"  Enriched rows: {(df['pmi_sum'] > 0).sum()}")
    log_message(log_path, "")

    # =========================================================================
    # Step 5: Save Enriched Output (Multi-Sheet by Chapter)
    # =========================================================================
    log_message(log_path, "STEP 5: SAVING ENRICHED OUTPUT")
    log_message(log_path, "-" * 40)

    analyzed_dir = os.path.join(PROJECT_ROOT, config['paths']['analyzed_dir'])
    os.makedirs(analyzed_dir, exist_ok=True)
    output_path = os.path.join(analyzed_dir, 'pmi_analyzed.xlsx')

    chapter_list = config['chapters']
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for chapter_full in chapter_list:
            chapter_code = chapter_full.replace('CHD_', '').rstrip('_')
            chapter_data = df[df['chapter_code'] == chapter_code]
            chapter_data.to_excel(writer, sheet_name=chapter_full, index=False)

    total_rows = len(df)
    log_message(log_path, f"  Saved: {output_path} ({total_rows} rows, {len(chapter_list)} sheets)")
    log_message(log_path, "")

    # =========================================================================
    # Step 6: Save Corpus Statistics
    # =========================================================================
    log_message(log_path, "STEP 6: SAVING CORPUS STATISTICS")
    log_message(log_path, "-" * 40)

    stats_path = os.path.join(analyzed_dir, 'pmi_corpus_statistics.csv')
    stats_data = []
    for chapter in sorted(total_words_dict.keys()):
        stats_data.append({
            'chapter': chapter,
            'total_words': total_words_dict[chapter],
            'vocabulary_size': len(word_counts_dict[chapter]),
            'cooccurrence_pairs': len(cooccurrence_dict[chapter]),
            'pmi_pairs_calculated': sum(len(scores) for scores in all_pmi_scores.get(chapter, {}).values())
        })
    stats_df = pd.DataFrame(stats_data)
    stats_df.to_csv(stats_path, index=False)
    log_message(log_path, f"  Corpus statistics saved: {stats_path}")
    log_message(log_path, "")

    # =========================================================================
    # Step 7: Generate PMI Analysis Report
    # =========================================================================
    log_message(log_path, "STEP 7: GENERATING PMI ANALYSIS REPORT")
    log_message(log_path, "-" * 40)

    report_path = os.path.join(analyzed_dir, 'pmi_analysis_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("AAAL 2026 PMI ANALYSIS REPORT\n")
        f.write(f"Generated: {timestamp}\n")
        f.write("=" * 60 + "\n\n")

        f.write("THEORETICAL FRAMEWORK:\n")
        f.write("  Church, K. W., & Hanks, P. (1990). Word association norms,\n")
        f.write("  mutual information, and lexicography. Computational Linguistics.\n\n")

        f.write("PARAMETERS:\n")
        f.write(f"  Anchor terms: {len(anchor_terms)}\n")
        f.write(f"  Window size: +/-{window_size} words\n")
        f.write(f"  Min frequency: {min_freq}\n")
        f.write(f"  Stopwords excluded: {len(STOPWORDS)}\n\n")

        f.write("CORPUS SUMMARY:\n")
        f.write(f"  Total rows analyzed: {len(df)}\n")
        f.write(f"  Tweets with PMI content: {tweets_with_pmi} ({tweets_with_pmi/len(df)*100:.1f}%)\n")
        f.write(f"  Mean PMI sum: {pmi_mean:.3f}\n")
        f.write(f"  Max PMI sum: {pmi_max:.3f}\n\n")

        f.write("CHAPTER BREAKDOWN:\n")
        f.write(f"  {'Chapter':<12} {'Rows':>8} {'Mean PMI':>10} {'PMI>0':>8}\n")
        f.write(f"  {'-'*12} {'-'*8} {'-'*10} {'-'*8}\n")
        for chapter_full in sorted(chapter_list):
            chapter_code = chapter_full.replace('CHD_', '').rstrip('_')
            chapter_data = df[df['chapter_code'] == chapter_code]
            if len(chapter_data) > 0:
                c_mean = chapter_data['pmi_sum'].mean()
                c_positive = (chapter_data['pmi_sum'] > 0).sum()
                f.write(f"  {chapter_full:<12} {len(chapter_data):>8} {c_mean:>10.3f} {c_positive:>8}\n")

        f.write("\nTOP PMI COLLOCATIONS (Corpus-Wide):\n")
        # Aggregate all PMI scores and find top pairs
        all_pairs = []
        for chapter, chapter_pmi in all_pmi_scores.items():
            for ds_source, pmi_dict in chapter_pmi.items():
                for (anchor, word), pmi in pmi_dict.items():
                    all_pairs.append((anchor, word, chapter, pmi))
        top_overall = sorted(all_pairs, key=lambda x: x[3], reverse=True)[:20]
        f.write(f"  {'Anchor':<15} {'Collocate':<15} {'Chapter':<10} {'PMI':>8}\n")
        f.write(f"  {'-'*15} {'-'*15} {'-'*10} {'-'*8}\n")
        for anchor, word, chapter, pmi in top_overall:
            f.write(f"  {anchor:<15} {word:<15} {chapter:<10} {pmi:>8.3f}\n")

        f.write("\nOUTPUT FILES:\n")
        f.write(f"  {output_path}\n")
        f.write(f"    -> {len(df)} rows, {len(chapter_list)} sheets\n")
        f.write(f"  {stats_path}\n")
        f.write(f"    -> Corpus statistics for reproducibility\n")

    log_message(log_path, f"  Report saved: {report_path}")
    log_message(log_path, "")

    # =========================================================================
    # Final Summary
    # =========================================================================
    log_message(log_path, "=" * 60)
    log_message(log_path, "SCRIPT 02 COMPLETE - PMI ANALYSIS")
    log_message(log_path, "=" * 60)
    log_message(log_path, f"Total rows analyzed: {len(df)}")
    log_message(log_path, f"Tweets with PMI content: {tweets_with_pmi} ({tweets_with_pmi/len(df)*100:.1f}%)")
    log_message(log_path, f"Mean PMI sum: {pmi_mean:.3f}")
    log_message(log_path, f"Output: {output_path}")
    log_message(log_path, f"Log: {log_path}")
    log_message(log_path, f"Report: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
