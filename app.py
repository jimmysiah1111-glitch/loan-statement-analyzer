import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
from collections import defaultdict
from docx.shared import Inches

# -------------------------------
# 函数：从 PDF 文件提取文本
# -------------------------------
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# -------------------------------
# 函数：从 Word 文件提取文本
# -------------------------------
def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

# -------------------------------
# 函数：提取转账记录
# -------------------------------
def extract_transactions(text):
    lines = text.split("\n")
    transactions = []
    current_name = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 忽略 Cash Deposit
        if "cash deposit" in line.lower():
            continue
        # 识别名字
        if any(keyword in line.upper() for keyword in ["SDN", "BHD", "BIN", "BINTI", "BINTI", "TRADING", "ENTERPRISE"]):
            current_name = line.strip()
        # 识别转账记录
        elif any(char.isdigit() for char in line):
            if current_name:
                transactions.append((current_name, line))
    return transactions

# -------------------------------
# 函数：整理记录
# -------------------------------
def summarize_transactions(all_transactions):
    grouped = defaultdict(list)
    for name, record in all_transactions:
        grouped[name].append(record)
    return grouped

# -------------------------------
# 函数：生成 Word 文件
# -------------------------------
def generate_word_report(grouped_data):
    doc = Document()
    doc.add_heading("贷款转账记录总表", level=1)

    for name, records in grouped_data.items():
        doc.add_paragraph(name, style="Heading 2")
        for record in records:
            doc.add_paragraph(record)
        doc.add_paragraph("")  # 空行分隔

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# -------------------------------
# Streamlit 界面
# -------------------------------
st.set_page_config(page_title="贷款转账整理助手", page_icon="💰", layout="wide")
st.title("💰 贷款转账记录自动整理工具")

st.write("上传多个银行账单（PDF 或 Word 格式），系统将自动：")
st.markdown("""
- 提取所有转账记录  
- 忽略 Cash Deposit  
- 自动合并同名客户  
- 导出为 Word 总表文件
""")

uploaded_files = st.file_uploader("📂 请选择账单文件（可多选）", type=["pdf", "docx"], accept_multiple_files=True)

if uploaded_files:
    all_transactions = []
    for uploaded_file in uploaded_files:
        if uploaded_file.name.lower().endswith(".pdf"):
            text = extract_text_from_pdf(uploaded_file)
        else:
            text = extract_text_from_docx(uploaded_file)
        transactions = extract_transactions(text)
        all_transactions.extend(transactions)

    grouped_data = summarize_transactions(all_transactions)

    st.success(f"✅ 已整理完成，共识别 {len(grouped_data)} 位客户。")
    st.write("点击下方按钮下载 Word 报告：")

    word_file = generate_word_report(grouped_data)
    st.download_button(
        label="📘 下载贷款转账记录总表 (.docx)",
        data=word_file,
        file_name="贷款转账记录总表.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
