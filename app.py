import streamlit as st
import requests
from datetime import date, timedelta


st.set_page_config(
    page_title="CineMatch",
    page_icon="🎬",
    layout="wide"
)


TMDB_TOKEN = st.secrets["TMDB_TOKEN"]

HEADERS = {
    "Authorization": f"Bearer {TMDB_TOKEN}",
    "accept": "application/json"
}


def tmdb_get(endpoint, params=None):
    url = f"https://api.themoviedb.org/3/{endpoint}"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=15
        )

        if response.status_code == 200:
            return response.json()

        return {}

    except Exception:
        return {}


def get_image(path, size="w500"):
    if not path:
        return "https://via.placeholder.com/500x750?text=No+Poster"

    return f"https://image.tmdb.org/t/p/{size}{path}"


def get_trending():
    data = tmdb_get(
        "trending/all/week",
        {
            "language": "id-ID"
        }
    )

    return data.get("results", [])


def get_popular_movies():
    data = tmdb_get(
        "movie/popular",
        {
            "language": "id-ID",
            "region": "ID"
        }
    )

    return data.get("results", [])


def get_popular_tv():
    data = tmdb_get(
        "tv/popular",
        {
            "language": "id-ID"
        }
    )

    return data.get("results", [])


def get_indonesia_movies():
    data = tmdb_get(
        "discover/movie",
        {
            "with_origin_country": "ID",
            "language": "id-ID",
            "sort_by": "popularity.desc"
        }
    )

    return data.get("results", [])


def get_horror_movies():
    data = tmdb_get(
        "discover/movie",
        {
            "with_genres": "27",
            "language": "id-ID",
            "sort_by": "popularity.desc"
        }
    )

    return data.get("results", [])


def get_korean_drama():
    data = tmdb_get(
        "discover/tv",
        {
            "with_origin_country": "KR",
            "language": "id-ID",
            "sort_by": "popularity.desc"
        }
    )

    return data.get("results", [])


def get_chinese_drama():
    data = tmdb_get(
        "discover/tv",
        {
            "with_origin_country": "CN",
            "language": "id-ID",
            "sort_by": "popularity.desc"
        }
    )

    return data.get("results", [])


def get_genre_movies(genre_id):
    data = tmdb_get(
        "discover/movie",
        {
            "with_genres": genre_id,
            "language": "id-ID",
            "sort_by": "popularity.desc"
        }
    )

    return data.get("results", [])


def search_movies(query):
    movie_data = tmdb_get(
        "search/movie",
        {
            "query": query,
            "language": "id-ID",
            "include_adult": "false"
        }
    )

    tv_data = tmdb_get(
        "search/tv",
        {
            "query": query,
            "language": "id-ID",
            "include_adult": "false"
        }
    )

    movies = movie_data.get("results", [])
    tv = tv_data.get("results", [])

    for item in movies:
        item["media_type"] = "movie"

    for item in tv:
        item["media_type"] = "tv"

    return movies + tv


def get_detail(item):
    media_type = item.get("media_type", "movie")
    item_id = item.get("id")

    if not item_id:
        return {}

    return tmdb_get(
        f"{media_type}/{item_id}",
        {
            "language": "id-ID",
            "append_to_response": "credits,videos"
        }
    )


def get_title(item):
    return item.get("title") or item.get("name") or "Tanpa Judul"


def get_overview(item):
    return item.get("overview") or "Belum ada deskripsi untuk film ini."


def get_rating(item):
    rating = item.get("vote_average")

    if rating:
        return f"{rating:.1f}"

    return "N/A"


def display_movies(items, title, limit=6):
    st.subheader(title)

    if not items:
        st.info("Film tidak ditemukan.")
        return

    items = items[:limit]

    cols = st.columns(len(items))

    for index, item in enumerate(items):
        with cols[index]:
            poster = get_image(
                item.get("poster_path"),
                "w500"
            )

            st.image(
                poster,
                use_container_width=True
            )

            st.markdown(
                f"**{get_title(item)}**"
            )

            st.caption(
                f"⭐ {get_rating(item)}"
            )

            if st.button(
                "Lihat Detail",
                key=f"detail_{title}_{index}_{item.get('id')}",
                use_container_width=True
            ):
                st.session_state["selected_item"] = item
                st.rerun()


def show_detail(item):
    detail = get_detail(item)

    if not detail:
        st.error("Detail film tidak dapat dimuat.")
        return

    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.image(
            get_image(
                detail.get("poster_path"),
                "w500"
            ),
            use_container_width=True
        )

    with col2:
        st.title(get_title(detail))

        rating = detail.get("vote_average")

        if rating:
            st.markdown(
                f"⭐ **{rating:.1f}/10**"
            )

        release_date = (
            detail.get("release_date")
            or detail.get("first_air_date")
        )

        if release_date:
            st.write(
                f"📅 {release_date}"
            )

        genres = detail.get("genres", [])

        if genres:
            genre_names = ", ".join(
                genre["name"]
                for genre in genres
            )

            st.write(
                f"🎭 {genre_names}"
            )

        st.write(
            get_overview(detail)
        )

        credits = detail.get("credits", {})

        cast = credits.get("cast", [])

        if cast:
            cast_names = ", ".join(
                actor.get("name", "")
                for actor in cast[:5]
            )

            st.write(
                f"👥 **Pemeran:** {cast_names}"
            )

        if st.button(
            "← Kembali",
            use_container_width=True
        ):
            st.session_state.pop(
                "selected_item",
                None
            )

            st.rerun()


if not st.user.is_logged_in:

    st.title("🎬 CineMatch")

    st.header("Selamat Datang")

    st.write(
        "Masuk untuk menemukan film dan series favoritmu."
    )

    st.button(
        "🔵 Masuk dengan Google",
        use_container_width=True,
        on_click=st.login
    )

    st.stop()


st.markdown(
    """
    <style>

    .stApp {
        background: #0b0b0b;
    }

    section[data-testid="stSidebar"] {
        background: #111111;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p {
        color: white;
    }

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .main-subtitle {
        color: #aaaaaa;
        font-size: 16px;
        margin-bottom: 25px;
    }

    div[data-testid="stImage"] img {
        border-radius: 10px;
    }

    button {
        border-radius: 8px !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)


user_name = st.user.get(
    "name",
    "Pengguna"
)


with st.sidebar:

    st.markdown(
        "# 🎬 CineMatch"
    )

    st.write(
        f"Halo, **{user_name}** 👋"
    )

    st.markdown("---")

    menu = st.radio(
        "Menu",
        [
            "Home",
            "Cari Film / Series",
            "Film Indonesia",
            "Horor Indonesia",
            "K-Drama",
            "Dracin",
            "Genre"
        ]
    )

    st.markdown("---")

    if st.button(
        "🚪 Keluar",
        use_container_width=True
    ):
        st.logout()


if "selected_item" in st.session_state:

    show_detail(
        st.session_state["selected_item"]
    )

    st.stop()


if menu == "Home":

    st.markdown(
        '<div class="main-title">🎬 CineMatch</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="main-subtitle">Temukan film dan series favoritmu.</div>',
        unsafe_allow_html=True
    )

    trending = get_trending()

    display_movies(
        trending,
        "🔥 Trending Sekarang",
        6
    )

    popular_movies = get_popular_movies()

    display_movies(
        popular_movies,
        "🎥 Film Populer",
        6
    )

    popular_tv = get_popular_tv()

    display_movies(
        popular_tv,
        "📺 Series Populer",
        6
    )

    indonesia = get_indonesia_movies()

    display_movies(
        indonesia,
        "🇮🇩 Film Indonesia",
        6
    )

    horror = get_horror_movies()

    display_movies(
        horror,
        "👻 Horor",
        6
    )

    korean = get_korean_drama()

    display_movies(
        korean,
        "🇰🇷 K-Drama",
        6
    )

    chinese = get_chinese_drama()

    display_movies(
        chinese,
        "🇨🇳 Dracin",
        6
    )


elif menu == "Cari Film / Series":

    st.title("🔎 Cari Film / Series")

    query = st.text_input(
        "Masukkan judul film atau series",
        placeholder="Contoh: Avengers, Squid Game, Titanic..."
    )

    if query:

        results = search_movies(query)

        st.write(
            f"Ditemukan {len(results)} hasil."
        )

        display_movies(
            results,
            "Hasil Pencarian",
            6
        )


elif menu == "Film Indonesia":

    st.title("🇮🇩 Film Indonesia")

    indonesia = get_indonesia_movies()

    display_movies(
        indonesia,
        "Film Indonesia Terpopuler",
        6
    )


elif menu == "Horor Indonesia":

    st.title("👻 Horor Indonesia")

    indonesia_horror = tmdb_get(
        "discover/movie",
        {
            "with_origin_country": "ID",
            "with_genres": "27",
            "language": "id-ID",
            "sort_by": "popularity.desc"
        }
    ).get("results", [])

    display_movies(
        indonesia_horror,
        "Horor Indonesia",
        6
    )


elif menu == "K-Drama":

    st.title("🇰🇷 K-Drama")

    korean = get_korean_drama()

    display_movies(
        korean,
        "K-Drama Populer",
        6
    )


elif menu == "Dracin":

    st.title("🇨🇳 Dracin")

    chinese = get_chinese_drama()

    display_movies(
        chinese,
        "Drama China Populer",
        6
    )


elif menu == "Genre":

    st.title("🎭 Pilih Genre")

    genre_options = {
        "Action": 28,
        "Adventure": 12,
        "Comedy": 35,
        "Drama": 18,
        "Horror": 27,
        "Romance": 10749,
        "Science Fiction": 878,
        "Thriller": 53,
        "Animation": 16
    }

    selected_genre = st.selectbox(
        "Pilih genre",
        list(genre_options.keys())
    )

    genre_movies = get_genre_movies(
        genre_options[selected_genre]
    )

    display_movies(
        genre_movies,
        f"Film {selected_genre}",
        6
    )