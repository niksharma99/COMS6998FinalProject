# visualizations/clusters.py
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA

from .genres import primary_genre_from_meta, majority_primary_genre, build_genre_color_map

from sklearn.cluster import KMeans

from .genres import majority_primary_genre

def compute_cluster_majority_genres(
    movie_embeddings: np.ndarray,
    movie_metadata: List[dict],
    n_clusters: int = 25,
    random_state: int = 0,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Run KMeans on all movie embeddings and compute a majority genre label
    for each cluster.

    Returns:
        labels:  np.ndarray[int] shape (N,)   - cluster id per movie
        centers: np.ndarray[float] shape (K,D) - cluster centroids
        cluster_genres: list[str] length K    - majority genre per cluster
    """
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init="auto",
    )
    labels = kmeans.fit_predict(movie_embeddings)
    centers = kmeans.cluster_centers_

    cluster_genres: list[str] = []
    for cid in range(n_clusters):
        idxs = np.where(labels == cid)[0].tolist()
        g = majority_primary_genre(idxs, movie_metadata)
        if g is None:
            cluster_genres.append("Unknown")  # fallback only if whole cluster is empty
        else:
            cluster_genres.append(g)

    return labels, centers, cluster_genres



def _cluster_movies(
    movie_embeddings: np.ndarray,
    movie_metadata: List[dict],
    n_clusters: int = 25,
):
    """
    Cluster all movies and attach a majority primary genre to each cluster.

    Returns:
      labels:        (N,) int array, cluster id for each movie
      centroids:     (C, D) array, cluster centers in embedding space
      cluster_genre: list[str] length C, majority primary genre per cluster
      cluster_sizes: (C,) int array, #movies per cluster
    """
    N, _ = movie_embeddings.shape

    kmeans = MiniBatchKMeans(
        n_clusters=n_clusters,
        batch_size=min(8192, N),
        random_state=0,
        verbose=False,
    )
    labels = kmeans.fit_predict(movie_embeddings)
    centroids = kmeans.cluster_centers_

    cluster_genre: List[str] = []
    cluster_sizes: List[int] = []

    for cid in range(n_clusters):
        idxs = np.where(labels == cid)[0].tolist()
        cluster_sizes.append(len(idxs))
        if not idxs:
            cluster_genre.append("Unknown")
        else:
            g = majority_primary_genre(idxs, movie_metadata)
            cluster_genre.append(g if g is not None else "Unknown")


    return labels, centroids, np.asarray(cluster_sizes, dtype=int), cluster_genre


def plot_cluster_overview_with_user(
    user_id: str,
    msg_idx: int | None,
    user_vec: np.ndarray,
    rec_indices: List[int],
    movie_embeddings: np.ndarray,
    movie_metadata: List[dict],
    out_path: Path,
    n_clusters: int = 25,
) -> None:
    """
    Cluster-level taste map:

      • One point per cluster (centroid in embedding space)
      • Cluster colored by its majority primary genre
      • User taste vector as an orange star
      • Top-K recommendations as green points with labels
        (each labelled with its cluster's majority genre)
    """
    user_vec = np.asarray(user_vec, dtype=np.float32)

    # 1) cluster movies
    labels, centroids, cluster_sizes, cluster_genre = _cluster_movies(
        movie_embeddings, movie_metadata, n_clusters=n_clusters
    )

    # 2) PCA on centroids + user + recs
    rec_indices = np.asarray(rec_indices, dtype=int)
    rec_embs = movie_embeddings[rec_indices]

    X = np.vstack([centroids, user_vec[None, :], rec_embs])
    pca = PCA(n_components=2, random_state=0)
    X2 = pca.fit_transform(X)

    C = centroids.shape[0]
    centroids_2d = X2[:C]
    user_2d = X2[C]
    rec_2d = X2[C + 1 :]

    # 3) colors for clusters by majority genre
    cluster_genre = [g if g is not None else "Unknown" for g in cluster_genre]
    color_map = build_genre_color_map(cluster_genre)
    cluster_colors = [color_map[g] for g in cluster_genre]

    fig, ax = plt.subplots(figsize=(10, 7))

    # cluster centroids
    ax.scatter(
        centroids_2d[:, 0],
        centroids_2d[:, 1],
        s=30 + 10 * np.sqrt(cluster_sizes / cluster_sizes.max()),
        c=cluster_colors,
        alpha=0.8,
        edgecolor="black",
        linewidths=0.5,
        label="Clusters",
        zorder=1,
    )

    # user taste
    ax.scatter(
        user_2d[0],
        user_2d[1],
        marker="*",
        s=260,
        edgecolor="black",
        facecolor="orange",
        linewidths=1.0,
        label=f"user '{user_id}' taste",
        zorder=3,
    )

    # recommendations
    ax.scatter(
        rec_2d[:, 0],
        rec_2d[:, 1],
        s=120,
        edgecolor="black",
        facecolor="limegreen",
        linewidths=1.0,
        label="top recommendations",
        zorder=4,
    )

    # lines + labels
    for idx, (x, y) in zip(rec_indices, rec_2d):
        ax.plot(
            [user_2d[0], x],
            [user_2d[1], y],
            linestyle="--",
            color="gray",
            linewidth=0.8,
            alpha=0.85,
            zorder=2,
        )

        meta = movie_metadata[idx]
        title = meta.get("title") or meta.get("tmdb_title") or f"movie_{idx}"
        cid = int(labels[idx])
        g = cluster_genre[cid]
        label_text = f"{title}\n(c{cid}: {g})"

        ax.text(
            x + 0.015,
            y + 0.015,
            label_text,
            fontsize=7,
            ha="left",
            va="bottom",
        )

    # genre legend
    genre_names = sorted(set(cluster_genre))
    handles = [
        Patch(facecolor=color_map[g], edgecolor="black", label=g)
        for g in genre_names
    ]
    legend1 = ax.legend(
        handles=handles,
        title="Cluster majority genre",
        loc="upper left",
        fontsize=8,
    )
    ax.add_artist(legend1)

    # user/recs legend
    ax.legend(loc="lower right", fontsize=8)

    ax.set_title(f"Cluster-level taste map (user='{user_id}', msg={msg_idx})")
    ax.set_xlabel("PC1 (clusters)")
    ax.set_ylabel("PC2 (clusters)")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"[viz] Saved {out_path}")


# visualizations/clusters.py

def compute_per_movie_cluster_genre(
    movie_embeddings: np.ndarray,
    movie_metadata: List[dict],
    n_clusters: int = 25,
    random_state: int = 0,
) -> tuple[np.ndarray, List[str], List[str]]:
    """
    Cluster movies once and assign a 'cluster-majority genre' to every movie.

    Returns:
        labels:          (N,) int    cluster id per movie
        cluster_genres:  list[str]   length K, majority genre per cluster
        movie_cluster_genre: list[str] length N, genre for each movie
    """
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init="auto",
    )
    labels = kmeans.fit_predict(movie_embeddings)

    # majority genre per cluster
    cluster_genres: list[str] = []
    for cid in range(n_clusters):
        idxs = np.where(labels == cid)[0].tolist()
        g = majority_primary_genre(idxs, movie_metadata)
        cluster_genres.append(g if g is not None else "Unknown")

    # genre per movie = genre of its cluster
    movie_cluster_genre = [cluster_genres[cid] for cid in labels]

    return labels, cluster_genres, movie_cluster_genre
