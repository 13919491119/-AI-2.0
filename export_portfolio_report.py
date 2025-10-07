import markdown # pyright: ignore[reportMissingModuleSource]
import pdfkit # pyright: ignore[reportMissingImports]
import os

md_file = '投资组合配置表.md'
pdf_file = '投资组合配置表.pdf'

# 读取Markdown内容
def read_md(md_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        return f.read()

# 转换为HTML
def md_to_html(md_text):
    return markdown.markdown(md_text, extensions=['tables'])

# 导出为PDF
def html_to_pdf(html, pdf_file):
    # 需要wkhtmltopdf支持
    options = {
        'encoding': 'UTF-8',
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'enable-local-file-access': None
    }
    pdfkit.from_string(html, pdf_file, options=options)

if __name__ == '__main__':
    md_text = read_md(md_file)
    html = md_to_html(md_text)
    html_to_pdf(html, pdf_file)
    print(f'PDF报告已导出：{pdf_file}')
