#!/usr/bin/env python3
"""
Script 01: Data Standardization with Intelligent Filling & Preservation
Processes Claude Vision output into clean, modular datasets for AAAL 2026 pipeline.

Key Features:
    - OCR re-analysis for missing image_tweet_text / image_description
    - Intelligent filling of word_count, hashtags
    - Within-chapter duplicate detection with Shared With mapping
    - Duplicate REMOVAL from main datasets (Biber et al., 1999 corpus standards)
    - Text-only tweet extraction
    - PNG copying with renaming to match data_snap_source identifiers
    - Multi-sheet Excel output organized by chapter (15 CHD state chapters)

Output Files:
    - tweet_reorganized_standardized.xlsx (15 sheets by chapter, duplicates removed)
    - image_reorganized_standardized.xlsx (15 sheets by chapter, duplicates removed)
    - text_only_tweets.xlsx (single sheet)
    - within_chapter_duplicates.xlsx (sheets by chapter, preserved for traceability)
    - multimodal_data_snaps/{chapter}/*.png (renamed PNGs matching data_snap_source)
    - preparation_report.txt

Theoretical Framework:
    - Digital discourse analysis (Androutsopoulos, 2014)
    - Corpus linguistics standards (Biber et al., 1999)
    - Forensic discourse analysis for epistemic stancetaking (Heritage, 2012)

Author: AAAL 2026 Pipeline
Date: January 2026
"""
import os
import sys
import re
import shutil
from datetime import datetime
import pandas as pd
import yaml
from PIL import Image
import pytesseract

# Set Tesseract path (macOS Homebrew ARM)
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)


def load_config():
    """Load configuration from config.yaml."""
    config_path = os.path.join(PROJECT_ROOT, 'config', 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def setup_logging(config):
    """Setup log file with timestamp."""
    log_dir = os.path.join(PROJECT_ROOT, config['paths']['log_dir'])
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(log_dir, f'01_data_standardization_{timestamp}.log')
    return log_path, timestamp


def log_message(log_path, message, also_print=True):
    """Write message to log file and optionally print."""
    with open(log_path, 'a') as f:
        f.write(f"{datetime.now().strftime('%H:%M:%S')} | {message}\n")
    if also_print:
        print(message)


def extract_data_snap_source(image_filename, subfolder):
    """
    Extract standardized data_snap_source identifier from image_filename.

    Examples:
        CHD_AZ_ + 01.png -> AZ_01
        CHD_MAIN_ + 123.png -> MAIN_123
    """
    if pd.isna(image_filename):
        return None

    match = re.search(r'(\d+)\.png$', str(image_filename), re.IGNORECASE)
    if not match:
        return None

    num = int(match.group(1))

    if pd.isna(subfolder):
        return None

    prefix = str(subfolder).replace('CHD_', '').rstrip('_')
    return f"{prefix}_{num:02d}" if num < 100 else f"{prefix}_{num}"


def extract_chapter_code(subfolder):
    """
    Extract chapter code from subfolder.

    Examples:
        CHD_AZ_ -> AZ
        CHD_MAIN_ -> MAIN
    """
    if pd.isna(subfolder):
        return None
    return str(subfolder).replace('CHD_', '').rstrip('_')


def intelligent_fill(df, png_base_dir, log_path):
    """
    Intelligent filling of missing data with OCR re-analysis.

    Steps:
        1. Recompute word_count from tweet_text
        2. Extract hashtags from tweet_text if missing
        3. OCR re-analysis for missing image_tweet_text / image_description
    """
    filled_stats = {'word_count': 0, 'hashtags': 0, 'ocr_text': 0, 'ocr_desc': 0}

    # 1. Recompute word_count (robust regex)
    df['word_count'] = df['tweet_text'].apply(
        lambda x: len(re.findall(r'\b\w+\b', str(x))) if pd.notna(x) else 0
    )
    filled_stats['word_count'] = len(df)
    log_message(log_path, f"  Recomputed word_count for {filled_stats['word_count']} rows")

    # 2. Extract hashtags if missing
    missing_hashtags = df[df['hashtags'].fillna('') == '']
    for idx, row in missing_hashtags.iterrows():
        extracted = re.findall(r'#(\w+)', str(row['tweet_text']))
        if extracted:
            df.at[idx, 'hashtags'] = ','.join(extracted)
            filled_stats['hashtags'] += 1
    log_message(log_path, f"  Extracted hashtags for {filled_stats['hashtags']} rows")

    # 3. OCR re-analysis for missing image_tweet_text / image_description
    missing_ocr = df[
        ((df['image_tweet_text'].fillna('') == '') | (df['image_description'].fillna('') == '')) &
        (df['image_present'] == True)
    ]
    log_message(log_path, f"  Found {len(missing_ocr)} rows needing OCR re-analysis")

    for idx, row in missing_ocr.iterrows():
        full_path = os.path.join(png_base_dir, str(row['subfolder']), str(row['image_filename']))
        if os.path.exists(full_path):
            try:
                img = Image.open(full_path)
                ocr_raw = pytesseract.image_to_string(img, config='--psm 6')
                cleaned = re.sub(r'\n+', ' ', ocr_raw.strip())

                # Check if OCR contains indicators of tweet content
                if re.search(r'@|views|LIVE:|https?', cleaned):
                    if df.at[idx, 'image_tweet_text'] == '' or pd.isna(df.at[idx, 'image_tweet_text']):
                        df.at[idx, 'image_tweet_text'] = cleaned
                        filled_stats['ocr_text'] += 1
                    if df.at[idx, 'image_description'] == '' or pd.isna(df.at[idx, 'image_description']):
                        df.at[idx, 'image_description'] = f"OCR-derived screenshot: {cleaned[:100]}..."
                        filled_stats['ocr_desc'] += 1
            except Exception as e:
                log_message(log_path, f"  OCR failed for {row['image_filename']}: {e}")

    log_message(log_path, f"  OCR filled: {filled_stats['ocr_text']} image_tweet_text, {filled_stats['ocr_desc']} image_description")

    return df, filled_stats


def verify_capture_accuracy(df, log_path):
    """Verify data capture accuracy and log statistics."""
    mismatches = (df['word_count'] != df['tweet_text'].apply(lambda x: len(str(x).split()))).sum()
    empty_tweet = (df['tweet_text'].fillna('') == '').sum()
    inconsistent_ocr = ((df['image_present'] == True) & (df['image_tweet_text'].fillna('') == '')).sum()

    log_message(log_path, f"  Word count mismatches (split vs regex): {mismatches}")
    log_message(log_path, f"  Empty tweet_text: {empty_tweet}")
    log_message(log_path, f"  Inconsistent OCR (image_present but no image_tweet_text): {inconsistent_ocr}")

    return {'mismatches': mismatches, 'empty_tweet': empty_tweet, 'inconsistent_ocr': inconsistent_ocr}


def detect_duplicates_with_shared(df, log_path, min_word_count=3):
    """
    Detect within-chapter duplicates and populate Shared With column.

    ENHANCED (Biber et al., 1999): Strengthened duplicate detection to prevent leakage.
    For each duplicate, lists all other data_snap_source IDs that share the same tweet_text.
    Only flags duplicates where word_count > min_word_count to avoid short hashtags/phrases.

    Returns:
        df: DataFrame with 'Shared With' column populated
        dup_ids: Set of data_snap_source IDs that are duplicates (for removal)
    """
    log_message(log_path, "  Detecting within-chapter duplicates (word_count > 3 threshold)...")

    # Add Shared With column - ensure clean state
    df['Shared With'] = ''

    # Track all duplicate IDs for later removal
    all_dup_ids = set()

    # Group by chapter_code and find duplicates within each chapter
    for chapter in df['chapter_code'].unique():
        if pd.isna(chapter):
            continue

        chapter_mask = df['chapter_code'] == chapter
        chapter_df = df[chapter_mask]

        # Find duplicate tweet_texts within this chapter (only consider rows with word_count > threshold)
        # FIX: Also normalize tweet_text for comparison (strip whitespace)
        substantive_df = chapter_df[chapter_df['word_count'] > min_word_count].copy()
        substantive_df['_normalized_text'] = substantive_df['tweet_text'].apply(
            lambda x: str(x).strip().lower() if pd.notna(x) else ''
        )

        dup_mask = substantive_df.duplicated(subset=['_normalized_text'], keep=False)
        dup_texts = substantive_df.loc[dup_mask, '_normalized_text'].unique()

        for dup_text in dup_texts:
            if pd.isna(dup_text) or dup_text == '':
                continue

            # Get all rows with this normalized tweet_text in this chapter
            # FIX: Use normalized comparison to catch case/whitespace variants
            matching_indices = substantive_df[substantive_df['_normalized_text'] == dup_text].index.tolist()
            matching_ids = df.loc[matching_indices, 'data_snap_source'].tolist()

            # Add all matching IDs to the set of duplicates
            all_dup_ids.update(matching_ids)

            # For each row, set Shared With to all OTHER matching IDs
            for idx in matching_indices:
                current_id = df.at[idx, 'data_snap_source']
                other_ids = [id for id in matching_ids if id != current_id]
                df.at[idx, 'Shared With'] = ', '.join(other_ids)

    # Count duplicates - explicit verification
    dup_count = (df['Shared With'] != '').sum()
    log_message(log_path, f"  Found {dup_count} rows with duplicates (word_count > {min_word_count})")
    log_message(log_path, f"  Unique duplicate IDs tracked: {len(all_dup_ids)}")

    return df, all_dup_ids


def copy_pngs(df, src_base, dest_base, log_path, organize_by_chapter=True):
    """Copy PNGs to destination directory, optionally organized by chapter."""
    os.makedirs(dest_base, exist_ok=True)
    copied = 0

    for _, row in df.iterrows():
        src = os.path.join(src_base, str(row['subfolder']), str(row['image_filename']))
        if os.path.exists(src):
            if organize_by_chapter:
                dest_dir = os.path.join(dest_base, row['chapter_code'])
            else:
                dest_dir = dest_base
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, str(row['image_filename']))
            shutil.copy(src, dest)
            copied += 1

    log_message(log_path, f"  Copied {copied} PNGs to {dest_base}")
    return copied


def copy_and_rename_multimodal_pngs(df, src_base, dest_base, log_path):
    """
    Copy PNGs for multimodal rows, renaming to match data_snap_source.

    Creates folder structure: multimodal_data_snaps/{chapter_code}/
    Renames files: C_FL1.png -> FL_01.png (matching data_snap_source)

    Args:
        df: DataFrame with multimodal rows (must have subfolder, image_filename,
            data_snap_source, chapter_code columns)
        src_base: Source PNG directory (data/raw/data_snaps)
        dest_base: Destination directory (outputs/multimodal_data_snaps)
        log_path: Log file path

    Returns:
        dict with 'copied', 'missing', 'errors' counts
    """
    os.makedirs(dest_base, exist_ok=True)
    stats = {'copied': 0, 'missing': 0, 'errors': 0}

    for _, row in df.iterrows():
        src = os.path.join(src_base, str(row['subfolder']), str(row['image_filename']))

        if not os.path.exists(src):
            stats['missing'] += 1
            continue

        try:
            # Create chapter subfolder
            chapter_dir = os.path.join(dest_base, str(row['chapter_code']))
            os.makedirs(chapter_dir, exist_ok=True)

            # Rename to match data_snap_source (e.g., FL_01.png)
            new_filename = f"{row['data_snap_source']}.png"
            dest = os.path.join(chapter_dir, new_filename)

            shutil.copy(src, dest)
            stats['copied'] += 1

        except Exception as e:
            stats['errors'] += 1
            log_message(log_path, f"    Error copying {row['image_filename']}: {e}", also_print=False)

    log_message(log_path, f"  PNG copy stats: {stats['copied']} copied, {stats['missing']} missing, {stats['errors']} errors")
    return stats


def main():
    """Main execution function."""
    print("=" * 60)
    print("SCRIPT 01: DATA STANDARDIZATION")
    print("=" * 60)
    print()

    # Load configuration
    config = load_config()
    log_path, timestamp = setup_logging(config)

    log_message(log_path, "=" * 60)
    log_message(log_path, "AAAL 2026 DATA STANDARDIZATION")
    log_message(log_path, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log_message(log_path, "=" * 60)
    log_message(log_path, "")

    # Setup paths
    input_dir = os.path.join(PROJECT_ROOT, config['paths']['input_dir'])
    output_dir = os.path.join(PROJECT_ROOT, config['paths']['output_dir'])
    png_base_dir = '/Users/carolyndavis/Desktop/AAAL_2026_Pipeline/data/raw/data_snaps'

    os.makedirs(output_dir, exist_ok=True)

    # =========================================================================
    # Step 1: Load Unified CSV
    # =========================================================================
    log_message(log_path, "STEP 1: LOADING UNIFIED SOURCE FILE")
    log_message(log_path, "-" * 40)

    input_file = os.path.join(input_dir, 'tweet_analysis_complete.csv')
    if not os.path.exists(input_file):
        log_message(log_path, f"ERROR: Source file not found: {input_file}")
        return 1

    df = pd.read_csv(input_file, low_memory=False)
    log_message(log_path, f"  Loaded {len(df)} rows from {input_file}")
    log_message(log_path, "")

    # =========================================================================
    # Step 2: Generate data_snap_source
    # =========================================================================
    log_message(log_path, "STEP 2: GENERATING DATA_SNAP_SOURCE IDENTIFIERS")
    log_message(log_path, "-" * 40)

    df['data_snap_source'] = df.apply(
        lambda r: extract_data_snap_source(r['image_filename'], r['subfolder']), axis=1
    )

    null_ids = df['data_snap_source'].isna().sum()
    log_message(log_path, f"  Generated IDs. Null count: {null_ids}")
    log_message(log_path, f"  Sample IDs: {df['data_snap_source'].head(5).tolist()}")
    log_message(log_path, "")

    # =========================================================================
    # Step 3: Generate chapter_code
    # =========================================================================
    log_message(log_path, "STEP 3: GENERATING CHAPTER CODES")
    log_message(log_path, "-" * 40)

    df['chapter_code'] = df['subfolder'].apply(extract_chapter_code)
    chapters_found = df['chapter_code'].unique().tolist()
    log_message(log_path, f"  Chapters found: {chapters_found}")
    log_message(log_path, "")

    # =========================================================================
    # Step 4: Intelligent Fill (with OCR)
    # =========================================================================
    log_message(log_path, "STEP 4: INTELLIGENT FILL (WITH OCR RE-ANALYSIS)")
    log_message(log_path, "-" * 40)

    df, filled_stats = intelligent_fill(df, png_base_dir, log_path)
    log_message(log_path, "")

    # =========================================================================
    # Step 5: Verification Checks
    # =========================================================================
    log_message(log_path, "STEP 5: VERIFICATION CHECKS")
    log_message(log_path, "-" * 40)

    verify_stats = verify_capture_accuracy(df, log_path)

    # Check for missing PNGs
    missing_pngs = 0
    for _, row in df[df['image_filename'].notna()].iterrows():
        full_path = os.path.join(png_base_dir, str(row['subfolder']), str(row['image_filename']))
        if not os.path.exists(full_path):
            missing_pngs += 1
    log_message(log_path, f"  Missing PNGs: {missing_pngs}")
    log_message(log_path, "")

    # =========================================================================
    # Step 6: Drop Irrecoverable Rows
    # =========================================================================
    log_message(log_path, "STEP 6: DROPPING IRRECOVERABLE ROWS")
    log_message(log_path, "-" * 40)

    pre_drop = len(df)
    df = df[
        (df['tweet_text'].fillna('') != '') |
        ((df['image_present'] == True) & (df['image_tweet_text'].fillna('') != ''))
    ]
    dropped = pre_drop - len(df)
    log_message(log_path, f"  Dropped {dropped} irrecoverable rows")
    log_message(log_path, f"  Remaining rows: {len(df)}")
    log_message(log_path, "")

    # =========================================================================
    # Step 7: Duplicate Detection (within-chapter)
    # =========================================================================
    log_message(log_path, "STEP 7: DUPLICATE DETECTION (WITHIN-CHAPTER)")
    log_message(log_path, "-" * 40)

    # Detect duplicates and get IDs for removal
    df, dup_ids = detect_duplicates_with_shared(df, log_path)
    log_message(log_path, "")

    # =========================================================================
    # Step 8: Extract Duplicates for Traceability (before removal)
    # =========================================================================
    log_message(log_path, "STEP 8: EXTRACTING DUPLICATES FOR TRACEABILITY")
    log_message(log_path, "-" * 40)

    # Extract duplicate rows BEFORE removing them from main df
    # This preserves full Shared With mapping for epistemic stancetaking analysis (Heritage, 2012)
    dup_mask = df['Shared With'] != ''
    dup_df = df.loc[dup_mask, [
        'data_snap_source', 'tweet_date', 'username', 'tweet_text', 'word_count', 'Shared With', 'chapter_code'
    ]].copy()
    dup_df = dup_df.rename(columns={'username': 'user_name'})

    # Store pre-removal counts for reporting
    total_duplicates_detected = len(dup_df)
    log_message(log_path, f"  Extracted {total_duplicates_detected} duplicate rows for traceability")

    # Copy duplicate PNGs before removal
    dup_for_copy = df.loc[dup_mask, ['subfolder', 'image_filename', 'chapter_code']]
    copy_pngs(dup_for_copy, png_base_dir, os.path.join(output_dir, 'duplicates'), log_path)
    log_message(log_path, "")

    # =========================================================================
    # Step 9: Remove Duplicates from Main DataFrame (Biber et al., 1999)
    # =========================================================================
    log_message(log_path, "STEP 9: REMOVING DUPLICATES FROM MAIN DATASET")
    log_message(log_path, "-" * 40)

    # Per corpus linguistics best practices (Biber et al., 1999), remove duplicates
    # to ensure data integrity in the primary analysis datasets.
    # Duplicates are preserved in within_chapter_duplicates.xlsx for traceability.

    pre_removal_count = len(df)

    # Remove all rows that are duplicates (have non-empty Shared With)
    df_clean = df[df['Shared With'] == ''].copy()

    duplicates_removed = pre_removal_count - len(df_clean)
    log_message(log_path, f"  Pre-removal rows: {pre_removal_count}")
    log_message(log_path, f"  Duplicates removed: {duplicates_removed}")
    log_message(log_path, f"  Post-removal rows: {len(df_clean)}")
    log_message(log_path, "")

    # =========================================================================
    # Step 10: Split Data into Output Sets (from cleaned df)
    # ENHANCED: Stricter multimodal filtering for true 1:1 alignment
    # =========================================================================
    log_message(log_path, "STEP 10: SPLITTING DATA INTO OUTPUT SETS (STRICT MULTIMODAL FILTER)")
    log_message(log_path, "-" * 40)

    # FIX: Define STRICT multimodal filter - rows must have:
    # 1. image_present == True AND
    # 2. Valid image_filename (not NaN/empty) AND
    # 3. At least one of: image_tweet_text OR image_description populated
    # This prevents "no image attached" rows from leaking into image_df
    multimodal_mask = (
        (df_clean['image_present'] == True) &
        (df_clean['image_filename'].fillna('') != '') &
        (
            (df_clean['image_tweet_text'].fillna('') != '') |
            (df_clean['image_description'].fillna('') != '')
        )
    )

    log_message(log_path, f"  Strict multimodal filter applied:")
    log_message(log_path, f"    image_present=True: {(df_clean['image_present'] == True).sum()}")
    log_message(log_path, f"    valid image_filename: {(df_clean['image_filename'].fillna('') != '').sum()}")
    log_message(log_path, f"    has image content: {((df_clean['image_tweet_text'].fillna('') != '') | (df_clean['image_description'].fillna('') != '')).sum()}")
    log_message(log_path, f"    STRICT multimodal rows: {multimodal_mask.sum()}")

    # tweet_reorganized: Multimodal rows only (1:1 with image_df), DUPLICATES REMOVED
    tweet_df = df_clean.loc[multimodal_mask, [
        'data_snap_source', 'tweet_date', 'username', 'tweet_text', 'word_count'
    ]].copy()
    tweet_df = tweet_df.rename(columns={'username': 'user_name'})

    # image_reorganized: Rows with image data (1:1 with tweet_df), DUPLICATES REMOVED
    # FIX: Apply same mask to ensure perfect 1:1 alignment
    image_df = df_clean.loc[multimodal_mask, [
        'data_snap_source', 'tweet_date', 'username', 'image_tweet_text',
        'image_description', 'image_subjects', 'image_contains_face', 'detected_persons'
    ]].copy()
    image_df = image_df.rename(columns={'username': 'user_name'})

    # VALIDATION: Ensure 1:1 alignment (Heritage, 2012 - epistemic analysis traceability)
    assert len(tweet_df) == len(image_df), \
        f"1:1 ALIGNMENT FAILED: tweet_df ({len(tweet_df)}) != image_df ({len(image_df)})"
    assert tweet_df['data_snap_source'].tolist() == image_df['data_snap_source'].tolist(), \
        "1:1 ALIGNMENT FAILED: data_snap_source order mismatch"

    log_message(log_path, f"  tweet_reorganized: {len(tweet_df)} rows (multimodal, duplicates removed)")
    log_message(log_path, f"  image_reorganized: {len(image_df)} rows (1:1 alignment VERIFIED)")

    # text_only: Rows without image data (preserved separately for reviewers)
    text_only_mask = ~multimodal_mask
    text_only_df = df_clean.loc[text_only_mask, [
        'data_snap_source', 'tweet_date', 'username', 'tweet_text', 'word_count'
    ]].copy()
    text_only_df = text_only_df.rename(columns={'username': 'user_name'})
    log_message(log_path, f"  text_only: {len(text_only_df)} rows (non-multimodal)")

    # Log duplicate extraction (already done in Step 8)
    log_message(log_path, f"  duplicates (preserved): {len(dup_df)} rows")

    # Final validation summary
    log_message(log_path, f"  --- 1:1 MULTIMODAL ALIGNMENT CONFIRMED: {len(tweet_df)} rows ---")
    log_message(log_path, "")

    # =========================================================================
    # Step 11: Copy Text-Only PNGs
    # =========================================================================
    log_message(log_path, "STEP 11: COPYING TEXT-ONLY PNGs")
    log_message(log_path, "-" * 40)

    # Copy text_only PNGs (using cleaned df)
    text_only_for_copy = df_clean.loc[text_only_mask, ['subfolder', 'image_filename', 'chapter_code']]
    copy_pngs(text_only_for_copy, png_base_dir, os.path.join(output_dir, 'tweet_only'), log_path)
    log_message(log_path, "")

    # =========================================================================
    # Step 11.5: Copy/Rename Multimodal PNGs
    # =========================================================================
    log_message(log_path, "STEP 11.5: COPYING/RENAMING MULTIMODAL PNGs")
    log_message(log_path, "-" * 40)

    # Prepare multimodal rows for PNG copying (need subfolder, image_filename, data_snap_source, chapter_code)
    multimodal_for_copy = df_clean.loc[multimodal_mask, [
        'subfolder', 'image_filename', 'data_snap_source', 'chapter_code'
    ]].copy()

    # Copy and rename PNGs to multimodal_data_snaps/{chapter}/
    multimodal_png_dest = os.path.join(output_dir, 'multimodal_data_snaps')
    png_copy_stats = copy_and_rename_multimodal_pngs(
        multimodal_for_copy,
        png_base_dir,
        multimodal_png_dest,
        log_path
    )
    log_message(log_path, f"  Destination: {multimodal_png_dest}")
    log_message(log_path, "")

    # =========================================================================
    # Step 12: Blanket NaN Fill
    # =========================================================================
    log_message(log_path, "STEP 12: BLANKET NaN FILL")
    log_message(log_path, "-" * 40)

    # Fill NaN in output dataframes
    for out_df in [tweet_df, image_df, text_only_df]:
        str_cols = out_df.select_dtypes('object').columns
        num_cols = out_df.select_dtypes('number').columns
        out_df[str_cols] = out_df[str_cols].fillna('')
        out_df[num_cols] = out_df[num_cols].fillna(0)

    # Handle boolean columns in dup_df
    dup_df = dup_df.fillna({'Shared With': ''})
    str_cols = dup_df.select_dtypes('object').columns
    num_cols = dup_df.select_dtypes('number').columns
    dup_df[str_cols] = dup_df[str_cols].fillna('')
    dup_df[num_cols] = dup_df[num_cols].fillna(0)

    log_message(log_path, "  NaN values filled")
    log_message(log_path, "")

    # =========================================================================
    # Step 13: Save Outputs (Multi-Sheet by Chapter) - SYMMETRIC FORMAT
    # ENHANCED: Validates 1:1 alignment per sheet for academic pipeline reliability
    # =========================================================================
    log_message(log_path, "STEP 13: SAVING OUTPUTS (MULTI-SHEET BY CHAPTER - SYMMETRIC)")
    log_message(log_path, "-" * 40)

    # Get chapter list from config (15 chapters)
    chapter_list = config.get('chapters', [])
    log_message(log_path, f"  Creating symmetric sheets for {len(chapter_list)} chapters")

    # Add chapter_code to tweet_df and image_df for filtering
    # Extract chapter code from data_snap_source (e.g., "FL_01" -> "FL")
    tweet_df['chapter_code'] = tweet_df['data_snap_source'].apply(
        lambda x: str(x).split('_')[0] if pd.notna(x) else None
    )
    image_df['chapter_code'] = image_df['data_snap_source'].apply(
        lambda x: str(x).split('_')[0] if pd.notna(x) else None
    )

    # FIX: Save both files simultaneously with symmetric validation
    tweet_path = os.path.join(output_dir, 'tweet_reorganized_standardized.xlsx')
    image_path = os.path.join(output_dir, 'image_reorganized_standardized.xlsx')
    tweet_sheet_counts = {}
    image_sheet_counts = {}

    # Track totals for validation
    total_tweet_rows = 0
    total_image_rows = 0

    log_message(log_path, "  --- TWEET_REORGANIZED (15 sheets) ---")
    with pd.ExcelWriter(tweet_path, engine='openpyxl') as writer:
        for chapter_full in chapter_list:
            # Extract short code from chapter name (CHD_AZ -> AZ, CHD_MAIN -> MAIN)
            chapter_code = chapter_full.replace('CHD_', '').rstrip('_')
            chapter_data = tweet_df[tweet_df['chapter_code'] == chapter_code].drop(columns=['chapter_code'])
            sheet_name = chapter_full
            chapter_data.to_excel(writer, sheet_name=sheet_name, index=False)
            tweet_sheet_counts[chapter_full] = len(chapter_data)
            total_tweet_rows += len(chapter_data)
            if len(chapter_data) > 0:
                log_message(log_path, f"    {sheet_name}: {len(chapter_data)} tweets")
    log_message(log_path, f"  Saved: {tweet_path} (TOTAL: {total_tweet_rows} rows)")

    log_message(log_path, "  --- IMAGE_REORGANIZED (15 sheets) ---")
    with pd.ExcelWriter(image_path, engine='openpyxl') as writer:
        for chapter_full in chapter_list:
            chapter_code = chapter_full.replace('CHD_', '').rstrip('_')
            chapter_data = image_df[image_df['chapter_code'] == chapter_code].drop(columns=['chapter_code'])
            sheet_name = chapter_full
            chapter_data.to_excel(writer, sheet_name=sheet_name, index=False)
            image_sheet_counts[chapter_full] = len(chapter_data)
            total_image_rows += len(chapter_data)
            if len(chapter_data) > 0:
                log_message(log_path, f"    {sheet_name}: {len(chapter_data)} images")
    log_message(log_path, f"  Saved: {image_path} (TOTAL: {total_image_rows} rows)")

    # VALIDATION: Verify symmetric sheet counts (Biber et al., 1999 - corpus integrity)
    symmetric_validation_passed = True
    for chapter_full in chapter_list:
        if tweet_sheet_counts[chapter_full] != image_sheet_counts[chapter_full]:
            log_message(log_path, f"  WARNING: Asymmetric count for {chapter_full}: "
                       f"tweets={tweet_sheet_counts[chapter_full]}, images={image_sheet_counts[chapter_full]}")
            symmetric_validation_passed = False

    if symmetric_validation_passed:
        log_message(log_path, f"  ✓ SYMMETRIC VALIDATION PASSED: All 15 sheets match")
    else:
        log_message(log_path, f"  ✗ SYMMETRIC VALIDATION FAILED: Check above warnings")

    # Final totals validation
    assert total_tweet_rows == total_image_rows, \
        f"TOTAL MISMATCH: tweets={total_tweet_rows}, images={total_image_rows}"
    log_message(log_path, f"  ✓ TOTAL ROWS MATCH: {total_tweet_rows} across {len(chapter_list)} sheets")

    # Save text_only (single sheet - non-multimodal rows)
    text_only_path = os.path.join(output_dir, 'text_only_tweets.xlsx')
    text_only_df.to_excel(text_only_path, index=False, sheet_name='Text_Only')
    log_message(log_path, f"  Saved: {text_only_path} ({len(text_only_df)} rows)")

    # Save duplicates (sheets by chapter with data) - preserved for traceability (Heritage, 2012)
    dup_path = os.path.join(output_dir, 'within_chapter_duplicates.xlsx')
    with pd.ExcelWriter(dup_path, engine='openpyxl') as writer:
        for chapter in sorted(dup_df['chapter_code'].unique()):
            chapter_data = dup_df[dup_df['chapter_code'] == chapter].drop(columns=['chapter_code'])
            if len(chapter_data) > 0:
                sheet_name = f"CHD_{chapter}" if chapter != 'MAIN' else 'CHD_MAIN'
                chapter_data.to_excel(writer, sheet_name=sheet_name, index=False)
                log_message(log_path, f"    {sheet_name}: {len(chapter_data)} duplicates")
    log_message(log_path, f"  Saved: {dup_path} ({len(dup_df)} rows, preserved for traceability)")
    log_message(log_path, "")

    # =========================================================================
    # Step 14: Generate Preparation Report
    # =========================================================================
    log_message(log_path, "STEP 14: GENERATING PREPARATION REPORT")
    log_message(log_path, "-" * 40)

    report_path = os.path.join(output_dir, 'preparation_report.txt')
    with open(report_path, 'w') as f:
        f.write(f"AAAL 2026 CORPUS PREPARATION REPORT\n")
        f.write(f"Generated: {timestamp}\n")
        f.write("=" * 60 + "\n\n")

        f.write("CORPUS SUMMARY (Post-Duplicate Removal):\n")
        f.write(f"  Total rows after cleaning: {len(df_clean)}\n")
        f.write(f"  Final multimodal rows: {total_tweet_rows} across {len(chapter_list)} sheets\n")
        f.write(f"  Text-only extracted: {len(text_only_df)} ({len(text_only_df)/len(df_clean)*100:.1f}%)\n")
        f.write(f"  1:1 Alignment: VERIFIED (tweet_df == image_df == {total_tweet_rows})\n\n")

        f.write("DUPLICATE HANDLING (Biber et al., 1999):\n")
        f.write(f"  Within-chapter duplicates detected: {total_duplicates_detected}\n")
        f.write(f"  Duplicates removed from main datasets: {duplicates_removed}\n")
        f.write(f"  Duplicates preserved for traceability: {len(dup_df)}\n\n")

        f.write("PNG COPY STATS (multimodal_data_snaps):\n")
        f.write(f"  PNGs copied: {png_copy_stats['copied']}\n")
        f.write(f"  PNGs missing: {png_copy_stats['missing']}\n")
        f.write(f"  Copy errors: {png_copy_stats['errors']}\n")
        f.write(f"  Destination: {multimodal_png_dest}\n\n")

        f.write("FILLED STATS:\n")
        f.write(f"  Word count recomputed: {filled_stats['word_count']}\n")
        f.write(f"  Hashtags extracted: {filled_stats['hashtags']}\n")
        f.write(f"  OCR image_tweet_text filled: {filled_stats['ocr_text']}\n")
        f.write(f"  OCR image_description filled: {filled_stats['ocr_desc']}\n\n")

        f.write("VERIFICATION:\n")
        f.write(f"  Word count mismatches: {verify_stats['mismatches']}\n")
        f.write(f"  Empty tweet_text: {verify_stats['empty_tweet']}\n")
        f.write(f"  Inconsistent OCR: {verify_stats['inconsistent_ocr']}\n")
        f.write(f"  Missing PNGs (source): {missing_pngs}\n\n")

        f.write("OUTPUT FILES (Multi-Sheet by Chapter - SYMMETRIC):\n")
        f.write(f"  {tweet_path}\n")
        f.write(f"    -> {total_tweet_rows} rows, {len(chapter_list)} sheets\n")
        f.write(f"  {image_path}\n")
        f.write(f"    -> {total_image_rows} rows, {len(chapter_list)} sheets\n")
        f.write(f"  {text_only_path}\n")
        f.write(f"    -> {len(text_only_df)} rows, 1 sheet\n")
        f.write(f"  {dup_path}\n")
        f.write(f"    -> {len(dup_df)} rows, preserved for traceability\n\n")

        f.write("SYMMETRIC VALIDATION:\n")
        f.write(f"  Status: {'PASSED' if symmetric_validation_passed else 'FAILED'}\n")
        f.write(f"  Total tweets: {total_tweet_rows}\n")
        f.write(f"  Total images: {total_image_rows}\n")
        f.write(f"  Match: {total_tweet_rows == total_image_rows}\n\n")

        f.write("CHAPTER BREAKDOWN (1:1 multimodal alignment):\n")
        f.write(f"  {'Chapter':<12} {'Tweets':>8} {'Images':>8} {'Match':>8}\n")
        f.write(f"  {'-'*12} {'-'*8} {'-'*8} {'-'*8}\n")
        for chapter in sorted(tweet_sheet_counts.keys()):
            t_count = tweet_sheet_counts[chapter]
            i_count = image_sheet_counts[chapter]
            match = "✓" if t_count == i_count else "✗"
            f.write(f"  {chapter:<12} {t_count:>8} {i_count:>8} {match:>8}\n")

    log_message(log_path, f"  Saved: {report_path}")
    log_message(log_path, "")

    # =========================================================================
    # Final Summary
    # =========================================================================
    log_message(log_path, "=" * 60)
    log_message(log_path, "SCRIPT 01 COMPLETE - SYMMETRIC VALIDATION")
    log_message(log_path, "=" * 60)
    log_message(log_path, f"Final multimodal rows: {total_tweet_rows} across {len(chapter_list)} sheets")
    log_message(log_path, f"1:1 Alignment: VERIFIED (tweet == image == {total_tweet_rows})")
    log_message(log_path, f"Duplicates preserved: {len(dup_df)} (for traceability, Heritage 2012)")
    log_message(log_path, f"Symmetric validation: {'PASSED' if symmetric_validation_passed else 'FAILED'}")
    log_message(log_path, f"Log: {log_path}")
    log_message(log_path, f"Report: {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
