import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
import re
from collections import defaultdict
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

# -------------------------------------------------
# 提取 PDF 文本（含 OCR 支持）
# -------------------------------------------------
def extract_text_from_pdf(file):
    text = ""

    try:
        reader = PdfReader(file)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    except Exception as e:
        st.warning(f"普通提取失败：{e}")

    # 如果没提取到文字，则启用 OCR
    if not text.strip():
        st.info("🔍 未检测到文本，尝试使用 OCR 识别扫描账单...")
        text = extract_text_with_ocr(file)

    return text


# OCR 识别（支持中文 + 英文 + 马来语）
def extract_text_with_ocr(file):
    text = ""
    pdf = fitz.open(stream=file.read(), filetype="pdf")

    for page_num in range(len(pdf)):
        page = pdf.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        # 多语言 OCR（需服务器支持语言包 eng+chi_sim+msa）
        text += pytesseract.image_to_string(img, lang="eng+chi_sim+msa") + "\n"

    return text


# -------------------------------------------------
# 提取 Word 文本
# -------------------------------------------------
def extract_text_from_docx(file):
    doc = Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text


# -------------------------------------------------
# 智能解析交易文本
# -------------------------------------------------
def parse_transactions(text):
    grouped_data = defaultdict(list)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    current_name = None

    for line in lines:
        # 判断是否为客户名
        if re.match(r"^[A-Za-z\s&.'()]+$", line, flags=re.I) or ("SDN BHD" in line.upper()):
            current_name = line.strip()
            continue

        # 判断是否为交易金额行
        if current_name and re.search(r"[\d\.,-]+", line):
            grouped_data[current_name].append(line)

    return grouped_data


# -------------------------------------------------
# 生成 Word 报告
# -------------------------------------------------
def generate_word_report(grouped_data):
    doc = Document()
    doc.add_heading("转账整理报告", level=1)

    for name, records in grouped_data.items():
        doc.add_heading(name, level=2)
        if not records:
            doc.add_paragraph("(无交易记录)")
        else:
            for record in records:
                doc.add_paragraph(record)

    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output


# -------------------------------------------------
# Streamlit 主逻辑
# -------------------------------------------------
st.set_page_config(page_title="账单自动整理助手", page_icon="💰")

st.title("📄 账单自动整理助手（支持多银行 + OCR）")
st.markdown("上传银行账单（PDF / Word），自动识别客户与交易记录并导出 Word 报告。支持扫描账单识别。")

uploaded_file = st.file_uploader("上传账单文件", type=["pdf", "docx"])

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        text = extract_text_from_pdf(uploaded_file)
    else:
        text = extract_text_from_docx(uploaded_file)

    grouped_data = parse_transactions(text)

    if grouped_data:
        st.success(f"✅ 整理完成，共识别 {len(grouped_data)} 位客户。")

        if st.button("📘 生成 Word 报告"):
            word_file = generate_word_report(grouped_data)
            st.download_button(
                label="📥 下载 Word 文件",
                data=word_file,
                file_name="转账整理报告.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    else:
        st.warning("⚠️ 没有识别到客户或交易记录，请确认账单是文字版或扫描清晰。")
