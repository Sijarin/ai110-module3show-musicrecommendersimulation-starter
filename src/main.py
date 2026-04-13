"""
Command line runner for the Music Recommender Simulation.

Run with:
    python -m src.main
"""

from src.recommender import load_songs, recommend_songs

MAX_SCORE = 5.0   # genre(2.0) + mood(1.0) + energy(1.5) + acoustic(0.5)
BAR_WIDTH = 20    # character width of the score bar


def score_bar(score: float) -> str:
    """Return a visual bar showing score as a fraction of MAX_SCORE."""
    filled = round((score / MAX_SCORE) * BAR_WIDTH)
    return "[" + "#" * filled + "-" * (BAR_WIDTH - filled) + "]"


def main() -> None:
    songs = load_songs("data/songs.csv")

    # User taste profile:
    # A high-energy pop listener who enjoys upbeat, danceable tracks and
    # prefers electronic/produced sound over acoustic instruments.
    user_prefs = {
        "genre":          "pop",
        "mood":           "happy",
        "energy":         0.82,
        "likes_acoustic": False,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    # ── Header ────────────────────────────────────────────────────────────────
    print()
    print("=" * 52)
    print("   MUSIC RECOMMENDER SIMULATION")
    print("=" * 52)
    print(f"  Catalog loaded : {len(songs)} songs")
    print(f"  Genre          : {user_prefs['genre']}")
    print(f"  Mood           : {user_prefs['mood']}")
    print(f"  Target energy  : {user_prefs['energy']}")
    print(f"  Likes acoustic : {user_prefs['likes_acoustic']}")
    print("=" * 52)
    print(f"  Top {len(recommendations)} Recommendations")
    print("=" * 52)

    # ── Results ───────────────────────────────────────────────────────────────
    for rank, (song, score, reasons) in enumerate(recommendations, start=1):
        bar = score_bar(score)
        print(f"\n  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"       Score: {score:.2f} / {MAX_SCORE:.1f}  {bar}")
        for reason in reasons:
            print(f"       • {reason}")

    print()
    print("=" * 52)


if __name__ == "__main__":
    main()
