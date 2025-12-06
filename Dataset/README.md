# Dataset Processing Pipeline for the LLM-Based Conversational Movie Recommender
This directory contains all scripts used to download, clean, normalize, and enrich all datasets used in our project:
- Movie-level datasets → For movie embeddings
- Dialogue & user preference datasets → For user embeddings
- Metadata enrichment → via TMDB API

All processed outputs are consumed by the downstream module:
```
TasteEmbeddingGenerator/
```

---

## 📊 Data Sources Overview
### 🎬 Movie Embedding Datasets
| Dataset               | Description                                                    | Status                      |
| --------------------- | -------------------------------------------------------------- | --------------------------- |
| **MovieLens 1M**      | ~1M user–movie ratings + ~3.9K movies                          | ✔ Processed                 |
| **TMDB API**          | Enriches movies with overview, genres, cast, keywords, runtime | ✔ Integrated                |
| **MovieTweetings**    | 39K+ movies + real Twitter-based ratings                       | ✔ Processed + TMDB enriched |
| **INSPIRED Movie DB** | Movie metadata referenced in INSPIRED dialogues                | ✔ Processed + TMDB enriched |
| **Netflix Prize**     | 100M ratings dataset                                           | ➤ *Planned (Future Work)*   |

### 🗣 User Embedding Datasets
| Dataset        | Description                                                  | Status                   |
| -------------- | ------------------------------------------------------------ | ------------------------ |
| **ReDial**     | Movie recommendation dialogues with explicit user mentions   | ✔ Downloaded + Processed |
| **CCPE**       | Customer-care dialogues with explicit preference annotations | ✔ Processed              |
| **GoEmotions** | 58K utterances annotated with 27 emotions                    | ✔ Processed              |

These datasets enable robust user taste modeling from natural language + ratings.

---

## 📁 Directory Structure
```
COMS6998FinalProject/
│
├── Dataset/
│   │
│   ├── raw/                       
│   │   # Raw downloaded datasets:
│   │   # MovieLens, TMDB metadata cache, ReDial, CCPE, GoEmotions,
│   │   # MovieTweetings, INSPIRED
│   │
│   ├── processed/                 
│   │   # Final cleaned & enriched datasets
│   │
│   │   ├── movielens_movies.csv
│   │   ├── movielens_ratings.csv
│   │   ├── movielens_movies_tmdb.csv
│   │
│   │   ├── movietweetings_movies.csv
│   │   ├── movietweetings_ratings.csv
│   │   ├── movietweetings_users.csv
│   │   ├── movietweetings_movies_tmdb.csv
│   │
│   │   ├── inspired_dialogs.csv
│   │   ├── inspired_movie_database.csv
│   │   ├── inspired_movie_database_tmdb.csv
│   │
│   │   ├── redial_dialogues.csv
│   │   ├── ccpe_dialogues.csv
│   │   ├── goemotions_text_emotions.csv
│   │
│   ├── download_movielens.py
│   ├── preprocess_movielens.py
│   ├── tmdb_client.py
│   ├── tmdb_enrich_movielens.py
│   │
│   ├── download_movietweetings.py
│   ├── preprocess_movietweetings.py
│   ├── tmdb_enrich_movietweetings.py
│   │
│   ├── preprocess_inspired.py
│   ├── tmdb_enrich_inspired_movies.py
│   │
│   ├── download_redial.py
│   ├── preprocess_redial.py
│   │
│   ├── download_ccpe.py
│   ├── preprocess_ccpe.py
│   │
│   ├── download_goemotions.py
│   ├── preprocess_goemotions.py
│   │
│   ├── summarize_dataset.py       # Automatically counts final dataset sizes
│   │
│   └── README.md
```

---

## 🔧 Processing Philosophy
### ✔ This directory does:
- Download raw datasets
- Clean, normalize, and extract structured metadata
- Perform TMDB enrichment for richer movie metadata
- Standardize dialogue datasets into unified formats
- Produce consistent and reusable inputs for embedding modules

### ✖ This directory does NOT:
- Build movie-level text embeddings
- Generate any vector embeddings
- Train or run prediction models

Embedding generation occurs later in:
```
TasteEmbeddingGenerator/
```

---

## 📦 Outputs Used by Embedding Modules
### MovieEmbedding module uses:
- ```movielens_movies_tmdb.csv```
- ```movietweetings_movies_tmdb.csv```
- ```inspired_movie_database_tmdb.csv```

These contain enriched movie metadata, including:
- Overview
- Genres
- Keyword tags
- Cast members
- Runtime
- TMDB-standardized titles

### UserEmbedding module uses:
- ```movielens_ratings.csv```
- ```redial_dialogues.csv```
- ```ccpe_dialogues.csv```
- ```goemotions_labeled_text.csv``` (optional for emotion modeling)

---

## 🔐 API Keys
TMDB API key is stored in a project-level ```.env``` file:
```bash
TMDB_API_KEY=your_api_key_here
```
Make sure ```.env``` is added to .gitignore for safety.

---

## 📈 Dataset Summary (Final Counts — Fill After Preprocessing)

| Dataset | Category | Count | File |
|--------|----------|-------|------|
| MovieLens Movies (TMDB enriched) | movie | 3,883 | `movielens_movies_tmdb.csv` |
| MovieTweetings Movies (TMDB enriched) | movie | 38,018 | `movietweetings_movies_tmdb.csv` |
| INSPIRED Movie Database (TMDB enriched) | movie | 17,869 | `inspired_movie_database_tmdb.csv` |
| MovieLens Ratings | rating | 1,000,209 | `movielens_ratings.csv` |
| MovieTweetings Ratings | rating | 921,398 | `movietweetings_ratings.csv` |
| ReDial Dialogues | dialogue | 206,102 | `redial_dialogues.csv` |
| CCPE Dialogues | dialogue | 11,971 | `ccpe_dialogues.csv` |
| GoEmotions Texts | text | 211,225 | `goemotions_text_emotions.csv` |

### 👉 Total processed items across all datasets:  `2,410,675`

---

## 🚀 Future Work: Netflix Prize Dataset Integration

The Netflix Prize dataset (100M ratings, 480K users, 17K movies) is planned for potential future extension:
- Efficient sampling for large-scale training
- Mapping Netflix movie IDs to TMDB IDs
- Merging with MovieLens + MovieTweetings interactions
- Performance-aware training on large foundation models