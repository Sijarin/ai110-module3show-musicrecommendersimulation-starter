"""
Command line runner for the Music Recommender Simulation.

Run with:
    python -m src.main
"""

from src.recommender import (
    load_songs, recommend_songs, diverse_recommend_songs,
    SCORING_MODES, get_max_score,
    ARTIST_REPEAT_PENALTY, GENRE_REPEAT_PENALTY,
)

BAR_WIDTH = 20    # character width of the score bar


def score_bar(score: float, max_score: float) -> str:
    """Return a visual bar showing score as a fraction of max_score."""
    filled = round((score / max_score) * BAR_WIDTH)
    return "[" + "#" * filled + "-" * (BAR_WIDTH - filled) + "]"


def print_profile_results(
    label: str, user_prefs: dict, songs: list, mode: str = "balanced"
) -> None:
    """Run the recommender for one profile+mode and print a formatted results block."""
    recommendations = recommend_songs(user_prefs, songs, k=5, mode=mode)
    max_score       = get_max_score(mode)

    decade_label = str(user_prefs.get("decade", 0)) + "s" if user_prefs.get("decade", 0) else "(any)"
    tags_label   = ", ".join(user_prefs.get("mood_tags", [])) or "(any)"

    print()
    print("=" * 62)
    print(f"  {label}")
    print("=" * 62)
    print(f"  Scoring mode     : {mode}")
    print(f"  Genre            : {user_prefs.get('genre', '(any)')}")
    print(f"  Mood             : {user_prefs.get('mood', '(any)')}")
    print(f"  Target energy    : {user_prefs.get('energy', 0.5)}")
    print(f"  Likes acoustic   : {user_prefs.get('likes_acoustic', False)}")
    print(f"  Target popularity: {user_prefs.get('popularity', 50)}")
    print(f"  Preferred decade : {decade_label}")
    print(f"  Mood tags        : {tags_label}")
    print(f"  Allow explicit   : {user_prefs.get('allow_explicit', True)}")
    print(f"  Subgenre         : {user_prefs.get('subgenre', '(any)') or '(any)'}")
    print("-" * 62)

    for rank, (song, score, reasons) in enumerate(recommendations, start=1):
        bar = score_bar(score, max_score)
        print(f"  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"       Score: {score:.2f} / {max_score:.2f}  {bar}")
        for reason in reasons:
            print(f"       • {reason}")
        print()

    print("=" * 62)


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"\nCatalog loaded: {len(songs)} songs")

    # ── Standard profiles — each uses a different scoring mode ──────────────
    # The mode is chosen to match the listener's personality:
    #   Pop fan  → balanced (all signals matter)
    #   Lofi fan → mood_first (emotional vibe is the point)
    #   Rock fan → genre_first (genre identity is non-negotiable)
    #   Workout  → energy_focused (sonic intensity over label)
    #   Explorer → discovery (break out of the usual bubble)

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
            "balanced",
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
            "mood_first",
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
            "genre_first",
        ),
        (
            "PROFILE 4 — Workout (high energy, no preference on genre)",
            {
                "genre":          "",
                "mood":           "",
                "energy":         0.95,
                "likes_acoustic": False,
                "popularity":     75,
                "decade":         2020,
                "mood_tags":      ["aggressive", "energetic"],
                "allow_explicit": True,
                "subgenre":       "",
            },
            "energy_focused",
        ),
        (
            "PROFILE 5 — Genre Orphan / Explorer (reggae)",
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
            "discovery",
        ),
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
            "balanced",
        ),
    ]

    for label, prefs, mode in profiles:
        print_profile_results(label, prefs, songs, mode=mode)

    # ── Mode comparison: same profile, all five strategies ───────────────────
    # Profile 3 (Deep Intense Rock) is the most interesting test case because
    # of the known Gym Hero vs Iron Curtain problem. Running it under every
    # mode shows exactly how the weight table changes the answer.

    print()
    print()
    print("*" * 62)
    print("  MODE COMPARISON")
    print("  Profile: Deep Intense Rock — same preferences, 5 modes")
    print("  Watch how Gym Hero (pop/intense) vs Iron Curtain (metal/explicit)")
    print("  swap ranks as the weight strategy changes.")
    print("*" * 62)

    rock_prefs = {
        "genre":          "rock",
        "mood":           "intense",
        "energy":         0.91,
        "likes_acoustic": False,
        "popularity":     70,
        "decade":         2010,
        "mood_tags":      ["aggressive", "powerful"],
        "allow_explicit": False,
        "subgenre":       "alternative rock",
    }

    for mode_name in SCORING_MODES:
        print_profile_results(
            f"[{mode_name.upper()}]  Deep Intense Rock",
            rock_prefs,
            songs,
            mode=mode_name,
        )

    # ── Diversity penalty demo ────────────────────────────────────────────────
    # Show two profiles that produce artist repeats without diversity logic,
    # then re-run them with diverse_recommend_songs to show the fix.
    #
    # Profile 2 (mood_first):   LoRoom appears at #2 AND #4
    # Profile 6 (balanced):     LoRoom appears at #4 AND #5

    print()
    print()
    print("*" * 62)
    print("  DIVERSITY PENALTY DEMO")
    print(f"  Artist repeat penalty : {ARTIST_REPEAT_PENALTY} per occurrence")
    print(f"  Genre  repeat penalty : {GENRE_REPEAT_PENALTY} per occurrence")
    print("  Penalties compound — a 3rd song from the same artist")
    print("  loses twice the single-repeat penalty.")
    print("*" * 62)

    diversity_cases = [
        (
            "Profile 2 — Chill Lofi  (LoRoom repeats at #2 and #4)",
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
            "mood_first",
        ),
        (
            "Profile 6 — Neutral  (LoRoom repeats at #4 and #5)",
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
            "balanced",
        ),
    ]

    for label, prefs, mode in diversity_cases:
        max_score = get_max_score(mode)

        # --- WITHOUT diversity ---
        standard = recommend_songs(prefs, songs, k=5, mode=mode)
        print()
        print("=" * 62)
        print(f"  WITHOUT diversity — {label}")
        print(f"  mode: {mode}  |  max score: {max_score:.2f}")
        print("-" * 62)
        for rank, (song, sc, reasons) in enumerate(standard, 1):
            bar = score_bar(sc, max_score)
            print(f"  #{rank}  {song['title']}  —  {song['artist']}  [{song['genre']}]")
            print(f"       Score: {sc:.2f} / {max_score:.2f}  {bar}")
        print("=" * 62)

        # --- WITH diversity ---
        diverse = diverse_recommend_songs(prefs, songs, k=5, mode=mode)
        print()
        print("=" * 62)
        print(f"  WITH diversity    — {label}")
        print(f"  mode: {mode}  |  max score: {max_score:.2f}")
        print("-" * 62)
        for rank, (song, sc, reasons) in enumerate(diverse, 1):
            bar = score_bar(sc, max_score)
            print(f"  #{rank}  {song['title']}  —  {song['artist']}  [{song['genre']}]")
            print(f"       Score: {sc:.2f} / {max_score:.2f}  {bar}")
            for r in reasons:
                if "penalty" in r:
                    print(f"       • {r}")
        print("=" * 62)

    print()


if __name__ == "__main__":
    main()
