SCHEMAS = {

    # === LINK TABLES (appid → many-to-many) ===
    "application_categories": {
        "appid": int,
        "category_id": int
    },

    "application_developers": {
        "appid": int,
        "developer_id": int
    },

    "application_genres": {
        "appid": int,
        "genre_id": int
    },

    "application_platforms": {
        "appid": int,
        "platform_id": int
    },

    "application_publishers": {
        "appid": int,
        "publisher_id": int
    },

    # === MAIN APPLICATION TABLE ===
    "applications": {
        "appid": int,
        "name": str,
        "type": str,
        "is_free": int,                       # 0 or 1 in dataset
        "release_date": str,                  # keep as string unless you want datetime
        "required_age": int,
        "short_description": str,
        "supported_languages": str,
        "header_image": str,
        "background": str,
        "metacritic_score": int,
        "recommendations_total": int,
        "mat_supports_windows": int,
        "mat_supports_mac": int,
        "mat_supports_linux": int,
        "mat_final_price": float,
        "mat_discount_percent": float,
        "mat_currency": str,
        "created_at": str,
        "updated_at": str
    },

    # === LOOKUP TABLES ===
    "categories": {
        "id": int,
        "name": str
    },
    "genres": {
        "id": int,
        "name": str
    },
    "platforms": {
        "id": int,
        "name": str
    },
    "publishers": {
        "id": int,
        "name": str
    },
    "developers": {
        "id": int,
        "name": str
    },

    # === REVIEWS TABLE ===
    "reviews_final": {
        "review_text": str,
        "recommendationid": int,
        "appid": int,
        "author_steamid": int,
        "author_num_games_owned": int,
        "author_num_reviews": int,
        "language": str,
        "timestamp_created": int,
        "timestamp_updated": int,
        "voted_up": int,
        "votes_up": int,
        "votes_funny": int,
        "weighted_vote_score": float,
        "comment_count": int,
        "steam_purchase": int,
        "received_for_free": int,
        "written_during_early_access": int,
        "created_at": str,
        "updated_at": str
    }
}
