
# 🎬 LLM-Augmented Movie Recommender Backend

This backend exposes a **taste-embedding–driven movie recommender** with:

- Precomputed **movie embeddings** + **user taste embeddings** (from `TasteEmbeddingGenerator`)
- A **runtime taste vector** built from user input (free text or “top 4 movies” style)
- **Semantic nearest-neighbor search** over movies
- Optional **LLM explanations** of why each movie was recommended
- Lightweight **conversational memory** via a persistent taste vector per `user_id`

The main way to interact right now is via an **interactive CLI**: `test_cli.py`.

---

## 🗂 Project Layout

Assuming the following directory structure:

```bash
COMS6998FinalProject/
│
├── TasteEmbeddingGenerator/        # Your existing embedding pipeline
│   ├── Generator.py
│   ├── MovieEmbedding.py
│   ├── UserEmbedding.py
│   ├── embeddings_backend.py
│   └── artifacts/
│       ├── movie_embeddings.parquet
│       └── user_embeddings.parquet
│
└── RecommenderBackend/
    ├── recommender.py              # Main recommendation logic
    ├── embedding_loader.py         # Loads parquet + builds in-memory arrays
    ├── test_cli.py                 # Interactive terminal demo
    └── README.md                   # (this file)
````

> ✅ `TasteEmbeddingGenerator` and `RecommenderBackend` live **side by side** in the same parent directory.

---

## ⚙️ Requirements

* Python **3.9+**
* A working conda environment (recommended)
* macOS with **MPS** or CPU is fine (you’re using `BAAI/bge-base-en-v1.5` via `sentence-transformers`)
* An OpenAI API key (for explanation / chat)

### Core Python dependencies

You can create a `requirements.txt` like:

```txt
torch>=2.0
sentence-transformers>=2.2.2
pandas>=2.0
pyarrow>=14.0
tqdm
datasets
openai>=1.0.0
python-dotenv
```

---

## 🧪 Setup & Installation

### 1. Create and activate a conda environment

```bash
conda create -n movie-rec python=3.9 -y
conda activate movie-rec
```

### 2. Install Python dependencies

From the `COMS6998FinalProject` root (or from `RecommenderBackend`, doesn’t really matter as long as you point pip to the right file):

```bash
pip install -r RecommenderBackend/requirements.txt
```

(or install the listed packages manually if you don’t keep a `requirements.txt`.)

### 3. Download embedding artifacts

You should already have this from `TasteEmbeddingGenerator`, but for completeness:

* `TasteEmbeddingGenerator/artifacts/movie_embeddings.parquet`
* `TasteEmbeddingGenerator/artifacts/user_embeddings.parquet`

Place them under:

```bash
TasteEmbeddingGenerator/artifacts/
    movie_embeddings.parquet
    user_embeddings.parquet
```

If you have a script like `download_artifacts.sh`, you can run it from inside `TasteEmbeddingGenerator`:

```bash
cd TasteEmbeddingGenerator
bash src/download_artifacts.sh
cd ..
```

### 4. Set your OpenAI API key

The recommender uses OpenAI **only to format / explain the recommendations** (1 chat call per query).

You can set:

```bash
export OPENAI_API_KEY="sk-..."
```

Or use a `.env` file in `RecommenderBackend/`:

```env
OPENAI_API_KEY=sk-...
```

(If you use `.env`, make sure `recommender.py` loads it via `dotenv` or similar.)

---

## ▶️ Running the CLI Demo

From the `RecommenderBackend` directory:

```bash
cd RecommenderBackend
python test_cli.py
```

You should see:

```text
=== MOVIE RECOMMENDER TEST CLI ===
Type 'exit' to quit.
```

Then you can interact:

```text
User Preference: My top 4 movies: Inception, Arrival, Ex Machina, Blade Runner 2049
User ID (press Enter for session-based memory): 
[Session user id created: aa4fc494-fa08-4822-a065-72ccebb7aea3]

--- Recommendation ---
Based on your top four movies—Inception, Arrival, Ex Machina, and Blade Runner 2049...
(5 recommendations with explanations)
-----------------------
```

For a follow-up turn in the **same conversation**, just press Enter again at the `User ID` prompt:

```text
User Preference: Also I like slow, atmospheric pacing and minimal action
User ID (press Enter for session-based memory): 
# (Same session user id is reused internally)

--- Recommendation ---
(Refined recommendations reflecting BOTH sci-fi + slow/atmospheric preferences)
-----------------------
```

Type `exit` at the preference prompt to quit.

---

## 🧠 System Pipeline (What Actually Happens)

Each call to `recommend(user_input, user_id)` goes roughly like this:

1. **User input arrives**

   * Example:

     * `"I'm interested in romance!"`
     * or `"My top 4 movies: Inception, Arrival, Ex Machina, Blade Runner 2049"`

   * In your current setup:

     ```python
     taste_profile = user_input
     ```

2. **Text → Taste Embedding (local)**

   * The taste profile string is passed to the `SentenceTransformerBackend` from `TasteEmbeddingGenerator`:

     ```python
     vec = backend.embed_texts([taste_profile])[0]
     ```
   * Backend uses:

     * Model: `BAAI/bge-base-en-v1.5`
     * Device: `mps` (on Mac)
   * This produces a **normalized vector** in the *same embedding space* as your movie embeddings.

3. **Conversational memory update (per `user_id`)**

   * The system tracks a runtime user taste vector in something like `USER_STATE[user_id]`.

   * On the **first** message for that `user_id`, `taste_vec` = current embedding.

   * On subsequent messages, it blends the old taste and new message embedding:
     [
     u_{\text{fused}} = \alpha , u_{\text{old}} + (1-\alpha),u_{\text{current}}
     ]
     (for some `α` like 0.7–0.9).

   * This gives you **session-based conversational memory** in vector form.

   > 🔑 If the user presses Enter at the `User ID` prompt, a UUID (session id) is created and reused for the rest of that CLI session.

4. **Nearest-Neighbor Search over Movie Embeddings**

   * `embedding_loader.py` loads:

     * `movie_embeddings.parquet`
   * The recommender computes **cosine similarity** between the user taste vector and each movie vector.
   * It selects the **top-K** movies (e.g. 5) and returns:

     * metadata: title, year, genres, overview
     * similarity scores (if needed internally)

5. **LLM Explanation of Recommendations (OpenAI GPT)**

   * This is the **only GPT call per recommendation** in your current configuration.

   * It takes:

     * the user’s taste text
     * the top-K candidate movie metadata

   * And returns a **verbose explanation** like:

     > “Based on your top four movies—Inception, Arrival, Ex Machina, and Blade Runner 2049—here are five candidate films…”

   * This is purely a **presentation layer**:

     * It does **not** change the taste vector.
     * It does **not** control retrieval.
     * It only turns raw results into nice human-readable justification.

6. **Printed Output in CLI**

   * The formatted explanation text from GPT is printed to the console, wrapped between:

     ```text
     --- Recommendation ---
     ...
     -----------------------
     ```

---

## 💾 Memory Model

Memory is **per `user_id`**, not per raw text:

* The CLI offers:

  * Enter a custom `User ID` manually (e.g. `"emily"`)
  * Or press Enter for **session-based memory**:

    * On first turn: a new UUID is created and shown.
    * On later turns: pressing Enter again reuses that UUID.

Each time you call `recommend(user_input, user_id)`:

* The stored taste vector for that `user_id` is updated.
* Future recommendations for that `user_id` consider **all previous turns**, via the fused embedding.

There is **no GPT-based memory** and no chat history is sent to OpenAI.
All memory is local and numeric (embedding vectors).

---

## 🎛 Example Interaction Patterns

### 1. Pure free-text preferences

```text
User Preference: I like dark sci-fi with AI and moral dilemmas
User ID: emily
```

→ Builds a vector from that sentence, runs retrieval, explains results.

### 2. “Top 4 movies” seeding

```text
User Preference: My top 4 movies: Inception, Arrival, Ex Machina, Blade Runner 2049
User ID:  (press Enter for session id)
```

→ Embeds the whole string; the model strongly activates on those titles and associated themes.

### 3. Multi-turn refinement (same session)

```text
User Preference: I'm interested in romance!
User ID:  (Enter → creates session id)

User Preference: I'm also interested in high school settings.
User ID:  (Enter → reuses that session id)
```

→ Second turn updates the existing taste vector to emphasize **romance + high school**.

---

## 🔧 Customization Ideas

* **Turn off GPT explanations** (for offline testing or zero OpenAI cost):

  * Have `recommend()` return raw titles and metadata, and skip the OpenAI call.
* **Add explicit “top-N favorites” parsing**:

  * Detect phrases like `My top 4 movies: ...`
  * Extract titles, look them up in `movie_embeddings.parquet`
  * Average those embeddings for an even sharper taste vector.
* **Switch to OpenAI embeddings in v2**:

  * Use `OpenAIEmbeddingBackend` in `TasteEmbeddingGenerator` instead of SentenceTransformers for a unified OpenAI stack.

---

## ❓ FAQ

**Q: How many GPT calls per recommendation right now?**
**A:** Exactly **one** — to format and explain the results.

**Q: Is GPT used to compute the taste vector?**
**A:** No. Taste vectors are computed locally using `BAAI/bge-base-en-v1.5`.

**Q: Does the system remember my previous turns?**
**A:** Yes, as long as you reuse the same `user_id` (or keep pressing Enter in the same CLI session). Memory is stored as a fused taste vector per `user_id`.

**Q: Can I use only “top 4 movies” instead of a description?**
**A:** Yes. The current system embeds that text directly and it already works well. In a future refinement you can explicitly parse those titles and average their embeddings.

```
