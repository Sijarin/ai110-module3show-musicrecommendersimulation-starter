# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use

VibeFinder suggests up to 5 songs from an 18-song catalog based on a listener's stated genre, mood, energy level, and acoustic preference. It is designed for classroom exploration of how recommendation systems work — not for real-world deployment or real users. Every recommendation comes with a plain-language explanation of exactly which features drove the match, so the logic is fully transparent and inspectable.

---

## 3. How the Model Works

Imagine a judge scoring a gymnastics routine: each competitor earns points for different skills, and the total determines their ranking. VibeFinder works the same way — it scores every song in the catalog and sorts them highest to lowest.

For each song, four questions are asked:

1. **Does the genre match?** If yes, the song earns 2 points. This is the biggest single reward because genre is the broadest signal of what a listener wants — a lofi fan and a metal fan have almost nothing in common.

2. **Does the mood match?** If yes, the song earns 1 point. Mood matters, but the same mood (e.g. "intense") can appear across very different genres, so it carries less weight than genre alone.

3. **How close is the energy?** Every song gets a score between 0 and 1.5 depending on how close its energy level is to what the listener wants. A perfect match gives 1.5 points; the more different, the fewer points.

4. **Does the acoustic character match?** If the listener wants acoustic/organic sound and the song is very acoustic (or vice versa), the song earns 0.5 bonus points.

The total of all four scores is the song's final number. The top 5 songs by total score become the recommendation list. Maximum possible score is 5.0.

---

## 4. Data

The catalog contains **18 songs** stored in `data/songs.csv`. It was expanded from the original 10-song starter dataset. Genres represented include: pop, lofi, rock, ambient, jazz, synthwave, indie pop, r&b, hip-hop, classical, edm, country, metal, soul, and reggae. Moods represented include: happy, chill, intense, relaxed, focused, moody, romantic, euphoric, peaceful, nostalgic, angry, melancholic, and uplifting.

**Gaps in the data:**
- Most genres have only one or two songs. When a user's preferred genre has only one match (e.g. reggae, classical, country), the system can only confirm one obvious #1 pick and must fill the remaining four slots using energy and acoustic similarity alone — which may produce unexpected genre jumps.
- The catalog reflects a particular taste in Western popular music from ~2000–2025. Traditional music, non-English genres, and spoken-word formats are entirely absent.
- Song features were manually assigned, not measured from actual audio. This means the numbers reflect a human's estimate of each song's energy and acousticness, not an objective acoustic analysis.

---

## 5. Strengths

- **Clear profiles work well.** When a user has a strong, consistent preference — such as chill lofi with acoustic sound or high-energy pop — the top results feel intuitively correct. The scoring surfaces the right cluster of songs without any ambiguity.
- **Explainability.** Every result shows exactly which rules contributed points and how many. A user can see why `Gym Hero` ranked above `Iron Curtain` at a glance, rather than getting an opaque black-box recommendation.
- **Genre + energy together separate clusters reliably.** Chill lofi (low energy, acoustic) and intense rock (high energy, electronic) never overlap in the results, even when mood labels conflict.

---

## 6. Limitations and Bias

**No genre adjacency.** The system treats all non-matching genres as equally wrong. For a rock listener, `metal` and `pop` both score zero on the genre rule — but metal is sonically far closer to rock than pop is. This flaw was discovered during testing when `Gym Hero` (pop, mood=intense) consistently outranked `Iron Curtain` (metal, mood=angry) for the "Deep Intense Rock" profile, entirely because of the mood bonus. Reducing the mood weight or doubling the energy weight (both were tested) did not fix this — Gym Hero still won. The only real solution is a genre-adjacency feature, which this system does not have.

**The mood bonus can override sonic reality.** A +1.0 mood bonus is enough to promote a pop song above a metal song when both songs have nearly identical energy proximity to the target. Users asking for "intense rock" are likely thinking about sonic heaviness, not the presence of the word "intense" in a song's tag.

**Filter bubble in the neutral profile.** When no genre or mood preferences are set, the maximum achievable score drops to ~1.6 out of 5.0. The system is so dependent on categorical bonuses that it barely differentiates between songs for users who have not declared strong preferences. In a real product, this would result in poor recommendations for new users who have not yet built a listening history.

**Catalog underrepresentation creates orphaned genres.** Ten of the fifteen genres have exactly one song. This means a user who genuinely loves reggae, classical, or country will get a perfect #1 match and then four near-random fallback songs. The fallbacks are chosen by energy/acoustic proximity, which may jump genres in surprising ways — for example, a reggae fan with high acousticness preference ends up with lofi and jazz in their top 5.

**No repeat-artist filter.** The same artist can appear multiple times in the top 5. In profiles 1 and 6, "Neon Echo" appears twice because two of their songs happen to score well. A real recommender would cap artist repetition to ensure variety.

---

## 7. Evaluation

Six user profiles were tested in total: three standard profiles (High-Energy Pop, Chill Lofi, Deep Intense Rock) and three adversarial profiles (high-energy + melancholic mood conflict, genre orphan, dead-centre neutral with no preferences).

**What matched intuition:**
- High-Energy Pop correctly surfaced `Sunrise City` at a perfect score, then filled the list with energetic, electronic songs.
- Chill Lofi surfaced all three lofi songs in the top three slots, with ambient and jazz filling the remainder — both reasonable choices for a chill listener.
- Deep Intense Rock correctly identified `Storm Runner` as the only full match. The lower ranks also feel acceptable — `Block Party Anthem` and `Drop the Signal` both have rock-adjacent sonic energy even without the genre label.

**What surprised me:**
- In the Deep Intense Rock profile, `Gym Hero` (pop) ranked #2 above `Iron Curtain` (metal, #5). This is the most counterintuitive result. A rock listener would never choose a pop gym-playlist song over a metal track just because both are "intense." The system cannot reason about genre proximity — it only knows match or no match.
- The weight-shift experiment (halving genre to 1.0, doubling energy to 3.0) changed the *margins* but not the *flaw*. Gym Hero still outranked Iron Curtain even with the doubled energy weight, because their energy values are nearly identical (0.93 vs 0.97). This showed that the problem is structural, not fixable by tuning numbers.
- In the neutral profile (no genre/mood set), the maximum score dropped to ~1.6/5.0. This reveals how much the system relies on categorical bonuses. Without genre and mood signals, it is essentially a one-dimensional energy sorter.

**A simple test that confirmed correctness:**
Comparing Profile 1 and Profile 2 results for the same songs: `Library Rain` scores 4.96 for the Chill Lofi profile but would score close to 0 for the High-Energy Pop profile (energy=0.35 vs target=0.82, gap=0.47, energy pts ≈ 0.77; no genre or mood match). This confirms the scoring correctly separates the two clusters.

---

## 8. Future Work

- **Genre adjacency scoring.** Instead of 0/1 for genre match, assign partial credit for sonically similar genres: rock→metal = 1.5 pts, rock→indie = 1.0 pt, rock→pop = 0 pt. This single change would fix the most significant intuition failure identified in testing.
- **Valence as a second numeric feature.** The catalog already has valence (emotional positivity) data that is never used in scoring. Adding `1.0 × (1 - |target_valence - song.valence|)` would help distinguish melancholic from happy songs in profiles where mood labels are absent or conflict with energy.
- **Repeat-artist diversity filter.** Cap each artist at one song per recommendation list to prevent the same artist appearing twice in the top 5.
- **Catalog expansion.** With only one song per genre for most genres, the orphan problem dominates fallback slots. Expanding to 5+ songs per genre would make energy/acoustic proximity meaningful within a genre rather than across unrelated ones.

---

## 9. Personal Reflection

Building this system made the hidden complexity of real-world music recommendations much clearer. What feels like a natural "vibe match" to a listener involves dozens of overlapping signals — and the order in which those signals are weighted changes the answer entirely. The most surprising discovery was that **no amount of weight tuning fixed the Gym Hero problem** — the system needed a new *type* of feature (genre adjacency), not just different numbers on existing features. This is probably true of real recommenders too: adding collaborative filtering to Spotify did not just change the weights, it added a fundamentally different kind of signal. The other key insight is how much categorical bonuses dominate the score. When a user's genre and mood both match, those two rules alone account for 60% of the maximum score — which means the system rewards self-confirming preferences and creates a mild filter bubble even in a tiny 18-song catalog. In a system with millions of songs, that same bias would trap users in tight genre clusters and make genuine discovery unlikely.
