import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
from collections import defaultdict
from docx.shared import Inches

# ------------------------------------------------
# 函数：从 PDF 文件提取文本
# ------------------------------------------------
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


# ------------------------------------------------
# 函数：从 Word 文件提取文本
# ------------------------------------------------
def extract_text_from_docx(file):
    doc = Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text


# ------------------------------------------------
# 函数：将文本拆分成客户分组
# ------------------------------------------------
def group_transactions(text):
    lines = text.splitlines()
    groups = defaultdict(list)
    current_name = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.isupper() or any(x in line for x in ["SDN", "BHD", "TRADING", "ENTERPRISE", "BIN", "BINTI", "A/L", "A/P"]):
            current_name = line.strip()
        elif current_name:
            groups[current_name].append(line)
    return groups


# ------------------------------------------------
# 函数：生成 Word 报告
# ------------------------------------------------
def generate_word_report(groups):
    doc = Document()
    doc.add_heading("转账记录整理报告", level=1)

    for name, transactions in groups.items():
        clean_name = str(name).replace('\n', ' ').replace('\r', ' ').strip()
        if not clean_name:
            continue

        doc.add_paragraph(clean_name, style="Heading 2")
        for t in transactions:
            clean_t = str(t).replace('\n', ' ').replace('\r', ' ').strip()
            doc.add_paragraph(clean_t, style="List Bullet")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# ------------------------------------------------
# Streamlit 前端界面
# ------------------------------------------------
st.set_page_config(page_title="账单自动整理助手", layout="wide")
st.title("📊 银行账单自动整理工具")

uploaded_file = st.file_uploader("上传账单文件（PDF 或 Word）", type=["pdf", "docx"])

if uploaded_file:
    if uploaded_file.name.lower().endswith(".pdf"):
        text = extract_text_from_pdf(uploaded_file)
    else:
        text = extract_text_from_docx(uploaded_file)

    grouped_data = group_transactions(text)

    st.success(f"✅ 已整理完成，共识别 {len(grouped_data)} 位客户。")

    if st.button("📄 生成 Word 报告"):
        word_file = generate_word_report(grouped_data)
        st.download_button(
            label="⬇️ 点击下载 Word 报告",
            data=word_file,
            file_name="账单整理报告.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
