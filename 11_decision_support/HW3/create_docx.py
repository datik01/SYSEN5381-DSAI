import docx
from docx.shared import Inches

def md_to_docx(md_filepath, docx_filepath, img_filepath):
    doc = docx.Document()
    
    with open(md_filepath, 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if not line:
            doc.add_paragraph()
            continue
            
        if line.startswith("# "):
            doc.add_heading(line[2:], 0)
        elif line.startswith("## "):
            doc.add_heading(line[3:], 1)
        elif line.startswith("### "):
            doc.add_heading(line[4:], 2)
        elif line.startswith("* "):
            doc.add_paragraph(line, style='List Bullet')
        elif line.startswith("1. ") or line.startswith("2. ") or line.startswith("3. ") or line.startswith("4. ") or line.startswith("5. "):
            doc.add_paragraph(line, style='List Number')
        elif line.startswith("|") or line.startswith("---"):
            doc.add_paragraph(line) # Simplified table handling for now
        elif line.startswith("*(Please insert"):
            # Insert the image here
            doc.add_paragraph(line)
            try:
                doc.add_picture(img_filepath, width=Inches(6.0))
                doc.add_paragraph("Figure: Validation Results Boxplot")
            except Exception as e:
                doc.add_paragraph(f"[Image placeholder for {img_filepath} - {e}]")
        else:
            doc.add_paragraph(line)
            
    doc.save(docx_filepath)
    print(f"Successfully saved {docx_filepath}")

if __name__ == "__main__":
    md_to_docx("HOMEWORK3_SUBMISSION.md", "HOMEWORK3_SUBMISSION.docx", "validation_results.png")
