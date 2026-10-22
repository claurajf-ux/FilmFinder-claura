import os
import requests
import streamlit as st

API_BASE = "https://api.themoviedb.org/3"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

GENRES = {
    "Semua Genre": None,
    "Aksi": 28, "Petualangan": 12, "Animasi": 16, "Komedi": 35,
    "Kriminal": 80, "Dokumenter": 99, "Drama": 18, "Keluarga": 10751,
    "Fantasi": 14, "Sejarah": 36, "Horor": 27, "Musik": 10402,
    "Misteri": 9648, "Romantis": 10749, "Fiksi Ilmiah": 878,
    "Film TV": 10770, "Thriller": 53, "Perang": 10752, "Western": 37,
}

st.set_page_config(page_title="FilmFinder | by Claura", page_icon="🎬", layout="wide")

st.markdown("""
<style>
.stApp { background: #fff0f6; color: #583344; }
.block-container { padding-top: 1.8rem; }
.hero {
  background: linear-gradient(120deg, #b83270, #e75480);
  padding: 1.6rem 1.8rem; border-radius: 22px; color: white; margin-bottom: 1rem;
}
.hero h1 { color: white; margin: 0; font-size: 2.5rem; }
.hero p { color: #ffe1ee; margin-bottom: 0; }
div.stButton > button {
  background: #e75480; color: white; border: 0; border-radius: 12px;
  padding: .55rem 1.2rem; font-weight: 700;
}
div.stButton > button:hover { background: #b83270; color: white; border: 0; }
.movie-card { background: #fffafd; border: 1px solid #f2a7c7; border-radius: 16px; padding: 1rem; }
.small { color: #9b5475; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>♡ 🎬 FILMFINDER</h1>
  <p>Temukan film Indonesia dan internasional berdasarkan judul dan genre.</p>
  <p><b>by Claura Jasmine Frizzcaren</b> · Happy Movie, Happy You ♡</p>
</div>
""", unsafe_allow_html=True)

def get_token():
    token = os.getenv("TMDB_READ_ACCESS_TOKEN", "")
    try:
        if not token and "TMDB_READ_ACCESS_TOKEN" in st.secrets:
            token = st.secrets["TMDB_READ_ACCESS_TOKEN"]
    except Exception:
        pass
    return token.strip()

token = get_token()
if not token:
    st.warning("Website ini memerlukan TMDB Read Access Token agar pencarian film bisa berjalan.")
    st.markdown("Pemilik website: tambahkan token sebagai **Secret** bernama `TMDB_READ_ACCESS_TOKEN` di pengaturan hosting. Jangan unggah token ke GitHub atau bagikan di halaman publik.")
    with st.expander("Saya hanya ingin mencoba sendiri"):
        entered = st.text_input("TMDB Read Access Token", type="password")
        if entered:
            st.session_state["temporary_token"] = entered.strip()
    token = st.session_state.get("temporary_token", "")

with st.container():
    c1, c2 = st.columns(2)
    with c1:
        country = st.selectbox("🌏 Wilayah film", ["Semua", "Indonesia", "Internasional"])
    with c2:
        genre_name = st.selectbox("🎞️ Genre", list(GENRES.keys()))
    query = st.text_input("🔎 Judul film", placeholder="Contoh: Agak Laen, Inside Out...")
    search = st.button("♡ Cari Film ♡", use_container_width=True)
    reset = st.button("Reset filter", use_container_width=True)

if reset:
    st.session_state.pop("movies", None)
    st.session_state.pop("selected_movie_id", None)
    st.rerun()

if search:
    if not token:
        st.error("Token TMDB belum tersedia. Pemilik website perlu mengatur secret TMDB_READ_ACCESS_TOKEN.")
    else:
        headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
        params = {"language": "id-ID", "include_adult": "false", "page": 1}
        if query.strip():
            endpoint = API_BASE + "/search/movie"
            params["query"] = query.strip()
        else:
            endpoint = API_BASE + "/discover/movie"
            params["sort_by"] = "popularity.desc"
            genre_id = GENRES.get(genre_name)
            if genre_id:
                params["with_genres"] = genre_id
            if country == "Indonesia":
                params["with_original_language"] = "id"
            elif country == "Internasional":
                params["without_original_language"] = "id"
        try:
            with st.spinner("Sedang mencari film..."):
                response = requests.get(endpoint, headers=headers, params=params, timeout=20)
                if response.status_code in (401, 403):
                    st.error("Token TMDB tidak valid atau belum memiliki akses. Periksa pengaturan token.")
                    st.stop()
                response.raise_for_status()
                movies = response.json().get("results", [])
            if query.strip() and country == "Indonesia":
                movies = [m for m in movies if m.get("original_language") == "id"]
            elif query.strip() and country == "Internasional":
                movies = [m for m in movies if m.get("original_language") != "id"]
            genre_id = GENRES.get(genre_name)
            if genre_id:
                movies = [m for m in movies if genre_id in m.get("genre_ids", [])]
            st.session_state["movies"] = movies
            st.session_state["selected_movie_id"] = movies[0]["id"] if movies else None
        except requests.RequestException:
            st.error("Tidak dapat terhubung ke TMDB. Periksa koneksi internet dan coba lagi.")

movies = st.session_state.get("movies", [])
if movies:
    st.success(f"Ditemukan {len(movies)} film. Pilih film untuk melihat poster dan sinopsis.")
    titles = {}
    for m in movies:
        title = m.get("title") or m.get("original_title") or "Tanpa judul"
        year = (m.get("release_date") or "")[:4] or "—"
        rating = m.get("vote_average")
        rating_text = f"{rating:.1f}/10" if isinstance(rating, (int, float)) else "—"
        titles[f"{title} ({year}) · ⭐ {rating_text}"] = m
    labels = list(titles.keys())
    current_id = st.session_state.get("selected_movie_id")
    default_idx = next((i for i, label in enumerate(labels) if titles[label].get("id") == current_id), 0)
    selected_label = st.selectbox("Pilih film dari hasil pencarian", labels, index=default_idx)
    movie = titles[selected_label]
    st.session_state["selected_movie_id"] = movie.get("id")
    left, right = st.columns([1, 2], gap="large")
    with left:
        poster_path = movie.get("poster_path")
        if poster_path:
            st.image(IMAGE_BASE + poster_path, use_container_width=True)
        else:
            st.info("Poster belum tersedia.")
    with right:
        st.markdown(f"## {movie.get('title') or movie.get('original_title') or 'Tanpa judul'}")
        year = (movie.get("release_date") or "")[:4] or "Tahun tidak diketahui"
        rating = movie.get("vote_average")
        votes = movie.get("vote_count", 0)
        rating_text = f"{rating:.1f}/10 ({votes:,} suara)" if isinstance(rating, (int, float)) else "Belum ada rating"
        st.write(f"**Tahun:** {year}")
        st.write(f"**Rating TMDB:** {rating_text}")
        st.write(f"**Bahasa asli:** {movie.get('original_language', '—').upper()}")
        st.markdown("### SINOPSIS")
        st.write(movie.get("overview") or "Sinopsis belum tersedia dalam bahasa Indonesia.")
        if movie.get("id"):
            st.link_button("Buka halaman film di TMDB", f"https://www.themoviedb.org/movie/{movie['id']}")
elif "movies" in st.session_state:
    st.info("Belum ada hasil. Coba judul atau filter lain.")

st.markdown("---")
st.caption("FilmFinder by Claura ♡ · Data film dan poster disediakan oleh TMDB. FilmFinder bukan layanan streaming.")
st.caption("Catatan: penggunaan TMDB API harus mengikuti ketentuan dan atribusi TMDB.")
