import streamlit as st
import requests
from datetime import date, timedelta

st.set_page_config(
    page_title="CineMatch",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

TMDB_TOKEN = st.secrets["TMDB_TOKEN"]

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_URL = "https://image.tmdb.org/t/p/w500"


def tmdb_get(endpoint, params=None):
    headers = {
        "Authorization": f"Bearer {TMDB_TOKEN}",
        "accept": "application/json"
    }

    try:
        response = requests.get(
            BASE_URL + endpoint,
            headers=headers,
            params=params or {},
            timeout=15
        )

        if response.status_code != 200:
            return {
                "error": f"TMDB Error {response.status_code}"
            }

        return response.json()

    except requests.exceptions.RequestException:
        return {
            "error": "Koneksi ke TMDB gagal"
        }


def poster_url(path):
    if path:
        return IMAGE_URL + path

    return "https://placehold.co/500x750?text=No+Poster"


def normalize_item(item, media_type=None):
    item = dict(item)

    if media_type:
        item["media_type"] = media_type

    if "media_type" not in item:
        if "title" in item:
            item["media_type"] = "movie"
        elif "name" in item:
            item["media_type"] = "tv"

    if item.get("media_type") == "movie":
        item["display_title"] = item.get(
            "title",
            "Tanpa Judul"
        )
        item["release_date"] = item.get(
            "release_date",
            ""
        )
    else:
        item["display_title"] = item.get(
            "name",
            "Tanpa Judul"
        )
        item["release_date"] = item.get(
            "first_air_date",
            ""
        )

    return item


def unique_items(items):
    seen = set()
    result = []

    for item in items:
        key = (
            item.get("media_type"),
            item.get("id")
        )

        if key not in seen:
            seen.add(key)
            result.append(item)

    return result


@st.cache_data(ttl=1800)
def search_tmdb(query):
    movie_data = tmdb_get(
        "/search/movie",
        {
            "query": query,
            "language": "id-ID",
            "include_adult": False,
            "page": 1
        }
    )

    tv_data = tmdb_get(
        "/search/tv",
        {
            "query": query,
            "language": "id-ID",
            "include_adult": False,
            "page": 1
        }
    )

    results = []

    for item in movie_data.get("results", []):
        if item.get("poster_path"):
            results.append(
                normalize_item(item, "movie")
            )

    for item in tv_data.get("results", []):
        if item.get("poster_path"):
            results.append(
                normalize_item(item, "tv")
            )

    return unique_items(results)


@st.cache_data(ttl=1800)
def discover_movies(
    pages=3,
    sort_by="popularity.desc",
    genre=None,
    origin_country=None,
    original_language=None,
    date_gte=None,
    date_lte=None
):
    results = []

    for page in range(1, pages + 1):
        params = {
            "language": "id-ID",
            "page": page,
            "sort_by": sort_by,
            "include_adult": False,
            "include_video": False
        }

        if genre:
            params["with_genres"] = genre

        if origin_country:
            params["with_origin_country"] = origin_country

        if original_language:
            params["with_original_language"] = original_language

        if date_gte:
            params["primary_release_date.gte"] = date_gte

        if date_lte:
            params["primary_release_date.lte"] = date_lte

        data = tmdb_get(
            "/discover/movie",
            params
        )

        for item in data.get("results", []):
            if item.get("poster_path"):
                results.append(
                    normalize_item(
                        item,
                        "movie"
                    )
                )

    return unique_items(results)


@st.cache_data(ttl=1800)
def discover_tv(
    pages=3,
    sort_by="popularity.desc",
    genre=None,
    origin_country=None,
    original_language=None,
    date_gte=None,
    date_lte=None
):
    results = []

    for page in range(1, pages + 1):
        params = {
            "language": "id-ID",
            "page": page,
            "sort_by": sort_by,
            "include_adult": False
        }

        if genre:
            params["with_genres"] = genre

        if origin_country:
            params["with_origin_country"] = origin_country

        if original_language:
            params["with_original_language"] = original_language

        if date_gte:
            params["first_air_date.gte"] = date_gte

        if date_lte:
            params["first_air_date.lte"] = date_lte

        data = tmdb_get(
            "/discover/tv",
            params
        )

        for item in data.get("results", []):
            if item.get("poster_path"):
                results.append(
                    normalize_item(
                        item,
                        "tv"
                    )
                )

    return unique_items(results)


@st.cache_data(ttl=1800)
def get_trending():
    data = tmdb_get(
        "/trending/all/week",
        {
            "language": "id-ID"
        }
    )

    results = []

    for item in data.get("results", []):
        if item.get("media_type") in ["movie", "tv"]:
            if item.get("poster_path"):
                results.append(
                    normalize_item(item)
                )

    return unique_items(results)


@st.cache_data(ttl=1800)
def get_details(media_type, item_id):
    return tmdb_get(
        f"/{media_type}/{item_id}",
        {
            "language": "id-ID",
            "append_to_response": "credits,videos"
        }
    )


def latest_movies():
    today = date.today()
    start = today - timedelta(days=365)

    return discover_movies(
        pages=5,
        sort_by="primary_release_date.desc",
        date_gte=start.isoformat(),
        date_lte=today.isoformat()
    )


def latest_tv():
    today = date.today()
    start = today - timedelta(days=365)

    return discover_tv(
        pages=5,
        sort_by="first_air_date.desc",
        date_gte=start.isoformat(),
        date_lte=today.isoformat()
    )


def latest_indonesia():
    today = date.today()
    start = today - timedelta(days=365)

    return discover_movies(
        pages=5,
        sort_by="primary_release_date.desc",
        origin_country="ID",
        date_gte=start.isoformat(),
        date_lte=today.isoformat()
    )


def popular_indonesia():
    return discover_movies(
        pages=5,
        sort_by="popularity.desc",
        origin_country="ID"
    )


def latest_horror_indonesia():
    today = date.today()
    start = today - timedelta(days=730)

    return discover_movies(
        pages=5,
        sort_by="primary_release_date.desc",
        genre="27",
        origin_country="ID",
        date_gte=start.isoformat(),
        date_lte=today.isoformat()
    )


def popular_horror_indonesia():
    return discover_movies(
        pages=5,
        sort_by="popularity.desc",
        genre="27",
        origin_country="ID"
    )


def latest_kdrama():
    today = date.today()
    start = today - timedelta(days=365)

    return discover_tv(
        pages=5,
        sort_by="first_air_date.desc",
        origin_country="KR",
        original_language="ko",
        date_gte=start.isoformat(),
        date_lte=today.isoformat()
    )


def popular_kdrama():
    return discover_tv(
        pages=5,
        sort_by="popularity.desc",
        origin_country="KR",
        original_language="ko"
    )


def latest_dracin():
    today = date.today()
    start = today - timedelta(days=365)

    return discover_tv(
        pages=5,
        sort_by="first_air_date.desc",
        origin_country="CN",
        original_language="zh",
        date_gte=start.isoformat(),
        date_lte=today.isoformat()
    )


def popular_dracin():
    return discover_tv(
        pages=5,
        sort_by="popularity.desc",
        origin_country="CN",
        original_language="zh"
    )


def latest_horror():
    today = date.today()
    start = today - timedelta(days=365)

    return discover_movies(
        pages=5,
        sort_by="primary_release_date.desc",
        genre="27",
        date_gte=start.isoformat(),
        date_lte=today.isoformat()
    )


def popular_horror():
    return discover_movies(
        pages=5,
        sort_by="popularity.desc",
        genre="27"
    )


def action_movies():
    return discover_movies(
        pages=5,
        sort_by="popularity.desc",
        genre="28"
    )


def romance_movies():
    return discover_movies(
        pages=5,
        sort_by="popularity.desc",
        genre="10749"
    )


def comedy_movies():
    return discover_movies(
        pages=5,
        sort_by="popularity.desc",
        genre="35"
    )


def search_category(query):
    q = query.lower().strip()

    if q in [
        "indonesia",
        "film indonesia",
        "film indo"
    ]:
        return discover_movies(
            pages=5,
            sort_by="popularity.desc",
            origin_country="ID"
        )

    if q in [
        "horor indonesia",
        "horror indonesia",
        "horor indo",
        "horror indo"
    ]:
        return discover_movies(
            pages=5,
            sort_by="popularity.desc",
            genre="27",
            origin_country="ID"
        )

    if q in [
        "horor",
        "horror",
        "film horor",
        "film horror"
    ]:
        return popular_horror()

    if q in [
        "drakor",
        "kdrama",
        "k-drama",
        "korea",
        "drama korea"
    ]:
        return popular_kdrama()

    if q in [
        "dracin",
        "cdrama",
        "c-drama",
        "drama china",
        "chinese drama"
    ]:
        return popular_dracin()

    if q in [
        "action",
        "aksi",
        "film action"
    ]:
        return action_movies()

    if q in [
        "romance",
        "romantis",
        "film romance"
    ]:
        return romance_movies()

    if q in [
        "comedy",
        "komedi",
        "film comedy"
    ]:
        return comedy_movies()

    if q in [
        "thriller",
        "film thriller"
    ]:
        return discover_movies(
            pages=5,
            sort_by="popularity.desc",
            genre="53"
        )

    if q == "anime":
        return discover_tv(
            pages=5,
            sort_by="popularity.desc",
            original_language="ja"
        )

    return search_tmdb(query)


def show_movies(items, title, max_items=12):
    if not items:
        return

    items = items[:max_items]

    st.markdown(
        f'<div class="row-title">{title}</div>',
        unsafe_allow_html=True
    )

    cols = st.columns(
        min(6, len(items))
    )

    for index, item in enumerate(items):

        with cols[index % len(cols)]:

            st.image(
                poster_url(
                    item.get("poster_path")
                ),
                use_container_width=True
            )

            movie_title = item.get(
                "display_title",
                "Tanpa Judul"
            )

            if len(movie_title) > 22:
                movie_title = (
                    movie_title[:22] + "..."
                )

            rating = item.get(
                "vote_average",
                0
            )

            release = item.get(
                "release_date",
                ""
            )

            year = (
                release[:4]
                if release
                else ""
            )

            st.markdown(
                f"""
                <div class="poster-title">
                    {movie_title}
                </div>
                <div class="poster-meta">
                    ⭐ {rating:.1f}
                    {" • " + year if year else ""}
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                "Detail",
                key=(
                    f"{item.get('media_type')}_"
                    f"{item.get('id')}_"
                    f"{title}_{index}"
                ),
                use_container_width=True
            ):
                st.session_state[
                    "selected_item"
                ] = item

                st.rerun()


def show_detail(item):
    if not item:
        return

    st.divider()

    media_type = item.get(
        "media_type"
    )

    item_id = item.get("id")

    details = get_details(
        media_type,
        item_id
    )

    if not details or "error" in details:
        st.error(
            "Detail film tidak dapat dimuat."
        )
        return

    col1, col2 = st.columns(
        [1, 2],
        gap="large"
    )

    with col1:
        st.image(
            poster_url(
                details.get("poster_path")
            ),
            use_container_width=True
        )

    with col2:

        title = (
            details.get("title")
            if media_type == "movie"
            else details.get("name")
        )

        st.markdown(
            f"# {title or 'Tanpa Judul'}"
        )

        rating = details.get(
            "vote_average",
            0
        )

        if rating:
            st.write(
                f"⭐ **Rating:** {rating:.1f}/10"
            )

        release = (
            details.get("release_date", "")
            if media_type == "movie"
            else details.get("first_air_date", "")
        )

        if release:
            st.write(
                f"📅 **Tahun:** {release[:4]}"
            )

        genres = details.get(
            "genres",
            []
        )

        if genres:
            names = [
                genre.get("name", "")
                for genre in genres
            ]

            st.write(
                "🎭 **Genre:** " +
                ", ".join(names)
            )

        countries = details.get(
            "production_countries",
            []
        )

        if countries:
            names = [
                country.get("name", "")
                for country in countries
            ]

            st.write(
                "🌎 **Negara:** " +
                ", ".join(names)
            )

        overview = details.get(
            "overview"
        )

        if overview:
            st.markdown("### 📝 Sinopsis")
            st.write(overview)

        if st.button(
            "✖ Tutup Detail",
            use_container_width=True
        ):
            st.session_state[
                "selected_item"
            ] = None

            st.rerun()


st.markdown(
    """
    <style>

    .stApp {
        background: #080808;
        color: white;
    }

    [data-testid="stSidebar"] {
        background: #0d0d0d;
        border-right: 1px solid #222;
    }

    .brand {
        font-size: 28px;
        font-weight: 800;
        color: #e50914;
        margin-bottom: 20px;
    }

    .hero {
        min-height: 360px;
        padding: 55px 45px;
        margin-bottom: 35px;
        border-radius: 18px;
        background:
            linear-gradient(
                90deg,
                rgba(0,0,0,0.96),
                rgba(0,0,0,0.65),
                rgba(0,0,0,0.15)
            ),
            radial-gradient(
                circle at 75% 35%,
                #55205c,
                #151515 55%,
                #080808
            );
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .hero h1 {
        font-size: 52px;
        margin: 0;
        color: white;
        font-weight: 900;
    }

    .hero p {
        color: #c8c8c8;
        font-size: 17px;
        max-width: 620px;
        line-height: 1.6;
    }

    .search-title {
        font-size: 25px;
        font-weight: 700;
        margin-bottom: 12px;
    }

    .row-title {
        font-size: 23px;
        font-weight: 750;
        color: white;
        margin-top: 28px;
        margin-bottom: 14px;
    }

    .poster-title {
        color: white;
        font-size: 14px;
        font-weight: 650;
        line-height: 1.3;
        margin-top: 7px;
    }

    .poster-meta {
        color: #999;
        font-size: 12px;
        margin-top: 4px;
        margin-bottom: 7px;
    }

    div[data-testid="stImage"] img {
        border-radius: 8px;
    }

    div.stButton > button {
        background: #181818;
        color: white;
        border: 1px solid #333;
        border-radius: 6px;
        font-size: 12px;
        min-height: 32px;
    }

    div.stButton > button:hover {
        background: #e50914;
        border-color: #e50914;
        color: white;
    }

    .login-page {
        max-width: 520px;
        margin: 80px auto;
        text-align: center;
    }

    .login-logo {
        color: #e50914;
        font-size: 48px;
        font-weight: 900;
    }

    .login-text {
        color: #aaa;
        margin-bottom: 30px;
    }

    @media (max-width: 768px) {

        .hero {
            min-height: 260px;
            padding: 30px 22px;
            border-radius: 12px;
        }

        .hero h1 {
            font-size: 34px;
        }

        .hero p {
            font-size: 14px;
        }

        .row-title {
            font-size: 19px;
        }

        .poster-title {
            font-size: 11px;
        }

        .poster-meta {
            font-size: 10px;
        }

        div.stButton > button {
            font-size: 10px;
            padding: 3px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True
)


if not st.user.is_logged_in:

    st.markdown(
        """
        <div class="login-page">
            <div class="login-logo">
                🎬 CineMatch
            </div>

            <h1 style="color:white;">
                Selamat Datang
            </h1>

            <div class="login-text">
                Masuk untuk menemukan film dan
                series favoritmu.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        if st.button(
            "🔵  Masuk dengan Google",
            use_container_width=True
        ):
            st.login("google")

    st.stop()


user_name = st.user.get(
    "name",
    "Pengguna"
)

user_email = st.user.get(
    "email",
    ""
)


with st.sidebar:

    st.markdown(
        """
        <div class="brand">
            🎬 CineMatch
        </div>
        """,
        unsafe_allow_html=True
    )

    st.caption(
        f"👤 {user_name}"
    )

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

    st.divider()

    if st.button(
        "🚪 Keluar",
        use_container_width=True
    ):
        st.logout()


if menu == "Home":

    st.markdown(
        f"""
        <div class="hero">
            <h1>🎬 CineMatch</h1>
            <p>
                Halo, {user_name} 👋
                Temukan film dan series yang
                cocok untuk kamu malam ini.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="search-title">🔎 Mau nonton apa?</div>',
        unsafe_allow_html=True
    )

    search_col1, search_col2 = st.columns(
        [5, 1]
    )

    with search_col1:
        home_query = st.text_input(
            "Cari",
            placeholder="Cari film, series, drakor, dracin...",
            label_visibility="collapsed"
        )

    with search_col2:
        home_search = st.button(
            "🔍 Cari",
            use_container_width=True
        )

    if home_search and home_query.strip():

        with st.spinner("Mencari..."):
            results = search_category(
                home_query
            )

        if results:
            show_movies(
                results,
                f"Hasil: {home_query}",
                12
            )
        else:
            st.warning(
                "Film atau series tidak ditemukan."
            )

    else:

        show_movies(
            get_trending(),
            "🔥 Trending Minggu Ini",
            12
        )

        show_movies(
            latest_movies(),
            "🆕 Film Terbaru",
            12
        )

        show_movies(
            latest_tv(),
            "📺 Series Terbaru",
            12
        )

        show_movies(
            popular_indonesia(),
            "🇮🇩 Film Indonesia Populer",
            12
        )

        show_movies(
            latest_horror_indonesia(),
            "👻🇮🇩 Horor Indonesia Terbaru",
            12
        )

        show_movies(
            popular_horror(),
            "👻 Horor Internasional",
            12
        )

        show_movies(
            popular_kdrama(),
            "🇰🇷 K-Drama Populer",
            12
        )

        show_movies(
            popular_dracin(),
            "🇨🇳 Dracin Populer",
            12
        )

        show_movies(
            action_movies(),
            "💥 Action",
            12
        )

        show_movies(
            romance_movies(),
            "❤️ Romance",
            12
        )

        show_movies(
            comedy_movies(),
            "😂 Comedy",
            12
        )


elif menu == "Cari Film / Series":

    st.markdown(
        '<div class="search-title">🔎 Cari Film / Series</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(
        [5, 1]
    )

    with col1:
        query = st.text_input(
            "Cari film",
            placeholder="Contoh: KKN di Desa Penari, Avengers, drakor...",
            label_visibility="collapsed"
        )

    with col2:
        search_button = st.button(
            "🔍 Cari",
            use_container_width=True
        )

    if search_button:

        if not query.strip():
            st.warning(
                "Masukkan judul film atau series."
            )

        else:

            with st.spinner("Mencari..."):
                results = search_category(
                    query
                )

            if results:
                show_movies(
                    results,
                    f"🔎 Hasil: {query}",
                    30
                )
            else:
                st.warning(
                    "Film atau series tidak ditemukan."
                )


elif menu == "Film Indonesia":

    st.header("🇮🇩 Film Indonesia")

    tab1, tab2 = st.tabs(
        ["🆕 Terbaru", "🔥 Populer"]
    )

    with tab1:
        show_movies(
            latest_indonesia(),
            "🇮🇩 Film Indonesia Terbaru",
            30
        )

    with tab2:
        show_movies(
            popular_indonesia(),
            "🇮🇩 Film Indonesia Populer",
            30
        )


elif menu == "Horor Indonesia":

    st.header("👻 Horor Indonesia")

    tab1, tab2, tab3 = st.tabs(
        [
            "🆕 Terbaru",
            "🔥 Populer",
            "🌎 Internasional"
        ]
    )

    with tab1:
        show_movies(
            latest_horror_indonesia(),
            "👻🇮🇩 Horor Indonesia Terbaru",
            30
        )

    with tab2:
        show_movies(
            popular_horror_indonesia(),
            "👻🇮🇩 Horor Indonesia Populer",
            30
        )

    with tab3:
        show_movies(
            popular_horror(),
            "👻🌎 Horor Internasional",
            30
        )


elif menu == "K-Drama":

    st.header("🇰🇷 K-Drama")

    tab1, tab2 = st.tabs(
        ["🆕 Terbaru", "🔥 Populer"]
    )

    with tab1:
        show_movies(
            latest_kdrama(),
            "🇰🇷 K-Drama Terbaru",
            30
        )

    with tab2:
        show_movies(
            popular_kdrama(),
            "🇰🇷 K-Drama Populer",
            30
        )


elif menu == "Dracin":

    st.header("🇨🇳 Dracin")

    tab1, tab2 = st.tabs(
        ["🆕 Terbaru", "🔥 Populer"]
    )

    with tab1:
        show_movies(
            latest_dracin(),
            "🇨🇳 Dracin Terbaru",
            30
        )

    with tab2:
        show_movies(
            popular_dracin(),
            "🇨🇳 Dracin Populer",
            30
        )


elif menu == "Genre":

    st.header("🎭 Genre")

    genre = st.selectbox(
        "Pilih genre",
        [
            "Horor",
            "Action",
            "Romance",
            "Comedy",
            "Thriller"
        ]
    )

    if genre == "Horor":
        results = popular_horror()

    elif genre == "Action":
        results = action_movies()

    elif genre == "Romance":
        results = romance_movies()

    elif genre == "Comedy":
        results = comedy_movies()

    else:
        results = discover_movies(
            pages=5,
            sort_by="popularity.desc",
            genre="53"
        )

    show_movies(
        results,
        f"🎭 {genre}",
        30
    )


selected = st.session_state.get(
    "selected_item"
)

if selected:
    show_detail(selected)


st.divider()

st.caption(
    "CineMatch menggunakan TMDB untuk data film, "
    "series, poster, dan informasi terkait."
)