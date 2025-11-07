import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
import re
from collections import defaultdict

# -------------------------------------------------
# 提取 PDF 文本
# -------------------------------------------------
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        try:
            text += page.extract_text() + "\n"
        except:
            pass
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
# 智能解析交易文本（改进版）
# -------------------------------------------------
def parse_transactions(text):
    grouped_data = defaultdict(list)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    current_name = None

    for line in lines:
        # 识别客户名称（一般不含数字）
        if re.match(r"^[A-Za-z\s&.'()]+$", line, flags=re.I) or ("SDN BHD" in line.upper()):
            current_name = line.strip()
            continue

        # 识别交易行（包含金额）
        if current_name and re.search(r"[\d\.,-]+", line):
            grouped_data[current_name].append(line)

    return grouped_data


# -------------------------------------------------
# 生成 Word 报告（自动换行 + UTF-8 兼容）
# -------------------------------------------------
def generate_word_report(grouped_data):
    doc = Document()
    doc.add_heading("转账整理报告", level=1)

    for name, records in grouped_data.items():
        safe_name = str(name).encode("utf-8", "ignore").decode("utf-8", "ignore")
        doc.add_heading(safe_name, level=2)

        if not records:
            doc.add_paragraph("(无交易记录)")
        else:
            for record in records:
                safe_record = str(record).encode("utf-8", "ignore").decode("utf-8", "ignore")
                doc.add_paragraph(safe_record)

    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output


# -------------------------------------------------
# Streamlit 主逻辑
# -------------------------------------------------
st.set_page_config(page_title="账单自动整理助手", page_icon="💰")

st.title("📄 账单自动整理助手（支持多银行）")
st.markdown("上传你的银行账单（PDF 或 Word），自动识别客户与交易记录并导出 Word 报告。")

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
            try:
                word_file = generate_word_report(grouped_data)
                st.download_button(
                    label="📥 下载 Word 文件",
                    data=word_file,
                    file_name="转账整理报告.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as e:
                st.error(f"生成报告时出错：{e}")
    else:
        st.warning("⚠️ 没有识别到客户或交易记录，请确认账单文字清晰。")
