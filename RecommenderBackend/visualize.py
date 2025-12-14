#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import csv
import pandas as pd
from embedding_loader import load_movie_embeddings
from config import MOVIE_EMBED_PATH
from visualizations import (
    load_log_records,
    pick_record_for_visualization,
    plot_embedding_map,
    plot_local_neighborhood_with_genres,
    plot_genre_histogram,
    plot_local_neighborhood_with_cluster_genres,
)
from visualizations.clusters import (
    plot_cluster_overview_with_user,
    compute_cluster_majority_genres,
)
from visualizations.utils import pca_2d



# def main():
#     parser = argparse.ArgumentParser(
#         description="Visualize user taste vs movie embedding space using rec_log.jsonl."
#     )
#     parser.add_argument("--user-id", type=str, required=True)
#     parser.add_argument(
#         "--msg-index",
#         type=int,
#         default=None,
#         help="Per-user message index to visualize (default: latest).",
#     )
#     parser.add_argument(
#         "--out-dir",
#         type=str,
#         default="figures",
#         help="Output directory for plots.",
#     )
#     args = parser.parse_args()

#     user_id = args.user_id
#     msg_index = args.msg_index
#     out_dir = Path(args.out_dir)
#     out_dir.mkdir(parents=True, exist_ok=True)

#     # ----- load log entry -----
#     print(f"[visualize] Loading log records for user_id='{user_id}'...")
#     records = load_log_records(user_id)
#     log_rec = pick_record_for_visualization(records, msg_index=msg_index)
#     actual_msg_index = int(log_rec["msg_index"])
#     print(f"[visualize] Using msg_index={actual_msg_index} (ts={log_rec['timestamp']})")

#     # ----- load embeddings -----
#     print("[visualize] Loading movie embeddings…")
#     movie_embeddings, movie_metadata = load_movie_embeddings(MOVIE_EMBED_PATH)

#     user_vec = np.array(log_rec["user_vec"], dtype=np.float32)
#     candidate_indices = np.array(log_rec["candidate_indices"], dtype=int)
#     final_k = int(log_rec["final_k"])
#     rec_indices = candidate_indices[:final_k]

#     # ---------- 1) global embedding map ----------
#     from visualizations.utils import pca_2d  # avoid circular imports
#     X = np.vstack([movie_embeddings, user_vec[None, :]])
#     X2 = pca_2d(X)
#     movies_2d = X2[:-1]
#     user_2d = X2[-1]
#     rec_2d = movies_2d[rec_indices]

#     map_path = out_dir / f"{user_id}_msg{actual_msg_index}_global_map.png"
#     print(f"[visualize] Saving global embedding map to {map_path}")
#     plot_embedding_map(
#         user_id=user_id,
#         msg_index=actual_msg_index,
#         movies_2d=movies_2d,
#         user_2d=user_2d,
#         rec_indices=rec_indices,
#         rec_2d=rec_2d,
#         movie_metadata=movie_metadata,
#         out_path=map_path,
#     )

#     # ---------- 2) local neighborhood with genres (new) ----------
#     local_path = out_dir / f"{user_id}_msg{actual_msg_index}_local_map.png"
#     print(f"[visualize] Saving local neighborhood map to {local_path}")
#     plot_local_neighborhood_with_genres(
#         user_id=user_id,
#         msg_idx=actual_msg_index,
#         user_vec=user_vec,
#         rec_indices=rec_indices.tolist(),
#         movie_embeddings=movie_embeddings,
#         movie_metadata=movie_metadata,
#         out_path=local_path,
#     )

#         # ---------- 3) cluster-level overview ----------
#     cluster_path = out_dir / f"{user_id}_msg{actual_msg_index}_cluster_map.png"
#     print(f"[visualize] Saving cluster overview to {cluster_path}")
#     plot_cluster_overview_with_user(
#         user_id=user_id,
#         msg_idx=actual_msg_index,
#         user_vec=user_vec,
#         rec_indices=rec_indices.tolist(),
#         movie_embeddings=movie_embeddings,
#         movie_metadata=movie_metadata,
#         out_path=cluster_path,
#         n_clusters=25,   # tweak if you want coarser/finer
#     )


#     # ---------- 3) genre histogram of recommendations ----------
#     hist_path = out_dir / f"{user_id}_msg{actual_msg_index}_genre_hist.png"
#     print(f"[visualize] Saving genre histogram to {hist_path}")
#     plot_genre_histogram(
#         rec_indices=rec_indices,
#         movie_metadata=movie_metadata,
#         out_path=hist_path,
#     )

#     print("[visualize] Done.")


# if __name__ == "__main__":
#     main()



def main():
    parser = argparse.ArgumentParser(
        description="Visualize user taste vs movie embedding space using rec_log.jsonl."
    )
    parser.add_argument("--user-id", type=str, required=True)
    parser.add_argument(
        "--msg-index",
        type=int,
        default=None,
        help="Per-user message index to visualize (default: latest).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="figures",
        help="Output directory for plots.",
    )
    args = parser.parse_args()

    user_id = args.user_id
    msg_index = args.msg_index
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ----- load log entry -----
    print(f"[visualize] Loading log records for user_id='{user_id}'...")
    records = load_log_records(user_id)
    log_rec = pick_record_for_visualization(records, msg_index=msg_index)
    actual_msg_index = int(log_rec["msg_index"])
    print(f"[visualize] Using msg_index={actual_msg_index} (ts={log_rec['timestamp']})")

    # ----- load embeddings -----
    print("[visualize] Loading movie embeddings…")
    movie_embeddings, movie_metadata = load_movie_embeddings(MOVIE_EMBED_PATH)

    user_vec = np.array(log_rec["user_vec"], dtype=np.float32)
    candidate_indices = np.array(log_rec["candidate_indices"], dtype=int)
    final_k = int(log_rec["final_k"])
    rec_indices = candidate_indices[:final_k]

    # ---------- 1) global embedding map ----------
    X = np.vstack([movie_embeddings, user_vec[None, :]])
    X2 = pca_2d(X)
    movies_2d = X2[:-1]
    user_2d = X2[-1]
    rec_2d = movies_2d[rec_indices]

    map_path = out_dir / f"{user_id}_msg{actual_msg_index}_global_map.png"
    print(f"[visualize] Saving global embedding map to {map_path}")
    plot_embedding_map(
        user_id=user_id,
        msg_index=actual_msg_index,
        movies_2d=movies_2d,
        user_2d=user_2d,
        rec_indices=rec_indices,
        rec_2d=rec_2d,
        movie_metadata=movie_metadata,
        out_path=map_path,
    )

    # ---------- 2) local neighborhood with genres ----------
    movie_cluster_genre = pd.read_csv('movie_cluster_genres.csv')["cluster_genre"]


    local_path = out_dir / f"{user_id}_msg{actual_msg_index}_local_map.png"
    print(f"[visualize] Saving local neighborhood map to {local_path}")
    plot_local_neighborhood_with_genres(
        user_id=user_id,
        msg_idx=actual_msg_index,
        user_vec=user_vec,
        rec_indices=rec_indices.tolist(),
        movie_embeddings=movie_embeddings,
        movie_metadata=movie_metadata,
        out_path=local_path,
        movie_cluster_genre=movie_cluster_genre
    )

    # ---------- 3) cluster-level overview ----------
    cluster_path = out_dir / f"{user_id}_msg{actual_msg_index}_cluster_map.png"
    print(f"[visualize] Saving cluster overview to {cluster_path}")
    plot_cluster_overview_with_user(
        user_id=user_id,
        msg_idx=actual_msg_index,
        user_vec=user_vec,
        rec_indices=rec_indices.tolist(),
        movie_embeddings=movie_embeddings,
        movie_metadata=movie_metadata,
        out_path=cluster_path,
        n_clusters=25,
    )

    # ---------- 4) genre histogram of recommendations ----------
    hist_path = out_dir / f"{user_id}_msg{actual_msg_index}_genre_hist.png"
    print(f"[visualize] Saving genre histogram to {hist_path}")
    plot_genre_histogram(
        rec_indices=rec_indices,
        movie_metadata=movie_metadata,
        out_path=hist_path,
    )

    cluster_labels, cluster_centers, cluster_genres = compute_cluster_majority_genres(
        movie_embeddings,
        movie_metadata,
        n_clusters=25,
        random_state=0,
    )

    # local map USING cluster-majority genres
    local_path = out_dir / f"{user_id}_msg{actual_msg_index}_local_clusters.png"
    print(f"[visualize] Saving local neighborhood (cluster genres) map to {local_path}")
    plot_local_neighborhood_with_cluster_genres(
        user_id=user_id,
        msg_idx=actual_msg_index,
        user_vec=user_vec,
        rec_indices=rec_indices.tolist(),
        movie_embeddings=movie_embeddings,
        movie_metadata=movie_metadata,
        cluster_labels=cluster_labels,
        cluster_genres=cluster_genres,
        out_path=local_path,
    )

    from visualizations.plots import plot_global_sampled_genre_map
    # if you load cluster genres from DB, pass them in as movie_cluster_genre
    # for now you can just set it to None or compute on the fly


    # with open('movie_cluster_genres.csv', 'r') as read_obj:

    #     # Return a reader object which will
    #     # iterate over lines in the given csvfile
    #     csv_reader = csv.reader(read_obj)

    #     # convert string to list
    #     movie_cluster_genre = list(csv_reader)

    sampled_map_path = out_dir / f"{user_id}_msg{actual_msg_index}_global_sampled_genres.png"
    plot_global_sampled_genre_map(
        user_id=user_id,
        msg_idx=actual_msg_index,
        user_vec=user_vec,
        rec_indices=rec_indices,
        movie_embeddings=movie_embeddings,
        movie_metadata=movie_metadata,
        out_path=sampled_map_path,
        movie_cluster_genre=movie_cluster_genre,   # or your precomputed list
    )


    print("[visualize] Done.")


if __name__ == "__main__":
    main()
