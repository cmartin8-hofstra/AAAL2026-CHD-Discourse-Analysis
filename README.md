# Epistemic Stancetaking and Fear Appeals by CHD on Twitter (X)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Preprint](https://img.shields.io/badge/Status-Preprint-orange.svg)]()
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> **REPOSITORY STATUS**: This repository is currently **PRIVATE** and under active development. It will be made public after presentation at AAAL 2026 (March 2026) and subsequent manuscript publication.

---

## About This Project

This repository contains the complete computational analysis pipeline for a forensic linguistics study examining vaccine hesitancy discourse strategies employed by Children's Health Defense (CHD) state chapters on Twitter/X. Using a mixed-methods approach combining computational corpus linguistics with qualitative multimodal discourse analysis, we investigate how these organizations construct persuasive health misinformation through coordinated linguistic and visual strategies.

**Research Questions:**
1. How do CHD state chapters employ epistemic stancetaking (Heritage, 2012) to construct authority while potentially evading platform moderation?
2. What lexical association patterns (PMI analysis) characterize vaccine-related discourse across geographic chapters?
3. How do multimodal fear appeals (Gill & Lennon, 2022) integrate text and imagery to construct threat narratives?

**Conference Presentation**: American Association for Applied Linguistics (AAAL) 2026
**Presentation Date**: March 2026
**Manuscript Status**: In preparation

---

## Authors

**Carolyn Martin** (nee Davis)
MA Candidate, Forensic Linguistics
Hofstra University
<!-- Email will be added after publication -->

**Dr. [PROFESSOR_NAME]** (Advisor)
<!-- Title/Department to be added -->
Hofstra University
<!-- Email will be added after publication -->

> **Note**: ORCID identifiers will be added when repository becomes public.

---

## Repository Structure

```
github_launch/
├── README.md                    # This file
├── METHODOLOGY.md               # Detailed methods documentation (APA 7th)
├── CODEBOOK.md                  # Qualitative coding instructions
├── CITATION.cff                 # Citation metadata
├── LICENSE                      # MIT License
├── requirements.txt             # Python dependencies
├── DEPLOYMENT.md                # GitHub setup instructions
├── .gitignore                   # Git exclusions
│
├── scripts/                     # 7-script analysis pipeline
│   ├── 01_data_standardization.py
│   ├── 02_pmi_analysis.py
│   ├── 03_epistemic_analysis.py
│   ├── 04_sentiment_validation.py
│   ├── 05_exemplar_extraction.py
│   ├── 06_multimodal_coding_template.py
│   └── 07_generate_visualizations.py
│
├── config/
│   └── config.yaml              # Complete parameter specification
│
└── data/
    └── analyzed/
        ├── validated_corpus.csv          # 1,239 analyzed tweets
        ├── selected_exemplars.csv        # 150 exemplars (10 per chapter)
        ├── pmi_corpus_statistics.csv     # Chapter-level stats
        └── *.txt                         # 6 analysis reports
```

---

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Tesseract OCR (for Script 01 only)
  - macOS: `brew install tesseract`
  - Ubuntu: `sudo apt install tesseract-ocr`
  - Windows: [Download installer](https://github.com/UB-Mannheim/tesseract/wiki)

### Installation

```bash
# Clone repository (after it becomes public)
git clone https://github.com/[username]/AAAL2026-CHD-Discourse-Analysis.git
cd AAAL2026-CHD-Discourse-Analysis

# Install dependencies
pip install -r requirements.txt

# Verify installation
python scripts/02_pmi_analysis.py --help
```

### Running the Pipeline

**Note**: Scripts 01 (data standardization) requires raw input data not included in this repository. Scripts 02-07 can be run using the provided analyzed data.

```bash
# Example: Re-run PMI analysis
python scripts/02_pmi_analysis.py

# Example: Generate visualizations
python scripts/07_generate_visualizations.py
```

---

## Corpus Summary

### Final Validated Dataset

| Metric | Count | Notes |
|--------|-------|-------|
| **Total tweets analyzed** | 1,239 | Multimodal corpus (text + image) |
| **CHD accounts** | 15 | 14 state chapters + CHD national |
| **Data collection period** | Spring 2025 | Public tweets only |
| **Exemplars selected** | 150 | 10 per chapter, composite scoring |
| **Analysis dimensions** | 3 | PMI + Epistemic + Sentiment |

### Pipeline Workflow

```
Raw Screenshots (1,545)
    | [01_data_standardization.py]
Validated Corpus (1,239) <- 1:1 text-image alignment verified
    | [02_pmi_analysis.py]
PMI Enriched (233 tweets with vaccine collocations)
    | [03_epistemic_analysis.py]
Epistemic Classified (679 with K+/K-/Mixed stance)
    | [04_sentiment_validation.py]
Sentiment Validated (Mean compound = 0.076)
    | [05_exemplar_extraction.py]
Exemplars Selected (150, composite scores 2.39-5.54)
    | [06_multimodal_coding_template.py]
Coding Template Generated (150 blank rows for qualitative analysis)
    | [07_generate_visualizations.py]
Publication Figures (5 figures, 3 formats each)
```

---

## Key Findings (Preliminary)

### 1. The Epistemic Paradox
Tweets using hedging language (K-) contain **significantly more vaccine-related content** than tweets using certain language (K+), contradicting Heritage's (2012) framework expectations. This suggests CHD chapters may strategically use uncertainty markers to evade platform moderation while still conveying anti-vaccine messages.

**Statistical Evidence:**
- K+ (high certainty): 20.0% of corpus (n=248)
- K- (low certainty): 4.3% of corpus (n=53)
- K- tweets average **higher PMI scores** than K+ tweets

### 2. Coordinated Lexical Patterns
PMI analysis reveals shared vocabulary patterns across geographically dispersed chapters, suggesting centralized messaging strategies rather than organic, local discourse.

**Top Collocations (PMI > 6.0):**
- vaccine -> injuries (PMI = 6.70, CHD Virginia)
- vaccine -> death (PMI = 6.70, CHD Virginia)
- vax -> unvax (PMI = 6.67, CHD Washington)

### 3. Geographic Variation in Intensity
One-way ANOVA reveals significant differences in sentiment across chapters, F(14, 1224) = 3.89, p < .001, eta-squared = 0.04, suggesting some state chapters employ more emotionally charged messaging than others.

---

## Methodology Overview

This project employs a **mixed-methods computational linguistics approach** integrating:

1. **Lexical Association Analysis** (Church & Hanks, 1990)
   - Pointwise Mutual Information (PMI) with +/-3 word window
   - 27 vaccine-related anchor terms
   - Minimum frequency threshold: 2

2. **Epistemic Stance Classification** (Heritage, 2012; Hyland, 1998)
   - 25 hedge markers (K-)
   - 26 booster markers (K+)
   - Minimum stance threshold: 2 markers

3. **Sentiment Analysis** (Hutto & Gilbert, 2014)
   - VADER for social media text
   - Compound scores: -1 (negative) to +1 (positive)

4. **Multimodal Fear Appeals Framework** (Gill & Lennon, 2022)
   - 6 coding categories: Composition, Color, Represented Participants, Perspective, Textual Components, Fear Integration
   - Manual qualitative coding of 150 exemplars

5. **Statistical Validation** (Biber et al., 1999)
   - Pearson correlations for feature relationships
   - One-way ANOVA for chapter variation
   - APA 7th edition formatted results

**For complete methodology**: See [METHODOLOGY.md](METHODOLOGY.md)

---

## Theoretical Frameworks

| Framework | Citation | Application |
|-----------|----------|-------------|
| **Epistemic Stancetaking** | Heritage (2012) | K+/K- classification system |
| **PMI Analysis** | Church & Hanks (1990) | Lexical association measures |
| **Hedge/Booster Lexicons** | Hyland (1998); Hinkel (2005) | Epistemic marker inventories |
| **Sentiment Analysis** | Hutto & Gilbert (2014) | VADER for social media |
| **Multimodal Fear Appeals** | Gill & Lennon (2022) | Visual meta-functions framework |
| **Corpus Linguistics** | Biber et al. (1999) | Quality control standards |
| **Register Variation** | Egbert & Biber (2019) | Geographic stratification |
| **Digital Discourse** | Androutsopoulos (2014) | Multimodal integration |

---

## Data Access & Ethics

### Current Status (Private Repository)
Data files are included in this private repository for:
- Advisor review and collaboration
- AAAL 2026 presentation preparation
- Manuscript development

### Post-Publication (Public Repository)
After manuscript acceptance, the following will be publicly available:
- validated_corpus.csv (1,239 analyzed tweets)
- selected_exemplars.csv (150 exemplars)
- All Python scripts and configuration files
- Analysis reports and corpus statistics

### Available Upon Request
- Raw PNG screenshots (1,239 images, ~800MB)
- Excel workbooks (.xlsx versions of CSVs)
- Additional documentation

### Ethical Considerations
- **Public data only**: All tweets were publicly accessible at time of collection
- **Usernames included**: Twitter handles are public identifiers necessary for methodological transparency and verification
- **Platform TOS compliance**: Data collection and analysis comply with Twitter/X Terms of Service
- **No private/protected accounts**: Only public organizational accounts analyzed
- **Academic fair use**: Analysis for scholarly research and criticism

---

## Citation

### Pre-Publication Citation (Current)

Use this format until manuscript is published:

```
Martin, C., & [Professor Last Name], [Initial]. (2026). Epistemic Stancetaking
  and Fear Appeals by State Chapters of Children's Health Defense on Twitter (X).
  Paper presented at the American Association for Applied Linguistics (AAAL)
  2026 Conference, [City], [State].
```

### Post-Publication Citation

After manuscript acceptance, see `CITATION.cff` for updated citation format including journal details and DOI.

### Software Citation

To cite the computational pipeline:

```
Martin, C., & [Professor Last Name], [Initial]. (2026). AAAL2026-CHD-Discourse-Analysis
  [Computer software]. GitHub. https://github.com/[username]/AAAL2026-CHD-Discourse-Analysis
```

---

## Reproducibility

### Complete Parameter Specification
All analysis parameters are externalized in `config/config.yaml`:
- PMI: anchor terms, window size, minimum frequency
- Epistemic: hedge/booster lexicons, classification thresholds
- Selection: composite scoring weights and normalization caps
- Paths: all directory locations (relative to repository root)

### Replication Package
This repository includes everything needed to replicate the analysis:
- Complete source code (7 scripts, ~130KB)
- Configuration files (all parameters documented)
- Analyzed data (validated corpus, exemplars, statistics)
- Analysis reports (7 detailed reports with methodology)
- Dependencies specification (requirements.txt)

### Verification Commands

```bash
# Verify corpus row counts
python -c "import pandas as pd; print('Validated:', len(pd.read_csv('data/analyzed/validated_corpus.csv')))"
# Expected output: Validated: 1239

python -c "import pandas as pd; print('Exemplars:', len(pd.read_csv('data/analyzed/selected_exemplars.csv')))"
# Expected output: Exemplars: 150

# Verify chapter distribution
python -c "
import pandas as pd
df = pd.read_csv('data/analyzed/validated_corpus.csv')
print('Chapters:', df['chapter_code'].nunique())
print(df['chapter_code'].value_counts().sort_index())
"
# Expected output: Chapters: 15
```

---

## Contributing

**Current Status**: This is a private repository for a specific research project. Contributions are not being accepted at this time.

**After Publication**: If you identify errors or have suggestions after the repository becomes public, please open an issue on GitHub.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**What this means:**
- You can use, modify, and distribute this code
- You can use it for commercial purposes
- You must include the original copyright notice
- No warranty or liability (use at your own risk)

**Note**: The MIT License applies to the code and methodology. Data is subject to Twitter/X Terms of Service and academic ethical guidelines for research involving public social media content.

---

## Acknowledgments

- **Hofstra University**: MA Forensic Linguistics Program
- **Anthropic**: Claude Vision API for multimodal content analysis
- **AAAL 2026**: Conference platform for dissemination

### Software & Libraries

This project builds on excellent open-source tools:
- **pandas** - Data manipulation
- **VADER Sentiment** - Social media sentiment analysis
- **pytesseract** - OCR text extraction
- **matplotlib/seaborn** - Data visualization
- **scipy** - Statistical analysis
- **networkx** - Network graph analysis

---

## Repository Timeline

| Date | Milestone |
|------|-----------|
| **January 2026** | Private repository created |
| **March 2026** | AAAL conference presentation |
| **Spring 2026** | Manuscript submission |
| **Post-acceptance** | Repository made public |
| **Post-publication** | Zenodo DOI assigned |

---

## Contact

For questions about this research:

**Carolyn Martin** (nee Davis)
MA Candidate, Forensic Linguistics
Hofstra University
<!-- Email will be added after publication -->

**Dr. [PROFESSOR_NAME]**
<!-- Title/Department to be added -->
Hofstra University
<!-- Email will be added after publication -->

---

## Version History

- **v0.9.0-preprint** (January 2026): Private repository created for AAAL 2026 submission
- **v1.0.0** (TBD): Public release after manuscript acceptance

---

*Last Updated: January 16, 2026*
*Repository Status: Private (will be made public post-publication)*
*For AAAL 2026 Conference Submission*
