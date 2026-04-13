"""
Command line runner for the Music Recommender Simulation.

Run with:
    python -m src.main
"""

from src.recommender import load_songs, recommend_songs

MAX_SCORE = 9.0   # genre(2.0)+mood(1.0)+energy(1.5)+acoustic(0.5)+
                  # popularity(0.75)+decade(1.0)+mood_tags(1.2)+subgenre(1.0)
BAR_WIDTH = 20    # character width of the score bar


def score_bar(score: float) -> str:
    """Return a visual bar showing score as a fraction of MAX_SCORE."""
    filled = round((score / MAX_SCORE) * BAR_WIDTH)
    return "[" + "#" * filled + "-" * (BAR_WIDTH - filled) + "]"


def print_profile_results(label: str, user_prefs: dict, songs: list) -> None:
    """Run the recommender for one profile and print a formatted results block."""
    recommendations = recommend_songs(user_prefs, songs, k=5)

    decade_label = str(user_prefs.get("decade", 0)) + "s" if user_prefs.get("decade", 0) else "(any)"
    tags_label   = ", ".join(user_prefs.get("mood_tags", [])) or "(any)"

    print()
    print("=" * 60)
    print(f"  {label}")
    print("=" * 60)
    print(f"  Genre            : {user_prefs.get('genre', '(any)')}")
    print(f"  Mood             : {user_prefs.get('mood', '(any)')}")
    print(f"  Target energy    : {user_prefs.get('energy', 0.5)}")
    print(f"  Likes acoustic   : {user_prefs.get('likes_acoustic', False)}")
    print(f"  Target popularity: {user_prefs.get('popularity', 50)}")
    print(f"  Preferred decade : {decade_label}")
    print(f"  Mood tags        : {tags_label}")
    print(f"  Allow explicit   : {user_prefs.get('allow_explicit', True)}")
    print(f"  Subgenre         : {user_prefs.get('subgenre', '(any)') or '(any)'}")
    print("-" * 60)

    for rank, (song, score, reasons) in enumerate(recommendations, start=1):
        bar = score_bar(score)
        print(f"  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"       Score: {score:.2f} / {MAX_SCORE:.1f}  {bar}")
        for reason in reasons:
            print(f"       • {reason}")
        print()

    print("=" * 60)


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
                "popularity":     85,
                "decade":         2020,
                "mood_tags":      ["euphoric", "danceable"],
                "allow_explicit": True,
                "subgenre":       "dance pop",
            },
        ),
        (
            "PROFILE 2 — Chill Lofi",
            {
                "genre":          "lofi",
                "mood":           "chill",
                "energy":         0.38,
                "likes_acoustic": True,
                "popularity":     58,
                "decade":         2020,
                "mood_tags":      ["nostalgic", "peaceful"],
                "allow_explicit": False,
                "subgenre":       "lo-fi hip hop",
            },
        ),
        (
            "PROFILE 3 — Deep Intense Rock",
            {
                "genre":          "rock",
                "mood":           "intense",
                "energy":         0.91,
                "likes_acoustic": False,
                "popularity":     70,
                "decade":         2010,
                "mood_tags":      ["aggressive", "powerful"],
                "allow_explicit": False,
                "subgenre":       "alternative rock",
            },
        ),

        # ── Adversarial / edge-case profiles ──────────────────────────────────

        # Profile 4 — Conflicting preferences
        # High energy + melancholic mood don't coexist in the catalog.
        # Now also requests death metal subgenre with explicit=False,
        # which penalises Iron Curtain (the only death metal song, explicit=1).
        (
            "PROFILE 4 — Conflicting (high energy + melancholic, no explicit)",
            {
                "genre":          "metal",
                "mood":           "melancholic",
                "energy":         0.92,
                "likes_acoustic": False,
                "popularity":     65,
                "decade":         2010,
                "mood_tags":      ["aggressive", "dark"],
                "allow_explicit": False,
                "subgenre":       "death metal",
            },
        ),

        # Profile 5 — Genre orphan
        # Only one reggae song in the catalog. Tests graceful fallback via
        # energy/acoustic similarity + new advanced rules.
        (
            "PROFILE 5 — Genre Orphan (reggae, uplifting)",
            {
                "genre":          "reggae",
                "mood":           "uplifting",
                "energy":         0.61,
                "likes_acoustic": True,
                "popularity":     57,
                "decade":         2010,
                "mood_tags":      ["uplifting", "peaceful"],
                "allow_explicit": False,
                "subgenre":       "reggae fusion",
            },
        ),

        # Profile 6 — Dead-centre neutral
        # No genre, mood, or subgenre preference. Tests pure numeric scoring:
        # energy proximity + popularity proximity + decade matching decide results.
        (
            "PROFILE 6 — Dead-Centre Neutral (no genre/mood preference)",
            {
                "genre":          "",
                "mood":           "",
                "energy":         0.50,
                "likes_acoustic": False,
                "popularity":     50,
                "decade":         0,
                "mood_tags":      [],
                "allow_explicit": True,
                "subgenre":       "",
            },
        ),
    ]

    for label, prefs in profiles:
        print_profile_results(label, prefs, songs)

    print()


if __name__ == "__main__":
    main()
