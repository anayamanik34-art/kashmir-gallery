"""Kashmir illustration gallery.

Run with:  streamlit run gallery.py
(or double-click run_gallery.bat)
"""

import io
import json
import re
from pathlib import Path

import streamlit as st
from PIL import Image

ROOT = Path(__file__).parent
LISTINGS = ROOT / "eksochanalytics-listings"

# Each collection is a name, a description and one or more file patterns
# (relative to this folder). Add an entry here to show more images in the app.
COLLECTIONS = {
    "Kashmir Illustrations": (
        "Ten scenes of Kashmiri life: shikaras, chinars, kahwa and more.",
        ["eksochanalytics-listings/illustrations-pack/files/*"],
    ),
    "Kashmiri Henna": (
        "Mehndi designs drawn from Kashmiri motifs.",
        ["eksochanalytics-listings/henna-pack/files/PNG/*"],
    ),
    "Rangoli": (
        "Circular rangoli patterns inspired by the valley.",
        ["kashmir/rangoli/*"],
    ),
    "Stickers": (
        "Print-then-cut stickers from the Kashmir bundle.",
        ["eksochanalytics-listings/kashmir-bundle/files/3-Bookmarks-Gift-Tags-Stickers"
         "/Cricut-Print-Then-Cut/Individual-Stickers-PNG/*"],
    ),
    "Shop Photos & Logo": (
        "Shop cover, banners, process photos and the logo.",
        ["eksochanalytics-photos/*.png", "eksochanalytics-logo/*.png"],
    ),
}
ALL = "All collections"

# Online mode: export_online.py copies this file next to a "previews" folder of
# small, low-resolution copies. Then the app shows only those, with no downloads.
ONLINE_INFO = ROOT / "previews" / "collections.json"
ONLINE = ONLINE_INFO.exists()
SHOP_URL = ""
if ONLINE:
    info = json.loads(ONLINE_INFO.read_text(encoding="utf-8"))
    SHOP_URL = info.get("shop_url", "")
    COLLECTIONS = {
        name: (c["description"], [f"previews/{c['folder']}/*"])
        for name, c in info["collections"].items()
    }

IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".webp", ".svg"}


def nice_title(path: Path) -> str:
    """'Kashmir-Illustration-01-Shikara-on-Dal-Lake.png' -> '01 · Shikara on Dal Lake'."""
    match = re.match(r"^(?:.*?-)?(\d{1,3})-(.+)$", path.stem)
    if match:
        number, name = match.groups()
        return f"{number} · {pretty(name)}"
    return pretty(path.stem)


SMALL_WORDS = {"a", "an", "and", "at", "in", "of", "on", "the", "to"}


def pretty(name: str) -> str:
    words = name.replace("-", " ").split()
    return " ".join(
        w.lower() if i and w.lower() in SMALL_WORDS else w[:1].upper() + w[1:]
        for i, w in enumerate(words)
    )


def list_images(collection: str) -> list[Path]:
    if collection == ALL:
        return [p for name in COLLECTIONS for p in list_images(name)]
    found = []
    for pattern in COLLECTIONS[collection][1]:
        found += sorted(p for p in ROOT.glob(pattern) if p.suffix.lower() in IMAGE_TYPES)
    return found


@st.cache_data(show_spinner=False)
def resized(path_str: str, mtime: float, max_side: int) -> bytes:
    """A smaller PNG copy so big print files load quickly. mtime busts the cache."""
    with Image.open(path_str) as img:
        img.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()


@st.cache_data(show_spinner=False)
def image_size(path_str: str, mtime: float) -> tuple[int, int]:
    with Image.open(path_str) as img:
        return img.size


def show(path: Path, max_side: int) -> None:
    if path.suffix.lower() == ".svg":
        st.image(path.read_text(encoding="utf-8"), width="stretch")
    else:
        st.image(resized(str(path), path.stat().st_mtime, max_side), width="stretch")


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


@st.dialog("Preview", width="large")
def preview(path: Path) -> None:
    st.subheader(nice_title(path))
    show(path, 1600)
    if ONLINE:
        note = "Low-resolution preview. Full-resolution files are available in the shop."
        st.caption(note)
        if SHOP_URL:
            st.link_button("Visit the shop", SHOP_URL, width="stretch", type="primary")
        return
    details = [path.suffix[1:].upper(), human_size(path.stat().st_size)]
    if path.suffix.lower() != ".svg":
        w, h = image_size(str(path), path.stat().st_mtime)
        details.insert(1, f"{w} × {h} px")
    st.caption(" · ".join(details) + f"  \n`{path.relative_to(ROOT)}`")
    st.download_button(
        "Download original", path.read_bytes(), file_name=path.name,
        width="stretch", type="primary",
    )


# ---------------------------------------------------------------- page

st.set_page_config(page_title="Kashmir Gallery", page_icon="🎨", layout="wide")

st.markdown(
    """
    <style>
      [data-testid="stImage"] img { border-radius: 10px; background: #fff; }
      [data-testid="stVerticalBlockBorderWrapper"] { height: 100%; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("🎨 Kashmir Gallery")
    collection = st.radio(
        "Collection",
        [ALL, *COLLECTIONS],
        format_func=lambda name: f"{name}  ({len(list_images(name))})",
    )
    query = st.text_input("Search", placeholder="e.g. chinar, lotus, shikara")
    columns = st.slider("Images per row", 2, 6, 4)
    if ONLINE and SHOP_URL:
        st.link_button("🛍️ Visit the shop", SHOP_URL, width="stretch")

# Each item is (image path, the collection it belongs to).
names = list(COLLECTIONS) if collection == ALL else [collection]
items = [(p, name) for name in names for p in list_images(name)]
if query:
    q = query.lower()
    items = [(p, name) for p, name in items
             if q in nice_title(p).lower() or q in name.lower()]

description = (f"Everything from all {len(COLLECTIONS)} collections."
               if collection == ALL else COLLECTIONS[collection][0])
st.header(collection)
st.caption(f"{description} · {len(items)} image{'s' if len(items) != 1 else ''}")

if not items:
    st.info("No images match your search." if query else "No images found.")

for start in range(0, len(items), columns):
    row = st.columns(columns)
    for col, (path, name) in zip(row, items[start:start + columns]):
        with col, st.container(border=True):
            show(path, 600)
            st.markdown(f"**{nice_title(path)}**")
            if collection == ALL:
                st.caption(name)
            if st.button("View", key=f"view-{path}", width="stretch"):
                preview(path)
