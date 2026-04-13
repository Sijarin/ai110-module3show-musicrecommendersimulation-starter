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


def print_profile_results(label: str, user_prefs: dict, songs: list) -> None:
    """Run the recommender for one profile and print a formatted results block."""
    recommendations = recommend_songs(user_prefs, songs, k=5)

    print()
    print("=" * 52)
    print(f"  {label}")
    print("=" * 52)
    print(f"  Genre          : {user_prefs.get('genre', '(any)')}")
    print(f"  Mood           : {user_prefs.get('mood', '(any)')}")
    print(f"  Target energy  : {user_prefs.get('energy', 0.5)}")
    print(f"  Likes acoustic : {user_prefs.get('likes_acoustic', False)}")
    print("-" * 52)

    for rank, (song, score, reasons) in enumerate(recommendations, start=1):
        bar = score_bar(score)
        print(f"  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"       Score: {score:.2f} / {MAX_SCORE:.1f}  {bar}")
        for reason in reasons:
            print(f"       • {reason}")
        print()

    print("=" * 52)


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"\nCatalog loaded: {len(songs)} songs")

    # ── Standard profiles ─────────────────────────────────────────────────────

    profiles = [
        (
            "PROFILE 1 — High-Energy Pop",
            {
                "genre":          "pop",
                "mood":           "happy",
                "energy":         0.82,
                "likes_acoustic": False,
            },
        ),
        (
            "PROFILE 2 — Chill Lofi",
            {
                "genre":          "lofi",
                "mood":           "chill",
                "energy":         0.38,
                "likes_acoustic": True,
            },
        ),
        (
            "PROFILE 3 — Deep Intense Rock",
            {
                "genre":          "rock",
                "mood":           "intense",
                "energy":         0.91,
                "likes_acoustic": False,
            },
        ),

        # ── Adversarial / edge-case profiles ──────────────────────────────────
        #
        # Profile 4 — Conflicting preferences
        #   energy=0.92 sits at the metal/EDM end of the catalog, but mood=melancholic
        #   maps to low-energy soul/ambient tracks. No song satisfies both.
        #   Expected reveal: the system picks by energy proximity + acoustic bonus;
        #   the mood bonus never fires, so melancholic songs never surface.
        (
            "PROFILE 4 — Conflicting (high energy + melancholic mood)",
            {
                "genre":          "metal",
                "mood":           "melancholic",
                "energy":         0.92,
                "likes_acoustic": False,
            },
        ),

        # Profile 5 — Genre orphan
        #   Only one reggae song in the catalog. Tests whether the ranking gracefully
        #   fills the remaining 4 slots via energy/acoustic similarity rather than
        #   collapsing to all low-scoring songs.
        (
            "PROFILE 5 — Genre Orphan (reggae, uplifting)",
            {
                "genre":          "reggae",
                "mood":           "uplifting",
                "energy":         0.61,
                "likes_acoustic": True,
            },
        ),

        # Profile 6 — Dead-centre neutral
        #   energy=0.5 is the midpoint of the 0–1 scale; no genre or mood set.
        #   No categorical bonuses ever fire. Tests pure energy-proximity ranking:
        #   whichever songs sit closest to 0.5 BPM-energy win, regardless of vibe.
        (
            "PROFILE 6 — Dead-Centre Neutral (no genre/mood preference)",
            {
                "genre":          "",
                "mood":           "",
                "energy":         0.50,
                "likes_acoustic": False,
            },
        ),
    ]

    for label, prefs in profiles:
        print_profile_results(label, prefs, songs)

    print()


if __name__ == "__main__":
    main()
