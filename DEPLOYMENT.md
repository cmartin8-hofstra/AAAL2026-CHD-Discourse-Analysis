# Deployment Instructions for AAAL 2026 Repository

## Quick Start: Hosting on GitHub

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `AAAL2026-CHD-Discourse-Analysis`
3. Description: "Computational forensic linguistics analysis of vaccine hesitancy discourse"
4. Select **Public** (required for academic reproducibility)
5. **Do NOT** initialize with README (we already have one)
6. Click "Create repository"

### Step 2: Upload Repository Contents

**Option A: Using Git Command Line (Recommended)**

```bash
# Navigate to the unzipped repository folder
cd AAAL2026_Repository

# Initialize git repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: AAAL 2026 CHD Discourse Analysis Pipeline"

# Add remote (replace [username] with your GitHub username)
git remote add origin https://github.com/[username]/AAAL2026-CHD-Discourse-Analysis.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Option B: Using GitHub Web Interface**

1. Download the ZIP file
2. Unzip to your computer
3. Go to your new repository on GitHub
4. Click "uploading an existing file"
5. Drag and drop all contents from the unzipped folder
6. Commit changes

### Step 3: Enable GitHub Pages (Optional - for README viewing)

1. Go to repository Settings
2. Click "Pages" in left sidebar
3. Source: "Deploy from a branch"
4. Branch: main / root
5. Click Save

### Step 4: Add DOI via Zenodo

1. Go to https://zenodo.org/
2. Log in with GitHub
3. Enable Zenodo sync for your repository
4. Create a GitHub Release (tag: v1.0.0)
5. Zenodo will automatically create a DOI
6. Update README.md badge with the real DOI

---

## Repository Checklist

### ✅ Code (7 scripts)
- [ ] `01_data_standardization.py` - 35KB
- [ ] `02_pmi_analysis.py` - 19KB
- [ ] `03_epistemic_analysis.py` - 15KB
- [ ] `04_sentiment_validation.py` - 16KB
- [ ] `05_exemplar_extraction.py` - 15KB
- [ ] `06_multimodal_coding_template.py` - 12KB
- [ ] `07_generate_visualizations.py` - 11KB

### ✅ Configuration
- [ ] `config/config.yaml` - Complete parameter specification

### ✅ Data (Analyzed)
- [ ] `validated_corpus.csv` - 1,239 rows, 21 columns
- [ ] `selected_exemplars.csv` - 150 rows, 23 columns
- [ ] `pmi_corpus_statistics.csv` - 15 rows (chapter stats)

### ✅ Reports
- [ ] `preparation_report.txt`
- [ ] `pmi_analysis_report.txt`
- [ ] `epistemic_analysis_report.txt`
- [ ] `validation_report.txt`
- [ ] `exemplar_extraction_report.txt`
- [ ] `coding_template_report.txt`

### ✅ Documentation
- [ ] `README.md` - Comprehensive project documentation
- [ ] `METHODOLOGY.md` - Detailed methods
- [ ] `CODEBOOK.md` - Qualitative coding instructions
- [ ] `CITATION.cff` - Academic citation metadata
- [ ] `LICENSE` - MIT License
- [ ] `requirements.txt` - Python dependencies
- [ ] `.gitignore` - Excludes logs, caches, raw data

---

## Data Privacy Considerations

### Included in Repository
- Analyzed CSV data (tweet text, metadata, computed features)
- Usernames (public Twitter handles for methodological transparency)
- All Python scripts and configuration

### NOT Included (Too Large / Privacy)
- Raw PNG screenshots (1,239 images)
- Original input CSV with full Claude Vision output
- Excel files (.xlsx versions of CSVs)

### To Request Full Data
Researchers can contact you for:
- Full PNG image archive
- Excel workbooks
- Raw Claude Vision API output

---

## Verification Commands

Run these after cloning to verify integrity:

```bash
# Check row counts
python -c "import pandas as pd; print('Validated:', len(pd.read_csv('data/analyzed/validated_corpus.csv')))"
# Expected: 1239

python -c "import pandas as pd; print('Exemplars:', len(pd.read_csv('data/analyzed/selected_exemplars.csv')))"
# Expected: 150

# Check chapter distribution
python -c "
import pandas as pd
df = pd.read_csv('data/analyzed/validated_corpus.csv')
print('Chapters:', df['chapter_code'].nunique())
print(df['chapter_code'].value_counts())
"
# Expected: 15 chapters
```

---

## AAAL Submission Checklist

For the conference submission:

1. **Abstract**: Already submitted (document in project)

2. **Supplementary Materials Link**:
   ```
   Repository: https://github.com/[username]/AAAL2026-CHD-Discourse-Analysis
   DOI: https://doi.org/10.5281/zenodo.XXXXXXX
   ```

3. **Reproducibility Statement**:
   ```
   All analysis code, configuration parameters, and analyzed data 
   are publicly available at [GitHub URL]. Raw data (screenshot images)
   available upon request for privacy considerations.
   ```

4. **Citation in Presentation**:
   ```
   Code and data: github.com/[username]/AAAL2026-CHD-Discourse-Analysis
   ```

---

## Troubleshooting

### "Tesseract not found" Error
Script 01 requires Tesseract OCR:
- macOS: `brew install tesseract`
- Ubuntu: `sudo apt install tesseract-ocr`
- Windows: Download installer from GitHub

### "File not found" Errors
Ensure you're running scripts from the repository root:
```bash
cd AAAL2026-CHD-Discourse-Analysis
python scripts/02_pmi_analysis.py
```

### Large File Issues on GitHub
If any file exceeds 100MB:
1. Use Git LFS: `git lfs track "*.csv"`
2. Or exclude from git and host separately

---

## Contact

For questions about the repository or data access requests:

**Carolyn Davis**  
MA Candidate, Forensic Linguistics  
Hofstra University  
[Email address]

---

*Last updated: January 2026*
