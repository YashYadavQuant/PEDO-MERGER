import io
import re
import zipfile
from pathlib import Path

import streamlit as st
import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter
from PIL import Image, ImageOps
import streamlit.components.v1 as components

st.set_page_config(page_title="Pedomerger", page_icon="📄", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #f6f7fb; }
.block-container { max-width: 1220px; padding-top: 1.4rem; padding-bottom: 3rem; }
.hero {
  padding: 1.5rem 1.7rem; border-radius: 22px; color: white;
  background: linear-gradient(120deg, #191b2e 0%, #292f52 58%, #493b70 100%);
  margin-bottom: 1.2rem; box-shadow: 0 12px 30px rgba(27,31,57,.12);
}
.hero h1 { font-family: 'Manrope', sans-serif; font-size: 2.45rem; margin: 0; color: white; letter-spacing: -1px; }
.hero p { color: #d9dcef; margin: .45rem 0 0; font-size: 1rem; }
.eyebrow { text-transform: uppercase; letter-spacing: 2px; color: #ffaaa5; font-size: .72rem; font-weight: 800; margin-bottom: .45rem; }
.tool-card {
  background: white; border: 1px solid #e7e9f2; border-radius: 17px;
  padding: 1rem 1.1rem; min-height: 125px; box-shadow: 0 4px 14px rgba(28,35,70,.035);
}
.tool-card h3 { margin: .3rem 0; font-size: 1rem; color: #20243a; }
.tool-card p { margin: 0; color: #70768a; font-size: .86rem; }
.small-muted { color: #73798c; font-size: .86rem; }
.stButton > button, .stDownloadButton > button {
  border-radius: 10px; min-height: 2.7rem; font-weight: 700;
  border: 1px solid #e2e4ed;
}
.stButton > button[kind="primary"] { background: #e5484d; border-color: #e5484d; }
section[data-testid="stFileUploader"] {
  background: #fff; border: 1px dashed #cbd0e1; border-radius: 14px; padding: .35rem;
}
div[data-testid="stTabs"] button { font-weight: 700; }
div[data-testid="stAlert"] { border-radius: 12px; }
hr { border-color: #e6e8f0; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">Your everyday document toolkit</div>
  <h1>📄 Pedomerger</h1>
  <p>Merge PDFs, crop images, convert files and organize pages — all in one place.</p>
</div>
""", unsafe_allow_html=True)

def safe_filename(name: str, default: str = "pedomerger_output") -> str:
    name = (name or "").strip()
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)
    name = re.sub(r"\s+", "_", name).strip("._")
    return name or default

def ensure_ext(name: str, ext: str) -> str:
    name = safe_filename(name)
    if not name.lower().endswith(ext.lower()):
        name += ext
    return name

def uploaded_bytes(file):
    file.seek(0)
    return file.read()

def pdf_page_count(data: bytes) -> int:
    return len(PdfReader(io.BytesIO(data)).pages)

def render_pdf_preview(data: bytes, page_num: int = 0, scale: float = 1.25):
    doc = fitz.open(stream=data, filetype="pdf")
    if not len(doc):
        return None
    page_num = max(0, min(page_num, len(doc) - 1))
    pix = doc[page_num].get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    return Image.open(io.BytesIO(pix.tobytes("png")))

def download_bytes(label: str, data: bytes, filename: str, mime: str):
    st.download_button(label, data=data, file_name=filename, mime=mime, use_container_width=True)

def show_preview_image(image: Image.Image, caption: str = ""):
    st.image(image, caption=caption, use_container_width=True)

with st.sidebar:
    st.markdown("## 🧰 Pedomerger")
    st.caption("PDF & image tools")
    appearance = st.radio(
        "Appearance",
        ["Light mode", "Dark mode"],
        horizontal=True,
        key="pedomerger_appearance",
    )
    dark_mode = appearance == "Dark mode"
    if dark_mode:
        st.markdown("""
        <style>
        .stApp { background: #11131b !important; color: #f2f3f8 !important; }
        [data-testid="stHeader"] { background: rgba(17,19,27,.92) !important; }
        [data-testid="stSidebar"] { background: #191c27 !important; }
        [data-testid="stSidebar"] * { color: #eef0f8 !important; }
        .tool-card { background: #1c2030 !important; border-color: #30364a !important; }
        .tool-card h3 { color: #f5f6fc !important; }
        .tool-card p, .small-muted { color: #b4bbce !important; }
        .stMarkdown, label, p, h1, h2, h3, h4, [data-testid="stWidgetLabel"] { color: #f0f2f8; }
        input, textarea, [data-baseweb="select"] > div, [data-baseweb="input"] > div {
          background: #202536 !important; color: #f4f5fb !important; border-color: #3b4258 !important;
        }
        section[data-testid="stFileUploader"] { background: #1c2030 !important; border-color: #414861 !important; }
        [data-testid="stFileUploader"] * { color: #eef0f8 !important; }
        .stButton > button, .stDownloadButton > button {
          background: #272d40; color: #f4f5fb; border-color: #414861;
        }
        div[data-testid="stTabs"] button { color: #f0f2f8 !important; }
        div[data-testid="stAlert"] { background: #202536 !important; }
        hr { border-color: #30364a !important; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp { background: #f6f7fb !important; color: #20243a !important; }
        [data-testid="stSidebar"] { background: #ffffff !important; }
        .tool-card { background: #ffffff !important; border-color: #e7e9f2 !important; }
        .tool-card h3 { color: #20243a !important; }
        .tool-card p, .small-muted { color: #70768a !important; }
        </style>
        """, unsafe_allow_html=True)
    tool = st.radio(
        "Choose a tool",
        [
            "Merge PDF",
            "Split PDF",
            "Rotate PDF",
            "PDF to JPG",
            "JPG to PDF",
            "Crop JPG image",
        ],
        label_visibility="visible",
    )
    st.divider()
    st.markdown("**Privacy**")
    st.caption("This app processes files in its Python runtime. Avoid uploading sensitive documents to a public deployment unless you trust the host.")

# ---------------- Merge PDFs ----------------
if tool == "Merge PDF":
    st.subheader("Merge PDF files")
    st.write("Upload PDFs, arrange their order, preview the first page, and download one combined file.")
    uploads = st.file_uploader("Choose PDF files", type=["pdf"], accept_multiple_files=True, key="merge_uploads")
    if uploads:
        items = []
        for i, f in enumerate(uploads):
            raw = uploaded_bytes(f)
            try:
                pages = pdf_page_count(raw)
                items.append({"name": f.name, "data": raw, "pages": pages, "index": i})
            except Exception as e:
                st.error(f"Could not read {f.name}: {e}")
        if items:
            st.markdown("#### Arrange files")
            st.caption("Choose a position for each PDF. Files with lower positions are merged first.")
            ordered = []
            cols = st.columns(min(3, len(items)))
            for i, item in enumerate(items):
                with cols[i % len(cols)]:
                    st.markdown(f"<div class='tool-card'><h3>📄 {item['name']}</h3><p>{item['pages']} page(s)</p></div>", unsafe_allow_html=True)
                    pos = st.number_input(
                        f"Order for {item['name']}", min_value=1, max_value=len(items),
                        value=i + 1, step=1, key=f"merge_order_{item['index']}"
                    )
                    ordered.append((int(pos), i, item))
            name = st.text_input("Output PDF filename", value="merged_document", key="merge_name")
            if st.button("Merge PDFs", type="primary", use_container_width=True):
                try:
                    writer = PdfWriter()
                    for _, _, item in sorted(ordered, key=lambda x: (x[0], x[1])):
                        reader = PdfReader(io.BytesIO(item["data"]))
                        for page in reader.pages:
                            writer.add_page(page)
                    out = io.BytesIO()
                    writer.write(out)
                    result = out.getvalue()
                    st.session_state["merge_result"] = result
                    st.session_state["merge_result_name"] = ensure_ext(name, ".pdf")
                    st.success(f"Merged {len(items)} PDF files successfully.")
                except Exception as e:
                    st.error(f"Could not merge PDFs: {e}")
            if st.session_state.get("merge_result"):
                result = st.session_state["merge_result"]
                with st.expander("Preview merged PDF — first page", expanded=True):
                    try:
                        show_preview_image(render_pdf_preview(result), "First page preview")
                    except Exception:
                        st.info("Preview is unavailable for this PDF, but the output may still be downloadable.")
                download_bytes("⬇ Download merged PDF", result, st.session_state.get("merge_result_name", "merged_document.pdf"), "application/pdf")

# ---------------- Split PDF ----------------
elif tool == "Split PDF":
    st.subheader("Split PDF")
    st.write("Extract a page range into a new PDF. Page numbers start at 1.")
    pdf = st.file_uploader("Upload a PDF", type=["pdf"], key="split_pdf")
    if pdf:
        data = uploaded_bytes(pdf)
        try:
            reader = PdfReader(io.BytesIO(data))
            count = len(reader.pages)
            st.info(f"Document contains **{count} pages**.")
            c1, c2 = st.columns(2)
            with c1:
                start = st.number_input("Start page", min_value=1, max_value=count, value=1, step=1)
            with c2:
                end = st.number_input("End page", min_value=1, max_value=count, value=count, step=1)
            outname = st.text_input("Output filename", value=Path(pdf.name).stem + "_split")
            if st.button("Extract pages", type="primary", use_container_width=True):
                if start > end:
                    st.error("Start page must be less than or equal to end page.")
                else:
                    writer = PdfWriter()
                    for p in range(int(start) - 1, int(end)):
                        writer.add_page(reader.pages[p])
                    output = io.BytesIO()
                    writer.write(output)
                    result = output.getvalue()
                    st.session_state["split_result"] = result
                    st.session_state["split_name"] = ensure_ext(outname, ".pdf")
                    st.success(f"Extracted pages {start}–{end}.")
            if st.session_state.get("split_result"):
                result = st.session_state["split_result"]
                try:
                    show_preview_image(render_pdf_preview(result), "First extracted page")
                except Exception:
                    pass
                download_bytes("⬇ Download split PDF", result, st.session_state.get("split_name", "split.pdf"), "application/pdf")
        except Exception as e:
            st.error(f"Could not read this PDF: {e}")

# ---------------- Rotate PDF ----------------
elif tool == "Rotate PDF":
    st.subheader("Rotate PDF pages")
    st.write("Rotate every page or a selected range and save a new PDF.")
    pdf = st.file_uploader("Upload a PDF", type=["pdf"], key="rotate_pdf")
    if pdf:
        data = uploaded_bytes(pdf)
        try:
            reader = PdfReader(io.BytesIO(data))
            count = len(reader.pages)
            st.info(f"Document contains **{count} pages**.")
            degrees = st.selectbox("Rotation", [90, 180, 270], format_func=lambda x: f"{x}° clockwise")
            scope = st.radio("Pages to rotate", ["All pages", "Selected range"], horizontal=True)
            if scope == "Selected range":
                c1, c2 = st.columns(2)
                with c1:
                    start = st.number_input("Start page", 1, count, 1, key="rot_start")
                with c2:
                    end = st.number_input("End page", 1, count, count, key="rot_end")
            else:
                start, end = 1, count
            outname = st.text_input("Output filename", value=Path(pdf.name).stem + "_rotated")
            if st.button("Rotate PDF", type="primary", use_container_width=True):
                if start > end:
                    st.error("Start page must be less than or equal to end page.")
                else:
                    writer = PdfWriter()
                    for i, page in enumerate(reader.pages, start=1):
                        if int(start) <= i <= int(end):
                            page.rotate(int(degrees))
                        writer.add_page(page)
                    out = io.BytesIO()
                    writer.write(out)
                    result = out.getvalue()
                    st.session_state["rotate_result"] = result
                    st.session_state["rotate_name"] = ensure_ext(outname, ".pdf")
                    st.success("PDF rotated successfully.")
            if st.session_state.get("rotate_result"):
                result = st.session_state["rotate_result"]
                try:
                    show_preview_image(render_pdf_preview(result), "Rotated PDF preview")
                except Exception:
                    pass
                download_bytes("⬇ Download rotated PDF", result, st.session_state.get("rotate_name", "rotated.pdf"), "application/pdf")
        except Exception as e:
            st.error(f"Could not rotate this PDF: {e}")

# ---------------- PDF to JPG ----------------
elif tool == "PDF to JPG":
    st.subheader("Convert PDF to JPG")
    st.write("Convert all pages or a selected page range into high-quality JPG images. Multiple images download as a ZIP.")
    pdf = st.file_uploader("Upload a PDF", type=["pdf"], key="pdf_to_jpg")
    if pdf:
        data = uploaded_bytes(pdf)
        try:
            doc = fitz.open(stream=data, filetype="pdf")
            count = len(doc)
            st.info(f"Document contains **{count} pages**.")
            c1, c2 = st.columns(2)
            with c1:
                start = st.number_input("First page", 1, count, 1, key="jpg_start")
            with c2:
                end = st.number_input("Last page", 1, count, count, key="jpg_end")
            dpi = st.select_slider("Image quality", options=[96, 120, 150, 200, 250, 300], value=150, format_func=lambda x: f"{x} DPI")
            prefix = st.text_input("Output filename prefix", value=Path(pdf.name).stem)
            if st.button("Convert to JPG", type="primary", use_container_width=True):
                if start > end:
                    st.error("First page must be less than or equal to last page.")
                else:
                    converted = []
                    scale = dpi / 72
                    for page_index in range(int(start) - 1, int(end)):
                        pix = doc[page_index].get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
                        image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                        buff = io.BytesIO()
                        image.save(buff, format="JPEG", quality=94, optimize=True)
                        converted.append((page_index + 1, buff.getvalue(), image))
                    st.session_state["pdfjpg_result"] = converted
                    st.session_state["pdfjpg_prefix"] = safe_filename(prefix, "page")
                    st.success(f"Converted {len(converted)} page(s) to JPG.")
            if st.session_state.get("pdfjpg_result"):
                converted = st.session_state["pdfjpg_result"]
                st.markdown("#### Preview")
                preview_cols = st.columns(min(3, len(converted)))
                for idx, (page_no, img_bytes, image) in enumerate(converted[:6]):
                    with preview_cols[idx % len(preview_cols)]:
                        st.image(image, caption=f"Page {page_no}", use_container_width=True)
                prefix_saved = st.session_state.get("pdfjpg_prefix", "page")
                if len(converted) == 1:
                    page_no, img_bytes, _ = converted[0]
                    download_bytes("⬇ Download JPG", img_bytes, f"{prefix_saved}_page_{page_no}.jpg", "image/jpeg")
                else:
                    zbuf = io.BytesIO()
                    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as zf:
                        for page_no, img_bytes, _ in converted:
                            zf.writestr(f"{prefix_saved}_page_{page_no}.jpg", img_bytes)
                    download_bytes("⬇ Download all JPGs (ZIP)", zbuf.getvalue(), f"{prefix_saved}_jpg_pages.zip", "application/zip")
        except Exception as e:
            st.error(f"Could not convert this PDF: {e}")

# ---------------- JPG to PDF ----------------
elif tool == "JPG to PDF":
    st.subheader("Convert JPG images to PDF")
    st.write("Select multiple images, arrange their order, and combine them into one PDF.")
    images = st.file_uploader("Choose JPG/JPEG images", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="jpg_to_pdf")
    if images:
        image_items = []
        for i, f in enumerate(images):
            try:
                im = Image.open(io.BytesIO(uploaded_bytes(f)))
                im = ImageOps.exif_transpose(im).convert("RGB")
                image_items.append({"name": f.name, "image": im, "index": i})
            except Exception as e:
                st.warning(f"Skipping {f.name}: {e}")
        if image_items:
            st.markdown("#### Image order")
            cols = st.columns(min(4, len(image_items)))
            ordered = []
            for i, item in enumerate(image_items):
                with cols[i % len(cols)]:
                    st.image(item["image"], caption=item["name"], use_container_width=True)
                    pos = st.number_input("Position", min_value=1, max_value=len(image_items), value=i + 1, key=f"jpg_order_{i}")
                    ordered.append((int(pos), i, item))
            outname = st.text_input("Output PDF filename", value="images_document")
            if st.button("Create PDF", type="primary", use_container_width=True):
                try:
                    sorted_items = sorted(ordered, key=lambda x: (x[0], x[1]))
                    first = sorted_items[0][2]["image"]
                    rest = [x[2]["image"] for x in sorted_items[1:]]
                    out = io.BytesIO()
                    first.save(out, format="PDF", save_all=True, append_images=rest, resolution=150)
                    result = out.getvalue()
                    st.session_state["jpgpdf_result"] = result
                    st.session_state["jpgpdf_name"] = ensure_ext(outname, ".pdf")
                    st.success(f"Created a PDF from {len(sorted_items)} image(s).")
                except Exception as e:
                    st.error(f"Could not create PDF: {e}")
            if st.session_state.get("jpgpdf_result"):
                result = st.session_state["jpgpdf_result"]
                try:
                    show_preview_image(render_pdf_preview(result), "PDF preview")
                except Exception:
                    pass
                download_bytes("⬇ Download PDF", result, st.session_state.get("jpgpdf_name", "images_document.pdf"), "application/pdf")

# ---------------- Crop JPG ----------------
elif tool == "Crop JPG image":
    st.subheader("Crop a JPG/JPEG image")
    st.write("Upload an image, set the crop area, preview the result, and download it with a custom name.")
    image_file = st.file_uploader("Upload JPG/JPEG or PNG", type=["jpg", "jpeg", "png"], key="crop_image")
    if image_file:
        try:
            original = ImageOps.exif_transpose(Image.open(io.BytesIO(uploaded_bytes(image_file)))).convert("RGB")
            st.caption(f"Original size: {original.width} × {original.height} pixels")
            st.markdown("#### Crop coordinates")
            st.caption("Coordinates are measured from the top-left corner of the image.")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                left = st.number_input("Left (X)", min_value=0, max_value=original.width - 1, value=0, step=1)
            with c2:
                top = st.number_input("Top (Y)", min_value=0, max_value=original.height - 1, value=0, step=1)
            with c3:
                right = st.number_input("Right (X)", min_value=1, max_value=original.width, value=original.width, step=1)
            with c4:
                bottom = st.number_input("Bottom (Y)", min_value=1, max_value=original.height, value=original.height, step=1)
            outname = st.text_input("Output image filename", value=Path(image_file.name).stem + "_cropped")
            preview_col, result_col = st.columns(2)
            with preview_col:
                st.markdown("**Original image**")
                st.image(original, use_container_width=True)
            if left < right and top < bottom:
                cropped = original.crop((int(left), int(top), int(right), int(bottom)))
                with result_col:
                    st.markdown("**Cropped preview**")
                    st.image(cropped, use_container_width=True)
                output = io.BytesIO()
                cropped.save(output, format="JPEG", quality=95, optimize=True)
                download_bytes("⬇ Download cropped JPG", output.getvalue(), ensure_ext(outname, ".jpg"), "image/jpeg")
            else:
                st.warning("Right must be greater than Left, and Bottom must be greater than Top.")
        except Exception as e:
            st.error(f"Could not open this image: {e}")

st.divider()
st.markdown(
    "<div style='text-align:center;color:#83889a;font-size:.82rem'>"
    "Pedomerger · PDF & Image Toolkit · Files are processed in the app runtime"
    "</div>",
    unsafe_allow_html=True,
)
