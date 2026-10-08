import streamlit as st
import requests
from datetime import date, timedelta
from urllib.parse import quote

st.set_page_config(
    page_title="CineMatch",
    page_icon="🎬",
    layout="wide"
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
                "error": f"TMDB Error {response.status_code}",
                "message": response.text[:500]
            }

        return response.json()

    except requests.exceptions.RequestException as e:
        return {
            "error": "Koneksi ke TMDB gagal",
            "message": str(e)
        }


def poster_url(path):
    if path:
        return IMAGE_URL + path

    return "https://placehold.co/500x750?text=No+Poster"


def normalize_item(item, media_type=None):
    if media_type:
        item["media_type"] = media_type

    if "media_type" not in item:
        if "title" in item:
            item["media_type"] = "movie"
        elif "name" in item:
            item["media_type"] = "tv"

    if item["media_type"] == "movie":
        item["display_title"] = item.get("title", "Tanpa Judul")
        item["release_date"] = item.get("release_date", "")
    else:
        item["display_title"] = item.get("name", "Tanpa Judul")
        item["release_date"] = item.get("first_air_date", "")

    return item


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

    if "results" in movie_data:
        for item in movie_data["results"]:
            if item.get("poster_path"):
                results.append(normalize_item(item, "movie"))

    if "results" in tv_data:
        for item in tv_data["results"]:
            if item.get("poster_path"):
                results.append(normalize_item(item, "tv"))

    return results


@st.cache_data(ttl=1800)
def discover_movies(
    pages=3,
    sort_by="popularity.desc",
    genre=None,
    origin_country=None,
    original_language=None,
    date_gte=None,
    date_lte=None,
    vote_count=0
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

        if vote_count:
            params["vote_count.gte"] = vote_count

        data = tmdb_get("/discover/movie", params)

        if "results" in data:
            for item in data["results"]:
                if item.get("poster_path"):
                    results.append(normalize_item(item, "movie"))

    return unique_items(results)


@st.cache_data(ttl=1800)
def discover_tv(
    pages=3,
    sort_by="popularity.desc",
    genre=None,
    origin_country=None,
    original_language=None,
    date_gte=None,
    date_lte=None,
    vote_count=0
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

        if vote_count:
            params["vote_count.gte"] = vote_count

        data = tmdb_get("/discover/tv", params)

        if "results" in data:
            for item in data["results"]:
                if item.get("poster_path"):
                    results.append(normalize_item(item, "tv"))

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

    if "results" in data:
        for item in data["results"]:
            if item.get("media_type") in ["movie", "tv"]:
                if item.get("poster_path"):
                    results.append(normalize_item(item))

    return results


@st.cache_data(ttl=1800)
def get_details(media_type, item_id):
    data = tmdb_get(
        f"/{media_type}/{item_id}",
        {
            "language": "id-ID",
            "append_to_response": "credits,videos"
        }
    )

    return data


def unique_items(items):
    seen = set()
    output = []

    for item in items:
        key = (
            item.get("media_type"),
            item.get("id")
        )

        if key not in seen:
            seen.add(key)
            output.append(item)

    return output


def display_row(items, title, max_items=12):
    if not items:
        return

    st.markdown(f"### {title}")

    items = items[:max_items]

    columns = st.columns(6)

    for index, item in enumerate(items):
        with columns[index % 6]:
            st.image(
                poster_url(item.get("poster_path")),
                use_container_width=True
            )

            st.markdown(
                f"**{item.get('display_title', 'Tanpa Judul')}**"
            )

            rating = item.get("vote_average", 0)

            if rating:
                st.caption(f"⭐ {rating:.1f}")

            release_date = item.get("release_date", "")

            if release_date:
                st.caption(release_date[:4])

            if st.button(
                "Lihat Detail",
                key=f"detail_{item.get('media_type')}_{item.get('id')}_{title}"
            ):
                st.session_state["selected_item"] = item
                st.rerun()


def search_category(query):
    q = query.lower().strip()

    if q in [
        "indonesia",
        "film indonesia",
        "film indo",
        "film indonesia terbaru"
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
        "horor indonesia terbaru",
        "horror indonesia terbaru"
    ]:
        return discover_movies(
            pages=5,
            sort_by="primary_release_date.desc",
            genre="27",
            origin_country="ID"
        )

    if q in [
        "horor",
        "horror",
        "film horor",
        "film horror"
    ]:
        return discover_movies(
            pages=5,
            sort_by="popularity.desc",
            genre="27"
        )

    if q in [
        "horor terbaru",
        "horror terbaru"
    ]:
        return discover_movies(
            pages=5,
            sort_by="primary_release_date.desc",
            genre="27"
        )

    if q in [
        "korea",
        "drakor",
        "kdrama",
        "k-drama",
        "korean drama",
        "drama korea"
    ]:
        return discover_tv(
            pages=5,
            sort_by="popularity.desc",
            origin_country="KR",
            original_language="ko"
        )

    if q in [
        "drakor terbaru",
        "kdrama terbaru",
        "k-drama terbaru",
        "drama korea terbaru"
    ]:
        return discover_tv(
            pages=5,
            sort_by="first_air_date.desc",
            origin_country="KR",
            original_language="ko"
        )

    if q in [
        "dracin",
        "cdrama",
        "c-drama",
        "chinese drama",
        "china drama",
        "drama china",
        "drama cina",
        "series china"
    ]:
        return discover_tv(
            pages=5,
            sort_by="popularity.desc",
            origin_country="CN",
            original_language="zh"
        )

    if q in [
        "dracin terbaru",
        "cdrama terbaru",
        "chinese drama terbaru",
        "drama china terbaru"
    ]:
        return discover_tv(
            pages=5,
            sort_by="first_air_date.desc",
            origin_country="CN",
            original_language="zh"
        )

    if q in ["action", "aksi", "film action", "film aksi"]:
        return discover_movies(
            pages=5,
            sort_by="popularity.desc",
            genre="28"
        )

    if q in ["romance", "romantis", "film romance", "film romantis"]:
        return discover_movies(
            pages=5,
            sort_by="popularity.desc",
            genre="10749"
        )

    if q in ["comedy", "komedi", "film comedy", "film komedi"]:
        return discover_movies(
            pages=5,
            sort_by="popularity.desc",
            genre="35"
        )

    if q in ["thriller", "film thriller"]:
        return discover_movies(
            pages=5,
            sort_by="popularity.desc",
            genre="53"
        )

    if q in ["anime"]:
        return discover_tv(
            pages=5,
            sort_by="popularity.desc",
            original_language="ja"
        )

    return search_tmdb(query)


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


def popular_tv():
    return discover_tv(
        pages=5,
        sort_by="popularity.desc"
    )


st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b0b0f;
    }

    h1, h2, h3 {
        color: white;
    }

    .movie-title {
        color: white;
        font-size: 16px;
        font-weight: 600;
    }

    .subtitle {
        color: #aaaaaa;
    }

    div[data-testid="stImage"] img {
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.title("🎬 CineMatch")
st.caption("Cari dan temukan film & series favoritmu")


if "selected_item" not in st.session_state:
    st.session_state["selected_item"] = None


with st.sidebar:
    st.header("🎬 CineMatch")

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


if menu == "Home":

    st.markdown("## 🔥 Sedang Populer")

    trending = get_trending()
    display_row(
        trending,
        "🔥 Trending Minggu Ini",
        12
    )

    latest = latest_movies()
    display_row(
        latest,
        "🆕 Film Terbaru",
        12
    )

    latest_tv_results = latest_tv()
    display_row(
        latest_tv_results,
        "📺 Series Terbaru",
        12
    )

    indonesia = latest_indonesia()
    display_row(
        indonesia,
        "🇮🇩 Film Indonesia Terbaru",
        12
    )

    indonesia_popular = popular_indonesia()
    display_row(
        indonesia_popular,
        "🇮🇩 Film Indonesia Populer",
        12
    )

    horror_id = latest_horror_indonesia()
    display_row(
        horror_id,
        "👻🇮🇩 Horor Indonesia Terbaru",
        12
    )

    horror_id_popular = popular_horror_indonesia()
    display_row(
        horror_id_popular,
        "👻🇮🇩 Horor Indonesia Populer",
        12
    )

    horror = latest_horror()
    display_row(
        horror,
        "👻🌎 Horor Internasional Terbaru",
        12
    )

    kdrama = latest_kdrama()
    display_row(
        kdrama,
        "🇰🇷 K-Drama Terbaru",
        12
    )

    kdrama_popular = popular_kdrama()
    display_row(
        kdrama_popular,
        "🇰🇷 K-Drama Populer",
        12
    )

    dracin = latest_dracin()
    display_row(
        dracin,
        "🇨🇳 Dracin Terbaru",
        12
    )

    dracin_popular = popular_dracin()
    display_row(
        dracin_popular,
        "🇨🇳 Dracin Populer",
        12
    )

    action = action_movies()
    display_row(
        action,
        "💥 Action",
        12
    )

    romance = romance_movies()
    display_row(
        romance,
        "❤️ Romance",
        12
    )

    comedy = comedy_movies()
    display_row(
        comedy,
        "😂 Comedy",
        12
    )


elif menu == "Cari Film / Series":

    st.header("🔎 Cari Film / Series")

    query = st.text_input(
        "Masukkan judul atau kategori",
        placeholder="Contoh: KKN di Desa Penari, horor indonesia, drakor, dracin..."
    )

    if query:
        with st.spinner("Mencari..."):
            results = search_category(query)

        if results:
            st.success(f"Ditemukan {len(results)} hasil")

            display_row(
                results,
                f"🔎 Hasil: {query}",
                30
            )

        else:
            st.warning(
                "Film atau series tidak ditemukan."
            )

            st.info(
                "Coba kata kunci seperti: horor indonesia, "
                "film indonesia, drakor, dracin, action, romance."
            )


elif menu == "Film Indonesia":

    st.header("🇮🇩 Film Indonesia")

    tab1, tab2 = st.tabs(
        [
            "🆕 Terbaru",
            "🔥 Populer"
        ]
    )

    with tab1:
        results = latest_indonesia()

        display_row(
            results,
            "🇮🇩 Film Indonesia Terbaru",
            30
        )

    with tab2:
        results = popular_indonesia()

        display_row(
            results,
            "🇮🇩 Film Indonesia Populer",
            30
        )


elif menu == "Horor Indonesia":

    st.header("👻🇮🇩 Horor Indonesia")

    tab1, tab2, tab3 = st.tabs(
        [
            "🆕 Terbaru",
            "🔥 Populer",
            "🌎 Internasional"
        ]
    )

    with tab1:
        results = latest_horror_indonesia()

        display_row(
            results,
            "👻🇮🇩 Horor Indonesia Terbaru",
            30
        )

    with tab2:
        results = popular_horror_indonesia()

        display_row(
            results,
            "👻🇮🇩 Horor Indonesia Populer",
            30
        )

    with tab3:
        results = popular_horror()

        display_row(
            results,
            "👻🌎 Horor Internasional",
            30
        )


elif menu == "K-Drama":

    st.header("🇰🇷 K-Drama")

    tab1, tab2 = st.tabs(
        [
            "🆕 Terbaru",
            "🔥 Populer"
        ]
    )

    with tab1:
        results = latest_kdrama()

        display_row(
            results,
            "🇰🇷 K-Drama Terbaru",
            30
        )

    with tab2:
        results = popular_kdrama()

        display_row(
            results,
            "🇰🇷 K-Drama Populer",
            30
        )


elif menu == "Dracin":

    st.header("🇨🇳 Dracin")

    tab1, tab2 = st.tabs(
        [
            "🆕 Terbaru",
            "🔥 Populer"
        ]
    )

    with tab1:
        results = latest_dracin()

        display_row(
            results,
            "🇨🇳 Dracin Terbaru",
            30
        )

    with tab2:
        results = popular_dracin()

        display_row(
            results,
            "🇨🇳 Dracin Populer",
            30
        )


elif menu == "Genre":

    st.header("🎭 Pilih Genre")

    genre = st.selectbox(
        "Genre",
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

    display_row(
        results,
        f"🎭 {genre}",
        30
    )


selected = st.session_state.get("selected_item")


if selected:

    st.divider()

    st.header("🎬 Detail")

    media_type = selected.get("media_type")
    item_id = selected.get("id")

    details = get_details(
        media_type,
        item_id
    )

    if details and "error" not in details:

        col1, col2 = st.columns(
            [1, 2]
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

            st.subheader(
                title or "Tanpa Judul"
            )

            rating = details.get(
                "vote_average",
                0
            )

            if rating:
                st.write(
                    f"⭐ Rating: {rating:.1f}/10"
                )

            if media_type == "movie":
                release = details.get(
                    "release_date",
                    ""
                )
            else:
                release = details.get(
                    "first_air_date",
                    ""
                )

            if release:
                st.write(
                    f"📅 Tahun: {release[:4]}"
                )

            genres = details.get(
                "genres",
                []
            )

            if genres:
                genre_names = [
                    g["name"]
                    for g in genres
                ]

                st.write(
                    "🎭 Genre: " +
                    ", ".join(genre_names)
                )

            overview = details.get(
                "overview"
            )

            if overview:
                st.write(
                    "📝 " + overview
                )

            countries = details.get(
                "production_countries",
                []
            )

            if countries:
                country_names = [
                    c.get("name", "")
                    for c in countries
                ]

                st.write(
                    "🌎 Negara: " +
                    ", ".join(country_names)
                )

    if st.button("✖ Tutup Detail"):
        st.session_state["selected_item"] = None
        st.rerun()


st.divider()

st.caption(
    "CineMatch menggunakan TMDB untuk data film, series, poster, dan informasi terkait."
)