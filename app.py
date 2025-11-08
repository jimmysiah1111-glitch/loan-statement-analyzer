import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

st.set_page_config(page_title="账单自动整理助手（支持多银行 + OCR）", layout="wide")

st.title("💰 账单自动整理助手（支持多银行 + OCR）")
st.write("上传你的银行账单（PDF 或 Word），系统会自动识别客户与交易记录并导出 Word 报告。支持扫描账单识别。")

uploaded_file = st.file_uploader("上传账单文件", type=["pdf", "docx"])

def extract_text_from_pdf(file):
    """尝试直接读取文字版 PDF"""
    text = ""
    doc = fitz.open(stream=file.read(), filetype="pdf")
    for page in doc:
        text += page.get_text("text")
    return text

def extract_text_from_scanned_pdf(file):
    """扫描账单 OCR 识别"""
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text += pytesseract.image_to_string(img, lang="chi_sim+eng") + "\n"
    return text

if uploaded_file:
    file_bytes = uploaded_file.read()
    st.success("✅ 文件上传成功，开始分析...")

    # Step 1: 尝试直接提取文字
    text = extract_text_from_pdf(io.BytesIO(file_bytes))
    if len(text.strip()) < 20:
        # Step 2: 尝试 OCR 提取
        st.warning("检测到文件可能是扫描账单，正在进行 OCR 文字识别，请稍候...")
        text = extract_text_from_scanned_pdf(io.BytesIO(file_bytes))

    if text.strip():
        st.success("✅ 已成功提取文本内容！以下为部分预览：")
        st.text_area("文字识别结果预览", text[:2000], height=400)
    else:
        st.error("❌ 没有识别到任何文字，请确认账单内容清晰。")
