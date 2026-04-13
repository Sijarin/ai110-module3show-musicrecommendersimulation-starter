from typing import List, Dict, Tuple
from dataclasses import dataclass, field
import csv

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # --- Advanced features (default values keep existing tests passing) ---
    popularity: int = 50        # 0–100 mainstream appeal score
    release_decade: int = 2010  # e.g. 1990, 2000, 2010, 2020
    mood_tags: str = ""         # comma-separated detailed mood descriptors
    explicit: int = 0           # 1 = contains explicit content, 0 = clean
    subgenre: str = ""          # finer genre classification


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # --- Advanced preference fields (all optional with sensible defaults) ---
    target_popularity: int = 50         # preferred mainstream level (0–100)
    preferred_decade: int = 0           # 0 = no era preference
    desired_mood_tags: list = field(default_factory=list)  # e.g. ["euphoric","nostalgic"]
    allow_explicit: bool = True         # False = penalise explicit songs
    preferred_subgenre: str = ""        # e.g. "lo-fi hip hop", "death metal"


# ---------------------------------------------------------------------------
# Scoring recipe weights
# ---------------------------------------------------------------------------
GENRE_POINTS       = 2.0   # genre match is the strongest signal
MOOD_POINTS        = 1.0   # mood match — meaningful but narrower than genre
ENERGY_WEIGHT      = 1.5   # max points for a perfect energy match
ACOUSTIC_POINTS    = 0.5   # bonus when acoustic preference is satisfied
# --- Advanced scoring weights (new) ---
POPULARITY_WEIGHT  = 0.75  # max points for a perfect popularity proximity match
DECADE_EXACT_PTS   = 1.0   # preferred decade matches exactly
DECADE_CLOSE_PTS   = 0.5   # preferred decade is one step (10 years) off
MOOD_TAG_PTS       = 0.4   # per matching detailed mood tag (3 tags max → 1.2)
EXPLICIT_PENALTY   = -2.0  # applied when user disallows explicit and song is explicit
SUBGENRE_PTS       = 1.0   # subgenre exact match bonus
# Max possible score = 2.0+1.0+1.5+0.5+0.75+1.0+1.2+1.0 = 9.0


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Return (score, reasons) for one song ranked against a user preference dict; max score is 9.0."""
    score   = 0.0
    reasons: List[str] = []

    # --- Genre match (+2.0) ---
    if song["genre"] == user_prefs.get("genre", ""):
        score += GENRE_POINTS
        reasons.append(f"genre match (+{GENRE_POINTS})")

    # --- Mood match (+1.0) ---
    if song["mood"] == user_prefs.get("mood", ""):
        score += MOOD_POINTS
        reasons.append(f"mood match (+{MOOD_POINTS})")

    # --- Energy proximity (up to +1.5) ---
    target_energy = float(user_prefs.get("energy", 0.5))
    energy_gap    = abs(target_energy - song["energy"])
    energy_pts    = round(ENERGY_WEIGHT * (1.0 - energy_gap), 2)
    score        += energy_pts
    reasons.append(f"energy proximity (+{energy_pts})")

    # --- Acoustic preference (+0.5) ---
    likes_acoustic = bool(user_prefs.get("likes_acoustic", False))
    if likes_acoustic and song["acousticness"] >= 0.6:
        score += ACOUSTIC_POINTS
        reasons.append(f"acoustic sound matches preference (+{ACOUSTIC_POINTS})")
    elif not likes_acoustic and song["acousticness"] < 0.4:
        score += ACOUSTIC_POINTS
        reasons.append(f"electronic sound matches preference (+{ACOUSTIC_POINTS})")

    # --- Popularity proximity (up to +0.75) ---
    # Rewards songs whose mainstream appeal is close to the user's target.
    # Formula mirrors energy proximity: 1 - (gap / 100) scaled by POPULARITY_WEIGHT.
    target_pop = int(user_prefs.get("popularity", 50))
    song_pop   = int(song.get("popularity", 50))
    pop_gap    = abs(target_pop - song_pop) / 100.0
    pop_pts    = round(POPULARITY_WEIGHT * (1.0 - pop_gap), 2)
    score     += pop_pts
    reasons.append(f"popularity proximity (+{pop_pts})")

    # --- Decade match (up to +1.0) ---
    # Exact decade match = full points; one decade off = half points; further = 0.
    # Skipped entirely when either value is 0 (no preference set).
    preferred_decade = int(user_prefs.get("decade", 0))
    song_decade      = int(song.get("release_decade", 0))
    if preferred_decade > 0 and song_decade > 0:
        decade_diff = abs(preferred_decade - song_decade)
        if decade_diff == 0:
            score += DECADE_EXACT_PTS
            reasons.append(f"decade match ({song_decade}s) (+{DECADE_EXACT_PTS})")
        elif decade_diff == 10:
            score += DECADE_CLOSE_PTS
            reasons.append(f"near decade match ({song_decade}s, {decade_diff}yr off) (+{DECADE_CLOSE_PTS})")

    # --- Detailed mood tags (up to +1.2; +0.4 per matching tag, max 3) ---
    # Each tag in the user's desired list that also appears in the song's tag list earns points.
    desired_tags = user_prefs.get("mood_tags", [])
    if isinstance(desired_tags, str):
        desired_tags = [t.strip() for t in desired_tags.split(",") if t.strip()]
    song_tags_raw = song.get("mood_tags", "")
    song_tags     = [t.strip() for t in song_tags_raw.split(",") if t.strip()]
    matching_tags = [t for t in desired_tags if t in song_tags]
    tag_pts       = round(len(matching_tags) * MOOD_TAG_PTS, 2)
    if tag_pts > 0:
        score += tag_pts
        reasons.append(f"mood tags {matching_tags} (+{tag_pts})")

    # --- Explicit content filter (-2.0 penalty) ---
    # Penalises explicit songs when the user has opted out of explicit content.
    allow_explicit = bool(user_prefs.get("allow_explicit", True))
    if not allow_explicit and int(song.get("explicit", 0)) == 1:
        score += EXPLICIT_PENALTY
        reasons.append(f"explicit content penalty ({EXPLICIT_PENALTY})")

    # --- Subgenre match (+1.0) ---
    # Full point bonus for an exact subgenre match; no partial credit.
    preferred_subgenre = user_prefs.get("subgenre", "")
    if preferred_subgenre and song.get("subgenre", "") == preferred_subgenre:
        score += SUBGENRE_PTS
        reasons.append(f"subgenre match '{preferred_subgenre}' (+{SUBGENRE_PTS})")

    return round(score, 4), reasons


# ---------------------------------------------------------------------------
# OOP interface — Recommender class (used by tests/test_recommender.py)
# ---------------------------------------------------------------------------

def _profile_to_prefs(user: UserProfile) -> Dict:
    """Convert a UserProfile dataclass to the dict format score_song expects."""
    return {
        "genre":          user.favorite_genre,
        "mood":           user.favorite_mood,
        "energy":         user.target_energy,
        "likes_acoustic": user.likes_acoustic,
        "popularity":     user.target_popularity,
        "decade":         user.preferred_decade,
        "mood_tags":      user.desired_mood_tags,
        "allow_explicit": user.allow_explicit,
        "subgenre":       user.preferred_subgenre,
    }

def _song_to_dict(song: Song) -> Dict:
    """Convert a Song dataclass to the dict format score_song expects."""
    return {
        "id":             song.id,
        "title":          song.title,
        "artist":         song.artist,
        "genre":          song.genre,
        "mood":           song.mood,
        "energy":         song.energy,
        "tempo_bpm":      song.tempo_bpm,
        "valence":        song.valence,
        "danceability":   song.danceability,
        "acousticness":   song.acousticness,
        "popularity":     song.popularity,
        "release_decade": song.release_decade,
        "mood_tags":      song.mood_tags,
        "explicit":       song.explicit,
        "subgenre":       song.subgenre,
    }


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        """Store the song catalog this recommender will rank against."""
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k songs ranked by descending score."""
        prefs = _profile_to_prefs(user)
        scored = [
            (song, score_song(prefs, _song_to_dict(song))[0])
            for song in self.songs
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [song for song, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-language explanation for why a song was recommended."""
        prefs = _profile_to_prefs(user)
        total, reasons = score_song(prefs, _song_to_dict(song))
        return f"Score {total:.2f} — " + "; ".join(reasons)


# ---------------------------------------------------------------------------
# Functional interface used by src/main.py
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file and return a list of dicts."""
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id":             int(row["id"]),
                "title":          row["title"],
                "artist":         row["artist"],
                "genre":          row["genre"],
                "mood":           row["mood"],
                "energy":         float(row["energy"]),
                "tempo_bpm":      float(row["tempo_bpm"]),
                "valence":        float(row["valence"]),
                "danceability":   float(row["danceability"]),
                "acousticness":   float(row["acousticness"]),
                "popularity":     int(row["popularity"]),
                "release_decade": int(row["release_decade"]),
                "mood_tags":      row["mood_tags"],
                "explicit":       int(row["explicit"]),
                "subgenre":       row["subgenre"],
            })
    return songs


def recommend_songs(
    user_prefs: Dict, songs: List[Dict], k: int = 5
) -> List[Tuple[Dict, float, List[str]]]:
    """Score every song in the catalog and return the top-k as (song, score, reasons) tuples."""
    scored = [
        (song, *score_song(user_prefs, song))
        for song in songs
    ]
    return sorted(scored, key=lambda entry: entry[1], reverse=True)[:k]
