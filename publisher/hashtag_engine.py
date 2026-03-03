"""HashtagEngine generates genre-specific and universal hashtag sets."""

HASHTAGS_PER_POST = 15

UNIVERSAL_HASHTAGS = [
    "#shorts",
    "#viral",
    "#trending",
    "#fyp",
    "#reels",
]

GENRE_HASHTAG_MAP: dict[str, list[str]] = {
    "fitness": [
        "#fitness", "#workout", "#gym", "#health", "#fit",
        "#motivation", "#exercise", "#training", "#gains", "#fitlife",
    ],
    "personalfinance": [
        "#personalfinance", "#money", "#investing", "#finance", "#wealth",
        "#savings", "#financialfreedom", "#moneymatters", "#budgeting", "#stockmarket",
    ],
    "tech": [
        "#tech", "#technology", "#ai", "#coding", "#programming",
        "#software", "#innovation", "#gadgets", "#developer", "#startup",
    ],
    "food": [
        "#food", "#recipe", "#cooking", "#foodie", "#easyrecipe",
        "#homecooking", "#mealprep", "#delicious", "#foodlover", "#instafood",
    ],
    "travel": [
        "#travel", "#wanderlust", "#adventure", "#explore", "#travelgram",
        "#vacation", "#trip", "#travelblogger", "#instatravel", "#bucketlist",
    ],
}

DEFAULT_GENRE_HASHTAGS = [
    "#content", "#creator", "#video", "#watch", "#learn",
    "#tips", "#lifestyle", "#daily", "#inspiration", "#knowledge",
]


class HashtagEngine:
    """Generates a curated set of hashtags for a given content genre."""

    def generate(self, genre: str) -> list[str]:
        """Return a list of genre-specific and universal hashtags.

        Args:
            genre: Content category (e.g. "fitness", "tech").

        Returns:
            List of up to HASHTAGS_PER_POST hashtag strings.
        """
        genre_specific = GENRE_HASHTAG_MAP.get(genre.lower(), DEFAULT_GENRE_HASHTAGS)
        combined = genre_specific + UNIVERSAL_HASHTAGS
        return combined[:HASHTAGS_PER_POST]
