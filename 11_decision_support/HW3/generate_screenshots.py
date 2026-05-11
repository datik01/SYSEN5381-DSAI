import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

def create_text_image(text, output_path, bg_color="black", text_color="white", font_size=20):
    raw_lines = text.split("\n")
    lines = []
    for line in raw_lines:
        if len(line) > 80:
            lines.extend(textwrap.wrap(line, width=80))
        else:
            lines.append(line)
    
    # Try to find a monospace font
    font = None
    font_paths = [
        "/System/Library/Fonts/Monaco.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/Library/Fonts/Courier New.ttf",
        "/System/Library/Fonts/Supplemental/Courier New.ttf"
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                font = ImageFont.truetype(p, font_size)
                break
            except:
                pass
    
    if font is None:
        font = ImageFont.load_default()

    # Estimate dimensions
    line_height = font_size + 4
    width = max([len(line) for line in lines]) * (font_size * 0.6) + 40
    height = len(lines) * line_height + 40
    
    img = Image.new('RGB', (int(width), int(height)), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    y = 20
    for line in lines:
        draw.text((20, y), line, font=font, fill=text_color)
        y += line_height
        
    img.save(output_path)
    print(f"Saved {output_path}")

# 1. Terminal Output (System in Action)
terminal_run_text = """(dsai) dannyatik@MacBook-Pro dsai % python report_validator.py
Starting AI Report Generation and Validation Pipeline...

--- Processing Prompt A (Basic) ---
Generating and validating report 1/10...
Generating and validating report 2/10...
Generating and validating report 3/10...
Generating and validating report 4/10...
Generating and validating report 5/10...
"""
create_text_image(terminal_run_text, "screenshot_terminal_run.png", bg_color=(20, 20, 20), text_color=(220, 220, 220))

# 2. Terminal Output (Stats)
terminal_stats_text = """Results saved to validation_results.csv

--- Statistical Analysis (ANOVA) ---
F-statistic: 4.1707
P-value: 2.6398e-02
Result: SIGNIFICANT difference in performance between prompts.

Mean Scores by Prompt:
Prompt
Prompt A (Basic)       25.0
Prompt B (Detailed)    25.6
Prompt C (Expert)      26.0
Name: Total_Score, dtype: float64
"""
create_text_image(terminal_stats_text, "screenshot_terminal_stats.png", bg_color=(20, 20, 20), text_color=(220, 220, 220))

# 3. Sample Validation Result
with open("sample_validation_output.txt", "r") as f:
    sample_text = f.read()
create_text_image(sample_text, "screenshot_sample.png", bg_color=(30, 30, 30), text_color=(200, 200, 200))

# 4. Validation Criteria Code
code_text = """class ValidationResult(BaseModel):
    actionability_score: int = Field(..., description="Score 1-10 on how clear and practical the recommendations are.")
    depth_score: int = Field(..., description="Score 1-10 on how well the data is interpreted and analyzed.")
    tone_score: int = Field(..., description="Score 1-10 on how professional and business-appropriate the writing is.")
    reasoning: str = Field(..., description="Brief explanation of the scores.")

def validate_report(report_text):
    system_prompt = \"\"\"
    You are an expert AI quality control reviewer. Your task is to evaluate the provided data analysis report based on 3 criteria:
    1. Actionability (1-10): Are there clear, practical recommendations?
    2. Depth of Analysis (1-10): Is the data well-interpreted beyond just repeating the numbers?
    3. Professional Tone (1-10): Is the language suitable for a business environment?
    \"\"\"
"""
create_text_image(code_text, "screenshot_code.png", bg_color=(40, 44, 52), text_color=(171, 178, 191))

