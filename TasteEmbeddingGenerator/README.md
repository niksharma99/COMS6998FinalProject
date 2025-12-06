# 🎬 TasteEmbeddingGenerator
## Unified Movie & User Taste Embedding Pipeline for Conversational Recommendation Systems

This module builds movie embeddings and user taste embeddings from heterogeneous datasets — integrating ratings, metadata, and conversational text.
It powers the LLM-Driven Conversational Movie Recommendation & Taste Graph Service.

---

## 📦 Directory Structure
```
TasteEmbeddingGenerator/
│
├── artifacts/                     # Saved movie/user embeddings (.parquet)
│
├── embeddings_backend.py          # Base + Backend implementations (ST / OpenAI)
├── Generator.py                   # High-level orchestration pipeline
├── MovieEmbedding.py              # Movie embedding builder
├── UserEmbedding.py               # User embedding builder (ratings + text)
├── test_generator.py              # Minimal sanity-check test
└── README.md

```

---

## ✨ Overview
TasteEmbeddingGenerator produces two core embedding spaces:

### 1. Movie Embeddings
Built from:
- MovieLens (TMDB enriched)
- MovieTweetings (TMDB enriched)
- INSPIRED Movie Database (TMDB enriched)

Each movie is normalized into a unified schema and encoded using a natural-language description:
```
Title: Inception (2010).
Genres: Action, Sci-Fi.
Cast: Leonardo DiCaprio, Joseph Gordon-Levitt.
Plot: A thief enters dreams to extract information...
Keywords: dream, subconscious, thriller.
```

### 2. User Taste Embeddings
A hybrid integration of:
#### ✔ Rating-based preference vector
Derived from MovieLens ratings:
```python
liked_movies = ratings[rating >= 4.0]
user_movie_vec = mean(embedding[movie_id])
```

#### ✔ Dialogue-based text preference vector
Aggregate user utterances from:
| Dataset               | Source File                    |
| --------------------- | ------------------------------ |
| CCPE Dialogues        | `ccpe_dialogues.csv`           |
| ReDial                | `redial_dialogues.csv`         |
| INSPIRED Dialogs      | `inspired_dialogs.csv`         |
| GoEmotions (optional) | `goemotions_text_emotions.csv` |

Text Embedding:
```python
user_text_vec = mean(embed(utterances))
```

#### ✔ Final taste vector (weighted fusion)
```python
user_final = α * user_movie_vec + (1 - α) * user_text_vec
```

---

## 🧠 Embedding Backend (Pluggable)
All encoders follow:
```
BaseEmbeddingBackend
```
### Available backends
| Backend                      | Status          | Notes                           |
| ---------------------------- | --------------- | ------------------------------- |
| `SentenceTransformerBackend` | ✅ Default (v1)  | Uses BAAI/bge-base-en-v1.5      |
| `OpenAIEmbeddingBackend`     | 🚧 Planned (v2) | Will use text-embedding-3-large |

Choose backend via config:
```python
cfg = TasteEmbeddingConfig(
    backend_type="sentence-transformers",  # or "openai"
    model_name="BAAI/bge-base-en-v1.5"
)
```

---

## 📚 Data Sources (Processed)
All located in:
```bash
Dataset/processed/
```
### Movie Metadata
| Dataset           | File                             | Rows  |
| ----------------- | -------------------------------- | ----- |
| MovieLens         | movielens_movies_tmdb.csv        | ~3.8K |
| MovieTweetings    | movietweetings_movies_tmdb.csv   | ~38K  |
| INSPIRED Movie DB | inspired_movie_database_tmdb.csv | ~17K  |

### Ratings
| Dataset                | File                       |
| ---------------------- | -------------------------- |
| MovieLens Ratings      | movielens_ratings.csv      |
| MovieTweetings Ratings | movietweetings_ratings.csv |

### User Dialogue Text
| Dataset    | File                         |
| ---------- | ---------------------------- |
| CCPE       | ccpe_dialogues.csv           |
| ReDial     | redial_dialogues.csv         |
| INSPIRED   | inspired_dialogs.csv         |
| GoEmotions | goemotions_text_emotions.csv |

---

## 🚀 Usage
### Run Full Pipeline
```bash
python -m TasteEmbeddingGenerator.Generator
```

### 🧪 Testing
A small-scale sanity test is available:
```bash
python -m TasteEmbeddingGenerator.test_generator
```
It verifies:
  - Movie embedding encoding
  - User embedding generation
  - Output dimensions
  - No NaNs

---

## 🛠 Implementation Details

### `MovieEmbedding.py`

We construct a unified movie embedding table across three sources
(**MovieLens**, **MovieTweetings**, **INSPIRED**) in the following steps:

1. **Load TMDB-enriched tables**
   - `movielens_movies_tmdb.csv`
   - `movietweetings_movies_tmdb.csv`
   - `inspired_movie_database_tmdb.csv`
   Each file is tagged with a `source` column.

2. **Normalize schema & IDs**
   - Ensure a common key: `movie_id`
     - MovieLens: `movieId → movie_id`
     - MovieTweetings: already `movie_id`
     - INSPIRED: `movieId` or `id` → `movie_id`
   - Keep / standardize the following columns (if available):
     - `title`, `year`, `genres`
     - `tmdb_title`, `tmdb_release_date`, `tmdb_overview`
     - `tmdb_runtime`, `tmdb_genres`, `tmdb_top_cast`, `tmdb_keywords`

3. **Build natural-language description per movie**
   For each row we synthesize a text field `embedding_text`, e.g.:

   > `Title: The Matrix (1999). Genres: Action, Sci-Fi. Plot: ... Cast: Keanu Reeves, Laurence Fishburne. Keywords: cyberpunk, dystopia.`

   This is assembled by:
   - Using TMDB title/year if present, otherwise MovieLens title/year
   - Concatenating genres, overview, cast, and keywords into a single string

4. **Batch encoding with the backend**
   - Collect all `embedding_text` into a list
   - Split into batches of size `batch_size`
   - Call `backend.embed_texts(batch)` where the backend is one of:
     - `SentenceTransformerBackend` (v1 default; `BAAI/bge-base-en-v1.5`)
     - `OpenAIEmbeddingBackend` (planned; `text-embedding-3-large`)
   - Store the resulting vectors in a new `embedding` column (list of floats)

5. **Save movie embeddings**
   - Final table columns (per movie):
     - `movie_id`, `source`, metadata fields, `embedding_text`, `embedding`
   - Written to:
     - `TasteEmbeddingGenerator/artifacts/movie_embeddings.parquet`


### `UserEmbedding.py`

User embeddings combine **implicit taste from ratings** and **explicit taste from dialogue text**.

1. **Load movie embeddings**
   - Read `movie_embeddings.parquet`
   - Optionally filter by `source` (e.g., `"movielens"`) for consistency with ratings
   - Build a mapping `movie_id → embedding` as NumPy vectors

2. **Rating-based user vectors (MovieLens)**
   - Load `movielens_ratings.csv`
   - Filter to “liked” movies: `rating >= rating_threshold` (default 4.0)
   - Group by `userId`
   - For each user:
     - Collect all `movieId` with sufficient ratings
     - Look up their movie embeddings
     - If the user has at least `min_movies` liked movies:
       - Compute the mean vector:
         \[
         \mathbf{u}_\text{rating} = \frac{1}{N} \sum_{i=1}^{N} \mathbf{m}_i
         \]
       - Store as `embedding_rating` and `num_movies = N`

3. **Dialogue-based text profiles**
   We aggregate user utterances from three conversational datasets:

   - **CCPE** (`ccpe_dialogues.csv`)
     - Group by `dialog_id`
     - Concatenate all `text` into one string
     - Assign synthetic ID: `user_id = "ccpe:<dialog_id>"`

   - **INSPIRED** (`inspired_dialogs.csv`)
     - Group by `(dialog_id, speaker)`
     - Concatenate all `text`
     - ID: `user_id = "inspired:<dialog_id>:<speaker>"`

   - **ReDial** (`redial_dialogues.csv`)
     - Group by `speaker_id`
     - Concatenate all `text`
     - ID: `user_id = "redial:<speaker_id>"`

   Each aggregated string becomes a **text profile**. All profiles are encoded
   via the same embedding backend (`backend.embed_texts`) into
   `embedding_text` vectors.

4. **Fusion: rating + text**
   We outer-join rating-based users and text-based profiles on `user_id`
   (note: IDs live in different namespaces such as integer MovieLens IDs vs
   `"ccpe:..."` / `"redial:..."`), then compute a final vector:

   - If both `embedding_rating` and `embedding_text` exist and have the same
     dimension:
     \[
     \mathbf{u}_\text{final}
       = \alpha \, \mathbf{u}_\text{rating}
       + (1 - \alpha) \, \mathbf{u}_\text{text}
     \]
     with default `α = 0.7` (rating-biased).
   - If only one exists, we use that vector as `embedding`.
   - Users with neither vector are dropped.

5. **Save user embeddings**
   Final output columns:

   - `user_id`
   - `embedding`          (final fused vector)
   - `embedding_rating`   (may be null for dialogue-only users)
   - `embedding_text`     (may be null for rating-only users)
   - `num_movies`         (MovieLens liked-movie count; 0 for dialogue-only)

   Written to:

   - `TasteEmbeddingGenerator/artifacts/user_embeddings.parquet`

---

## 📌 Current Version (v1)
| Component       | Implementation                            |
| --------------- | ----------------------------------------- |
| Movie Embedding | SentenceTransformers (BGE-base v1.5)      |
| User Embedding  | Rating-based + Dialogue-based             |
| Backend         | SentenceTransformers only                 |
| Output Format   | Parquet (embedding stored as list<float>) |

### 📦 Taste Embedding Artifacts (Stored Externally)
The embedding files are not stored in this repository due to GitHub's 100MB file size limit.
All generated artifacts (movie/user embeddings, FAISS indexes, parquet files) are stored in Google Drive:

#### 🔗 Download Artifacts
https://drive.google.com/drive/folders/1ci0GZueB6-zbxbYb0hCWOCCom9Odj3En?usp=sharing
- movie_embeddings.parquet
https://drive.google.com/file/d/1ld84nIDTzt_1DGxngMBn7n8Yp6mHP4tk/view?usp=sharing
- user_embeddings.parquet
https://drive.google.com/file/d/1qOhnyLKPCYxeueeMgxy__GS9SatdTg6I/view?usp=sharing

You can download them manually or run the script below:
```bash
bash ./TasteEmbeddingGenerator/src/download_artifacts.sh
```

### 🚧 Future Work (v2)
- 🔄 Add OpenAI Embeddings as a second backend
- 😭 Emotion-aware user vectors using GoEmotions
- 🔍 Movie similarity graph (genre / actor / keyword networks)
- 🧩 Taste clustering & persona prototypes
- 🧨 Multimodal embeddings (poster, trailer text)