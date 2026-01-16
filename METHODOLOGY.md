# Methodology Documentation

## AAAL 2026: Epistemic Stancetaking and Fear Appeals Analysis

This document provides detailed methodological documentation for the computational pipeline analyzing Children's Health Defense (CHD) Twitter/X discourse.

---

## 1. Data Collection

### 1.1 Corpus Construction

**Source**: Public Twitter/X posts from 15 CHD accounts (14 state chapters + national)

**Collection Period**: Spring 2025

**Method**: Screenshot capture with Claude Vision API analysis

**Initial Corpus**: n = 1,545 screenshot posts

### 1.2 Accounts Sampled

| Account | State | Tweet Count | % of Corpus |
|---------|-------|-------------|-------------|
| @ChildrensHD | National | 98 | 7.9% |
| @CHDArizona | Arizona | 72 | 5.8% |
| @CHDFlorida | Florida | 87 | 7.0% |
| @CHDHawaii | Hawaii | 30 | 2.4% |
| @CHDIndiana | Indiana | 75 | 6.1% |
| @CHDKansas | Kansas | 101 | 8.2% |
| @CHDMaryland | Maryland | 84 | 6.8% |
| @CHDMichigan | Michigan | 97 | 7.8% |
| @CHDMinnesota | Minnesota | 91 | 7.3% |
| @CHDNewJersey | New Jersey | 77 | 6.2% |
| @CHDNewYork | New York | 90 | 7.3% |
| @CHDPA | Pennsylvania | 80 | 6.5% |
| @CHDTennessee | Tennessee | 93 | 7.5% |
| @CHDVirginia | Virginia | 102 | 8.2% |
| @CHDWashington | Washington | 62 | 5.0% |
| **Total** | | **1,239** | **100%** |

---

## 2. Data Processing (Script 01)

### 2.1 Standardization Steps

1. **Data Snap Source Generation**
   - Unique identifier format: `{CHAPTER}_{NUMBER}` (e.g., "FL_01")
   - Enables 1:1 tweet-image alignment traceability

2. **OCR Re-Analysis**
   - Tesseract OCR for missing `image_tweet_text`
   - PSM 6 configuration for uniform text blocks
   - 272 rows recovered via OCR

3. **Duplicate Detection**
   - Within-chapter duplicate identification
   - Word count threshold: >3 words (prevents hashtag-only matches)
   - Normalized text comparison (case-insensitive, whitespace-stripped)

### 2.2 Exclusion Criteria

| Exclusion Type | Count | Reason |
|----------------|-------|--------|
| Quality failures | 73 | Empty text or unrecoverable OCR |
| Duplicates | 39 | Same content shared across posts |
| Text-only | 194 | No image present (separate analysis) |
| **Total excluded** | **306** | |
| **Final corpus** | **1,239** | Validated multimodal pairs |

### 2.3 Validation Checks

- **1:1 Alignment**: Verified tweet_df rows == image_df rows
- **Symmetric sheets**: All 15 chapter sheets match in both files
- **PNG verification**: All 1,239 images confirmed present

---

## 3. PMI Analysis (Script 02)

### 3.1 Theoretical Framework

**Citation**: Church, K. W., & Hanks, P. (1990). Word association norms, mutual information, and lexicography. *Computational Linguistics, 16*(1), 22-29.

### 3.2 PMI Formula

```
PMI(x,y) = log₂(P(x,y) / (P(x) × P(y)))
```

Where:
- P(x,y) = probability of x and y co-occurring
- P(x) = probability of x occurring
- P(y) = probability of y occurring

### 3.3 Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Window size | ±3 words | Captures local collocational context |
| Min frequency | 2 | Filters noise, ensures statistical stability |
| Anchor terms | 27 | Harmonized vaccine-related vocabulary |
| Stopwords | 179 | NLTK English stopwords (Egbert & Biber, 2019) |

### 3.4 Anchor Terms (27)

**Core terms**: vaccine, vaccines, vaccination, vaccinated, vax, vaxx, vaxxed, unvaxxed, vaxxine, vx

**Colloquial**: jab, jabs, shot, shots, injection, injections

**Booster/Tech**: booster, boosters, immunization, mrna, pfizer, moderna

**Compound (post-normalization)**: covidvaccine, covidjab, covidshot, covid19vaccine

### 3.5 Multiword Normalization

Applied BEFORE tokenization:
- "covid vaccine" → "covidvaccine"
- "mrna vaccine" → "mrnavaccine"
- "pfizer vaccine" → "pfizervaccine"

### 3.6 Results

| Metric | Value |
|--------|-------|
| Tweets with PMI content | 233 (18.8%) |
| Mean PMI sum | 18.360 |
| Max PMI sum | 83.882 |
| Total PMI pairs calculated | 846 |

---

## 4. Epistemic Analysis (Script 03)

### 4.1 Theoretical Framework

**Primary**: Heritage, J. (2012). Epistemic engine: Sequence organization and territories of knowledge. *Research on Language and Social Interaction, 45*(1), 30-52.

**Lexicons**: Hyland, K. (1998). Hedging in scientific research articles. *John Benjamins Publishing*.

**Validation**: Hinkel, E. (2005). Hedging, inflating, and persuading in L2 academic writing. *Applied Language Learning, 15*(1&2), 29-53.

### 4.2 K+/K- Framework

| Stance | Definition | Markers Required |
|--------|------------|-----------------|
| K+ (High certainty) | Booster-dominant | ≥2 boosters, boosters > hedges |
| K- (Low certainty) | Hedge-dominant | ≥2 hedges, hedges > boosters |
| Mixed | Both present | ≥1 hedge AND ≥1 booster |
| Neutral | No markers | 0 hedges AND 0 boosters |

### 4.3 Hedge Markers (25)

may, might, could, would, perhaps, possibly, probably, likely, suggests, appears, seems, assume, believe, think, indicate, arguably, reportedly, allegedly, approximately, roughly, maybe, tend, tends, uncertain, unclear

### 4.4 Booster Markers (26)

clearly, obviously, certainly, definitely, undoubtedly, absolutely, always, never, proven, proof, evidence, fact, facts, demonstrate, demonstrates, show, shows, establish, confirm, confirmed, must, will, know, known, truth, true

### 4.5 Epistemic Density Calculation

```
Epistemic Density = (hedge_count + booster_count) / word_count × 100
```

### 4.6 Results

| Stance | Count | Percentage |
|--------|-------|------------|
| K+ (High certainty) | 248 | 20.0% |
| K- (Low certainty) | 53 | 4.3% |
| Mixed | 51 | 4.1% |
| Neutral | 887 | 71.6% |

Mean epistemic density: 1.732 markers per 100 words

---

## 5. Sentiment Analysis (Script 04)

### 5.1 Theoretical Framework

**Citation**: Hutto, C., & Gilbert, E. (2014). VADER: A parsimonious rule-based model for sentiment analysis of social media text. *Proceedings of the International AAAI Conference on Web and Social Media*.

### 5.2 VADER Features

- **Sentiment lexicon**: Validated ratings for 7,500+ features
- **Social media handling**: Emojis, emoticons, slang
- **Intensity modifiers**: Capitalization, punctuation, degree adverbs
- **Negation handling**: Tri-gram context window

### 5.3 Compound Score Interpretation

| Score Range | Label |
|-------------|-------|
| ≥ +0.05 | Positive |
| ≤ -0.05 | Negative |
| -0.05 to +0.05 | Neutral |

### 5.4 Results

| Metric | Value |
|--------|-------|
| Mean compound | 0.076 (SD = 0.625) |
| Positive tweets | 640 (51.7%) |
| Negative tweets | 502 (40.5%) |
| Neutral tweets | 97 (7.8%) |

### 5.5 Statistical Validation

**Pearson Correlations**:
- PMI sum × Epistemic density: r = 0.01, p = .684 (ns)
- PMI sum × Sentiment: r = -0.07, p = .016*
- Epistemic density × Sentiment: r = -0.03, p = .259 (ns)

**One-Way ANOVA (Chapter Variation)**:
- PMI: F(14, 1224) = 2.46, p = .002*, η² = .03
- Sentiment: F(14, 1224) = 3.89, p < .001***, η² = .04

---

## 6. Exemplar Selection (Script 05)

### 6.1 Theoretical Framework

**Citation**: Biber, D. (1988). *Variation across speech and writing*. Cambridge University Press.

**Citation**: Egbert, J., & Biber, D. (2019). Incorporating text dispersion into keyword analyses. *Corpora, 14*(2), 131-170.

### 6.2 Composite Scoring Formula

```
Selection Score = (PMI_norm × 3.0) + (Epistemic_norm × 3.0) + (Sentiment_norm × 2.0)
```

Where:
- PMI_norm = min(pmi_sum, 15.0) / 15.0
- Epistemic_norm = min(epistemic_density, 20.0) / 20.0
- Sentiment_norm = abs(sentiment_compound)

**Maximum possible score**: 8.0

### 6.3 Selection Criteria

- Top 10 per chapter (balanced geographic representation)
- Total: 150 exemplars (10 × 15 chapters)
- Selection based on composite score ranking

### 6.4 Results

| Metric | Value |
|--------|-------|
| Total exemplars | 150 |
| Mean score | 4.150 |
| Score range | 2.393 - 5.537 |
| Chapters represented | 15 (all) |

---

## 7. Qualitative Coding (Script 06)

### 7.1 Theoretical Framework

**Citation**: Gill, P., & Lennon, R. (2022). A multimodal fear appeals analysis framework for vaccine misinformation. *Journal of Medical Internet Research, 24*(6), e36255.

### 7.2 Coding Categories

| Category | Definition | Analytical Focus |
|----------|------------|------------------|
| Composition | Visual arrangement and design | Salience, framing, layout |
| Color | Affective impact of palette | Emotional connotations |
| Represented Participants | Who/what is depicted | Actors, objects, roles |
| Perspective/Angles | Camera position | Power relations, viewer positioning |
| Textual Components | Embedded text | Typography, integration |
| Fear Appeal Integration | Overall strategy | How elements construct threat |

### 7.3 Template Structure

- 15 Excel sheets (one per chapter)
- 10 rows per sheet (selected exemplars)
- 7 columns (ID + 6 coding categories)
- APA 7th compliant formatting

---

## 8. Reproducibility Notes

### 8.1 Random Seeds

- Network visualization: seed=42
- All other analyses: deterministic

### 8.2 Software Versions

- Python: 3.9+
- pandas: 2.0.0+
- VADER: 3.3.2+
- Tesseract: 5.0+

### 8.3 System Requirements

- Tesseract OCR must be installed separately
- macOS: `brew install tesseract`
- Linux: `apt install tesseract-ocr`
- Windows: Download from GitHub releases

---

## 9. Limitations

1. **Temporal scope**: Spring 2025 snapshot; discourse may evolve
2. **Platform effects**: Twitter/X algorithm changes may affect visibility
3. **OCR accuracy**: Some image text may be imperfectly extracted
4. **Sentiment calibration**: VADER trained on general social media, not health misinformation specifically
5. **Cross-chapter coordination**: Cannot definitively establish central coordination

---

## 10. Ethical Considerations

- Publicly available data analyzed for academic research
- Organizational-level analysis, not individual user profiling
- No medical claims made; discourse analysis only
- Results contextualized within platform terms of service

---

*Document version: 1.0 | Last updated: January 2026*
