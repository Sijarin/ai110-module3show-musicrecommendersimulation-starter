from typing import List, Dict, Tuple
from dataclasses import dataclass
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


# ---------------------------------------------------------------------------
# Scoring recipe weights
# ---------------------------------------------------------------------------
GENRE_POINTS    = 2.0   # genre match is the strongest signal
MOOD_POINTS     = 1.0   # mood match — meaningful but narrower than genre
ENERGY_WEIGHT   = 1.5   # max points for a perfect energy match
ACOUSTIC_POINTS = 0.5   # bonus when acoustic preference is satisfied


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Return (score, reasons) for one song ranked against a user preference dict; max score is 5.0."""
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
    target_energy   = float(user_prefs.get("energy", 0.5))
    energy_gap      = abs(target_energy - song["energy"])
    energy_pts      = round(ENERGY_WEIGHT * (1.0 - energy_gap), 2)
    score          += energy_pts
    reasons.append(f"energy proximity (+{energy_pts})")

    # --- Acoustic preference (+0.5) ---
    likes_acoustic = bool(user_prefs.get("likes_acoustic", False))
    if likes_acoustic and song["acousticness"] >= 0.6:
        score += ACOUSTIC_POINTS
        reasons.append(f"acoustic sound matches preference (+{ACOUSTIC_POINTS})")
    elif not likes_acoustic and song["acousticness"] < 0.4:
        score += ACOUSTIC_POINTS
        reasons.append(f"electronic sound matches preference (+{ACOUSTIC_POINTS})")

    return round(score, 4), reasons


# ---------------------------------------------------------------------------
# OOP interface — Recommender class (used by tests/test_recommender.py)
# ---------------------------------------------------------------------------

def _profile_to_prefs(user: UserProfile) -> Dict:
    """Convert a UserProfile dataclass to the dict format score_song expects."""
    return {
        "genre":         user.favorite_genre,
        "mood":          user.favorite_mood,
        "energy":        user.target_energy,
        "likes_acoustic": user.likes_acoustic,
    }

def _song_to_dict(song: Song) -> Dict:
    """Convert a Song dataclass to the dict format score_song expects."""
    return {
        "id":           song.id,
        "title":        song.title,
        "artist":       song.artist,
        "genre":        song.genre,
        "mood":         song.mood,
        "energy":       song.energy,
        "tempo_bpm":    song.tempo_bpm,
        "valence":      song.valence,
        "danceability": song.danceability,
        "acousticness": song.acousticness,
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
                "id":           int(row["id"]),
                "title":        row["title"],
                "artist":       row["artist"],
                "genre":        row["genre"],
                "mood":         row["mood"],
                "energy":       float(row["energy"]),
                "tempo_bpm":    float(row["tempo_bpm"]),
                "valence":      float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    return songs


def recommend_songs(
    user_prefs: Dict, songs: List[Dict], k: int = 5
) -> List[Tuple[Dict, float, List[str]]]:
    """Score every song in the catalog and return the top-k as (song, score, reasons) tuples."""
    # Score every song in one list comprehension.
    # *score_song(...) unpacks the (total, reasons) tuple inline so each
    # entry is (song_dict, total, reasons) without a separate unpack step.
    scored = [
        (song, *score_song(user_prefs, song))
        for song in songs
    ]

    # sorted() key targets index 1 (the numeric score).
    # reverse=True puts the highest score first.
    # [:k] slices the top-k results from the already-sorted list.
    return sorted(scored, key=lambda entry: entry[1], reverse=True)[:k]
