import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from io import BytesIO
from docx import Document
from collections import defaultdict

# ======================
# 函数：从 PDF 文件提取文本（支持 OCR）
# ======================
def extract_text_from_pdf(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as pdf:
        for page_num, page in enumerate(pdf, start=1):
            # 提取文本
            page_text = page.get_text("text")
            if not page_text.strip():
                # 若是扫描件则进行 OCR
                pix = page.get_pixmap(dpi=300)
                img = Image.open(BytesIO(pix.tobytes("png")))
                img = img.convert("L")  # 灰度化
                text += pytesseract.image_to_string(img, lang="chi_sim+eng")
            else:
                text += page_text
    return text

# ======================
# 函数：从 Word 文件提取文本
# ======================
def extract_text_from_docx(file):
    doc = Document(file)
    text = "\n".join([p.text for p in doc.paragraphs])
    return text

# ======================
# 函数：解析账单文本（示例）
# ======================
def parse_transactions(text):
    customers = defaultdict(list)
    lines = text.splitlines()
    for line in lines:
        if not line.strip():
            continue
        # 示例：检测客户名和金额
        if "客户" in line or "户名" in line:
            current_name = line.strip()
        elif any(x in line for x in ["￥", "元", "金额"]):
            customers[current_name].append(line.strip())
    return customers

# ======================
# 函数：生成 Word 报告
# ======================
def generate_word_report(customers):
    doc = Document()
    doc.add_heading("转账整理报告", level=1)

    for name, records in customers.items():
        doc.add_heading(name, level=2)
        for r in records:
            doc.add_paragraph(r)

    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output

# ======================
# Streamlit 主程序
# ======================
st.title("📄 账单自动整理助手（支持多银行 + OCR）")
st.write("上传你的银行账单（PDF 或 Word），系统会自动识别客户与交易记录并导出 Word 报告。")

uploaded_file = st.file_uploader("上传账单文件", type=["pdf", "docx"])

if uploaded_file:
    if uploaded_file.name.endswith(".pdf"):
        text = extract_text_from_pdf(uploaded_file)
    else:
        text = extract_text_from_docx(uploaded_file)

    if text.strip():
        customers = parse_transactions(text)
        if customers:
            st.success(f"已识别 {len(customers)} 位客户。")
            word_file = generate_word_report(customers)
            st.download_button("📥 下载 Word 报告", word_file, file_name="转账整理报告.docx")
        else:
            st.warning("⚠️ 没有识别到客户或交易记录，请确认账单文字清晰。")
    else:
        st.error("无法从账单中提取任何文字，请确认上传的文件不是空白或受保护。")
