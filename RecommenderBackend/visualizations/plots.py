# visualizations/plots.py
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import textwrap
from matplotlib.patches import Patch

from .genres import primary_genre_from_meta, build_genre_color_map
from .utils import pca_2d


# ---------------- 1) Global embedding map -----------------


def plot_embedding_map(
    user_id: str,
    msg_index: int,
    movies_2d: np.ndarray,
    user_2d: np.ndarray,
    rec_indices: np.ndarray,
    rec_2d: np.ndarray,
    movie_metadata: List[dict],
    out_path: Path,
) -> None:
    """
    Simple global map:
      - all movies as faint points
      - user taste vector as star
      - top-k recommendations as highlighted points with labels
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    # all movies (light)
    ax.scatter(
        movies_2d[:, 0],
        movies_2d[:, 1],
        s=4,
        alpha=0.75,
        color="gray",
        label="Movies (all)",
    )

    # user
    ax.scatter(
        user_2d[0],
        user_2d[1],
        s=140,
        marker="*",
        edgecolor="black",
        linewidth=1.0,
        facecolor="orange",
        label=f"User '{user_id}' taste (msg {msg_index})",
    )

    # recs
    ax.scatter(
        rec_2d[:, 0],
        rec_2d[:, 1],
        s=70,
        marker="o",
        edgecolor="black",
        linewidth=1.0,
        facecolor="limegreen",
        label=f"Top {len(rec_indices)} recommendations",
    )

    # lines + short titles
    for i, movie_idx in enumerate(rec_indices):
        x, y = rec_2d[i]
        meta = movie_metadata[movie_idx]
        title = meta.get("title") or meta.get("tmdb_title") or f"movie_{movie_idx}"
        short_title = textwrap.shorten(title, width=25, placeholder="…")

        ax.plot(
            [user_2d[0], x],
            [user_2d[1], y],
            linestyle="--",
            linewidth=0.8,
            alpha=0.6,
        )
        ax.text(
            x + 0.01,
            y,
            short_title,
            fontsize=7,
            alpha=0.85,
        )

    ax.set_title(f"User vs Movie Embedding Space (user='{user_id}', msg={msg_index})")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


# ---------------- 2) Local neighborhood w/ genres ---------


def plot_local_neighborhood_with_genres(
    user_id: str,
    msg_idx: int,
    user_vec: np.ndarray,
    rec_indices: List[int],
    movie_embeddings: np.ndarray,
    movie_metadata: List[dict],
    out_path: Path,
    n_local: int = 800,
    movie_cluster_genre: List[str] | None = None,
) -> None:
    """
    Local map around the user:

      - pick the n_local movies closest to the user in embedding space
      - PCA on {these movies + user + recs}
      - color movies by *primary genre* (using tmdb_genres/genres)
      - overlay user (star) and recs (green points with labels)
    """
    user_vec = np.asarray(user_vec, dtype=np.float32)

    # cosine similarity to find local neighborhood
    movie_norms = np.linalg.norm(movie_embeddings, axis=1) + 1e-8
    user_norm = np.linalg.norm(user_vec) + 1e-8
    sims = (movie_embeddings @ user_vec) / (movie_norms * user_norm)

    # largest sims = nearest neighbors
    n_local = min(n_local, movie_embeddings.shape[0])
    local_ids = np.argpartition(-sims, n_local - 1)[:n_local]

    # ensure recs are included in neighborhood
    rec_indices = np.asarray(rec_indices, dtype=int)
    local_ids = np.unique(np.concatenate([local_ids, rec_indices]))

    local_embs = movie_embeddings[local_ids]

    # PCA on {local movies + user + recs}
    X = np.vstack([local_embs, user_vec[None, :], movie_embeddings[rec_indices]])
    X2 = pca_2d(X)

    L = local_embs.shape[0]
    local_2d = X2[:L]
    user_2d = X2[L]
    rec_2d = X2[L + 1 :]

    # build colors by primary genre for local movies
    # local_genres = [primary_genre_from_meta(movie_metadata[i]) for i in local_ids]
    # local_genres = [g for g in local_genres if g is not None]
    # color_map = build_genre_color_map(local_genres)
    # local_colors = [color_map[g] for g in local_genres]
    # build colors by primary genre for local movies
    # local_genres = []
    # for i in local_ids:
    #     g = primary_genre_from_meta(movie_metadata[i])
    #     if not g:
    #         g = "Unknown"
    #     local_genres.append(g)

    # # include Unknown in the colormap so those points still get a color
    # color_map = build_genre_color_map(local_genres)
    # local_colors = [color_map[g] for g in local_genres]

        # build genres for local movies (allow "Unknown")
    # local_genres = [
    #     primary_genre_from_meta(movie_metadata[i]) or "Unknown"
    #     for i in local_ids
    # ]

    # # make a colormap only for known genres; Unknown gets a neutral gray
    # known_genres = [g for g in local_genres if g != "Unknown"]
    # color_map = build_genre_color_map(known_genres)

    # UNKNOWN_COLOR = "#dddddd"  # light gray
    # local_colors = [
    #     color_map[g] if g != "Unknown" else UNKNOWN_COLOR
    #     for g in local_genres
    # ]

    # compute genres
    if movie_cluster_genre is not None:
        # use precomputed cluster-majority genre per movie
        local_genres_all = [movie_cluster_genre[i] for i in local_ids]
    else:
        # fall back to primary genre from metadata
        local_genres_all = [
            primary_genre_from_meta(movie_metadata[i]) or "Unknown"
            for i in local_ids
        ]
    # local_genres_all = [
    #     primary_genre_from_meta(movie_metadata[i]) or "Unknown"
    #     for i in local_ids
    # ]

    # mask out Unknown completely
    mask_known = np.array([g != "Unknown" for g in local_genres_all])

    local_2d = local_2d[mask_known]
    local_genres = list(np.array(local_genres_all)[mask_known])

    # build bright colors only for known genres
    color_map = build_genre_color_map(local_genres)
    local_colors = [color_map[g] for g in local_genres]



    # plot
    fig, ax = plt.subplots(figsize=(10, 7))

    ax.scatter(
        local_2d[:, 0],
        local_2d[:, 1],
        s=12,
        c=local_colors,
        alpha=0.85,
        linewidths=0,
    )

    # user
    ax.scatter(
        user_2d[0],
        user_2d[1],
        marker="*",
        s=220,
        edgecolor="black",
        facecolor="orange",
        linewidths=1.0,
        label=f"user '{user_id}'",
        zorder=3,
    )

    # recs
    ax.scatter(
        rec_2d[:, 0],
        rec_2d[:, 1],
        s=90,
        edgecolor="black",
        facecolor="limegreen",
        linewidths=1.0,
        label="top recommendations",
        zorder=4,
    )

    # labels for recs
    for idx, (x, y) in zip(rec_indices, rec_2d):
        title = movie_metadata[idx].get("title") or movie_metadata[idx].get(
            "tmdb_title"
        ) or f"movie_{idx}"
        short = textwrap.shorten(title, width=25, placeholder="…")
        ax.text(
            x + 0.01,
            y + 0.01,
            short,
            fontsize=7,
            ha="left",
            va="bottom",
        )

    # # genre legend (local)
    # legend_handles: List[Patch] = []
    # for g in sorted(set(local_genres)):
    #     legend_handles.append(
    #         Patch(facecolor=color_map[g], edgecolor="black", label=g)
    #     )
    # genre legend (local) – hide "Unknown"
    legend_handles: List[Patch] = []
    for g in sorted(set(local_genres)):
        if g == "Unknown":
            continue
        legend_handles.append(
            Patch(facecolor=color_map[g], edgecolor="black", label=g)
        )
    genre_legend = ax.legend(
        handles=legend_handles,
        title="Genres (local neighborhood)",
        loc="upper left",
        fontsize=8,
    )
    ax.add_artist(genre_legend)

    ax.legend(loc="lower right", fontsize=8)
    ax.set_title(f"Local taste map (user='{user_id}', msg={msg_idx})")
    ax.set_xlabel("PC1 (local)")
    ax.set_ylabel("PC2 (local)")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


# ---------------- 3) Genre histogram ----------------------
from collections import Counter
import matplotlib.pyplot as plt

def _parse_all_genres(meta: dict) -> list[str]:
    """
    Return ALL genre tags for a movie, combining tmdb_genres and genres.
    - tmdb_genres: 'Family, Comedy, Animation, Adventure'
    - genres:      'Animation|Children\'s|Comedy'
    We normalize separators and strip spaces, but we do NOT collapse to
    a single 'primary' genre here.
    """
    tags: list[str] = []

    # 1) TMDB-style (comma separated)
    raw_tmdb = meta.get("tmdb_genres") or ""
    if isinstance(raw_tmdb, str) and raw_tmdb.strip():
        for g in raw_tmdb.split(","):
            g = g.strip()
            if g:
                tags.append(g)

    # 2) MovieLens-style (pipe separated)
    raw_ml = meta.get("genres") or ""
    if isinstance(raw_ml, str) and raw_ml.strip():
        for g in raw_ml.split("|"):
            g = g.strip()
            if not g:
                continue
            # tiny normalization: map some ML labels into broader bins
            if g == "Children's":
                g = "Family"
            tags.append(g)

    return tags


def plot_genre_histogram(
    rec_indices: np.ndarray,
    movie_metadata: list[dict],
    out_path: Path,
) -> None:
    """
    Multi-label genre histogram for the TOP-K RECOMMENDATIONS only.

    Each movie can contribute to multiple genres (Comedy + Drama + Family…).
    Much more informative than a single 'primary genre' bar.
    """
    genre_counts = Counter()

    for idx in rec_indices:
        meta = movie_metadata[idx]
        tags = _parse_all_genres(meta)
        for g in tags:
            genre_counts[g] += 1

    if not genre_counts:
        print("[visualize] No genres found for recommendations; skipping histogram.")
        return

    # Sort by count and keep top ~12 for readability
    items = sorted(genre_counts.items(), key=lambda x: -x[1])
    labels, values = zip(*items[:12])

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(range(len(labels)), values)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")

    ax.set_title("Genre distribution of top recommendations (multi-label)")
    ax.set_ylabel("Count")
    ax.set_xlabel("Genre")

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"[viz] Saved {out_path}")


# def plot_genre_histogram(
#     rec_indices: np.ndarray,
#     movie_metadata: List[dict],
#     out_path: Path,
# ) -> None:
#     """
#     Simple histogram of *primary* genres for the recommended movies.
#     """
#     rec_indices = np.asarray(rec_indices, dtype=int)

#     genres = [
#         primary_genre_from_meta(movie_metadata[i])
#         for i in rec_indices
#     ]
#     genres = [g for g in genres if g and g != "Unknown"]

#     if not genres:
#         print("[visualize] No genres found for recommendations; skipping histogram.")
#         return

#     counts = Counter(genres)
#     labels, values = zip(*sorted(counts.items(), key=lambda x: -x[1]))

#     fig, ax = plt.subplots(figsize=(8, 4))
#     ax.bar(range(len(labels)), values)
#     ax.set_xticks(range(len(labels)))
#     ax.set_xticklabels(labels, rotation=45, ha="right")
#     ax.set_ylabel("Count")
#     ax.set_xlabel("Primary genre")
#     ax.set_title("Primary genre distribution of recommendations")

#     out_path.parent.mkdir(parents=True, exist_ok=True)
#     fig.tight_layout()
#     fig.savefig(out_path, dpi=180)
#     plt.close(fig)


# visualizations/plots.py (add this)

from typing import List
import numpy as np
import matplotlib.pyplot as plt
from .genres import build_genre_color_map, primary_genre_from_meta   # already there likely
from .utils import pca_2d

def plot_local_neighborhood_with_cluster_genres(
    user_id: str,
    msg_idx: int,
    user_vec: np.ndarray,
    rec_indices: List[int],
    movie_embeddings: np.ndarray,
    movie_metadata: List[dict],
    cluster_labels: np.ndarray,        # shape (N,)
    cluster_genres: List[str],         # len K
    out_path: Path,
    n_neighbors: int = 800,
):
    """
    Local PCA around the user, but coloring each movie by the majority
    genre of its cluster (cluster_genres[cluster_labels[i]]).
    """

    # --- 1) find nearest neighbors to the user ---
    d2 = np.sum((movie_embeddings - user_vec[None, :])**2, axis=1)
    nn_idx = np.argsort(d2)[:n_neighbors]   # local neighborhood
    local_embs = movie_embeddings[nn_idx]

    # --- 2) 2D PCA on [local movies + user + recs] ---
    rec_embs = movie_embeddings[rec_indices]
    X = np.vstack([local_embs, user_vec[None, :], rec_embs])
    X2 = pca_2d(X)

    L = local_embs.shape[0]
    local_2d = X2[:L]
    user_2d  = X2[L]
    rec_2d   = X2[L+1:]

    # --- 3) colors from cluster-majority genres ---
    # For each local movie, map its cluster id to majority genre
    local_labels = cluster_labels[nn_idx]
    local_genres = [cluster_genres[cid] for cid in local_labels]
    genre_colors = build_genre_color_map(local_genres)
    colors = [genre_colors[g] for g in local_genres]

    fig, ax = plt.subplots(figsize=(10, 7))

    ax.scatter(
        local_2d[:, 0],
        local_2d[:, 1],
        c=colors,
        s=10,
        alpha=0.85,
        linewidths=0,
    )

    # legend: one entry per genre in this neighborhood
    handles = []
    for g, col in sorted(genre_colors.items()):
        handles.append(
            plt.Line2D(
                [0], [0],
                marker="o",
                linestyle="",
                color=col,
                label=g,
                markersize=6,
            )
        )
    # handles = []
    # for g, col in sorted(genre_colors.items()):
    #     if g == "Unknown":
    #         continue
    #     handles.append(
    #         plt.Line2D(
    #             [0], [0],
    #             marker="o",
    #             linestyle="",
    #             color=col,
    #             label=g,
    #             markersize=6,
    #         )
    #     )

    leg = ax.legend(
        handles=[h for h in handles],
        title="Cluster majority genre (local)",
        loc="upper left",
        fontsize=8,
    )
    ax.add_artist(leg)

    # user star
    ax.scatter(
        user_2d[0],
        user_2d[1],
        marker="*",
        s=220,
        edgecolor="black",
        facecolor="orange",
        linewidths=1.0,
        label=f"user '{user_id}'",
        zorder=5,
    )

    # rec dots
    ax.scatter(
        rec_2d[:, 0],
        rec_2d[:, 1],
        s=90,
        edgecolor="black",
        facecolor="limegreen",
        linewidths=1.0,
        label="top recommendations",
        zorder=6,
    )

    # label recs
    import textwrap
    for idx, (x, y) in zip(rec_indices, rec_2d):
        title = movie_metadata[idx].get("title") or movie_metadata[idx].get("tmdb_title") or f"id={idx}"
        short = textwrap.shorten(title, width=28, placeholder="…")
        ax.text(x + 0.01, y + 0.01, short, fontsize=7, ha="left", va="bottom")

    ax.set_title(f"Local taste map (cluster genres) (user='{user_id}', msg={msg_idx})")
    ax.set_xlabel("PC1 (local)")
    ax.set_ylabel("PC2 (local)")
    ax.legend(loc="lower right", fontsize=8)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"[viz] Saved {out_path}")


# visualizations/plots.py
# from .genres import primary_genre_from_meta, build_genre_color_map
# from .utils import pca_2d

def plot_global_sampled_genre_map(
    user_id: str,
    msg_idx: int,
    user_vec: np.ndarray,
    rec_indices: np.ndarray,
    movie_embeddings: np.ndarray,
    movie_metadata: List[dict],
    out_path: Path,
    # optional: precomputed per-movie cluster genres
    movie_cluster_genre: List[str] | None = None,
    sample_frac: float = 0.05,
    max_points: int = 5000,
) -> None:
    """
    Global PCA map:

      • Random sample of movies, colored by genre
        – if movie_cluster_genre is given, use that
        – otherwise use primary_genre_from_meta()
      • User taste as an orange star
      • Top-K recommendations as green points with labels
    """
    N = movie_embeddings.shape[0]
    rng = np.random.default_rng(0)

    # --- 1) choose sample indices ---
    n_sample = min(int(N * sample_frac), max_points)
    sample_idx = rng.choice(N, size=n_sample, replace=False)

    # always ensure recs are included
    rec_indices = np.asarray(rec_indices, dtype=int)
    sample_idx = np.unique(np.concatenate([sample_idx, rec_indices]))
    sample_embs = movie_embeddings[sample_idx]

    # --- 2) PCA on [sample + user + recs] ---
    user_vec = np.asarray(user_vec, dtype=np.float32)
    rec_embs = movie_embeddings[rec_indices]

    X = np.vstack([sample_embs, user_vec[None, :], rec_embs])
    X2 = pca_2d(X)

    S = sample_embs.shape[0]
    sample_2d = X2[:S]
    user_2d = X2[S]
    rec_2d = X2[S + 1 :]

    # --- 3) genres + colors ---
    if movie_cluster_genre is not None:
        sample_genres = [movie_cluster_genre[i] for i in sample_idx]
    else:
        sample_genres = [primary_genre_from_meta(movie_metadata[i]) for i in sample_idx]

    # drop Unknown from color mapping but keep them plotted light gray
    UNKNOWN_COLOR = "#a63c3c"
    # print(sample_genres)
    known_genres = list([g for g in sample_genres if g and g != "Unknown"])
    # print(known_genres)
    color_map = build_genre_color_map(known_genres)

    sample_colors = [
        color_map[g] if g in color_map else UNKNOWN_COLOR
        for g in sample_genres
    ]

    # --- 4) plot ---
    fig, ax = plt.subplots(figsize=(10, 7))

    # sampled movies
    ax.scatter(
        sample_2d[:, 0],
        sample_2d[:, 1],
        s=10,
        c=sample_colors,
        alpha=0.8,
        linewidths=0,
        label="Sampled movies",
    )

    # user
    ax.scatter(
        user_2d[0],
        user_2d[1],
        marker="*",
        s=240,
        edgecolor="black",
        facecolor="orange",
        linewidths=1.0,
        label=f"user '{user_id}' taste",
        zorder=3,
    )

    # recs
    ax.scatter(
        rec_2d[:, 0],
        rec_2d[:, 1],
        s=110,
        edgecolor="black",
        facecolor="limegreen",
        linewidths=1.0,
        label="top recommendations",
        zorder=4,
    )

    # label recs
    for idx, (x, y) in zip(rec_indices, rec_2d):
        title = movie_metadata[idx].get("title") or movie_metadata[idx].get(
            "tmdb_title"
        ) or f"movie_{idx}"
        short = textwrap.shorten(title, width=25, placeholder="…")
        ax.text(
            x + 0.01,
            y + 0.01,
            short,
            fontsize=7,
            ha="left",
            va="bottom",
        )

    # legend for genres (only known)
    legend_handles: List[Patch] = []
    for g in sorted(set(known_genres)):
        legend_handles.append(
            Patch(facecolor=color_map[g], edgecolor="black", label=g)
        )
    genre_legend = ax.legend(
        handles=legend_handles,
        title="Genres (sampled global map)",
        loc="upper left",
        fontsize=8,
    )
    ax.add_artist(genre_legend)

    # user / recs legend
    ax.legend(loc="lower right", fontsize=8)

    ax.set_title(
        f"Global genre map (sampled) (user='{user_id}', msg={msg_idx})"
    )
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"[viz] Saved {out_path}")

