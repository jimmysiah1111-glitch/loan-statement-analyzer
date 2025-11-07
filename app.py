import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
from collections import defaultdict

# -------------------------------------------------
# 函数：从 PDF 文件提取文本
# -------------------------------------------------
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


# -------------------------------------------------
# 函数：从 Word 文件提取文本
# -------------------------------------------------
def extract_text_from_docx(file):
    doc = Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text


# -------------------------------------------------
# 函数：分析交易数据
# -------------------------------------------------
def parse_transactions(text):
    grouped_data = defaultdict(list)
    lines = text.split("\n")

    current_name = None
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检测姓名行（非交易行）
        if any(c.isalpha() for c in line) and not any(ch.isdigit() for ch in line):
            current_name = line.strip()
            continue

        # 交易行（包含金额）
        if current_name and any(ch.isdigit() for ch in line):
            grouped_data[current_name].append(line)

    return grouped_data


# -------------------------------------------------
# 函数：生成 Word 报告
# -------------------------------------------------
def generate_word_report(grouped_data):
    doc = Document()
    doc.add_heading("转账整理报告", level=1)

    for name, records in grouped_data.items():
        # 清理特殊字符，防止 ValueError
        safe_name = str(name).encode("utf-8", "ignore").decode("utf-8", "ignore")
        doc.add_paragraph(safe_name, style="Heading 2")

        for record in records:
            safe_record = str(record).encode("utf-8", "ignore").decode("utf-8", "ignore")
            doc.add_paragraph(safe_record)

    # 输出 Word 文件
    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output


# -------------------------------------------------
# Streamlit 页面主逻辑
# -------------------------------------------------
st.set_page_config(page_title="账单自动整理助手", page_icon="💰")

st.title("📄 账单自动整理助手（RHB / CIMB / HL / 等银行）")
st.markdown("上传你的银行账单（PDF 或 Word），我会自动识别客户并生成 Word 报告。")

uploaded_file = st.file_uploader("上传账单文件", type=["pdf", "docx"])

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        text = extract_text_from_pdf(uploaded_file)
    else:
        text = extract_text_from_docx(uploaded_file)

    grouped_data = parse_transactions(text)

    st.success(f"已整理完成，共识别到 **{len(grouped_data)} 位客户**。")

    if st.button("生成 Word 报告"):
        try:
            word_file = generate_word_report(grouped_data)
            st.download_button(
                label="📥 下载 Word 报告",
                data=word_file,
                file_name="转账整理报告.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except Exception as e:
            st.error(f"生成报告时出错：{e}")
