import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

# Setup
os.makedirs("reports", exist_ok=True)
load_dotenv("/Users/dannyatik/Desktop/Cornell/SYSEN-5381/dsai/.env", override=True)
load_dotenv("/Users/dannyatik/Desktop/Prediction-Markets/.env", override=True)

client = OpenAI() # Assumes OPENAI_API_KEY is in environment

NUM_REPORTS_PER_PROMPT = 10

# 1. Define Prompts for generating reports
PROMPTS = {
    "Prompt A (Basic)": "Write a report about the recent Q3 dataset showing a 15% increase in Metric A and high variance in Metric C.",
    "Prompt B (Detailed)": "Write a detailed data analysis report about the Q3 dataset showing a 15% increase in Metric A and high variance in Metric C. Include an Introduction, Body, and Conclusion.",
    "Prompt C (Expert)": "Write an expert-level, highly actionable data analysis report for executive leadership about the Q3 dataset (15% increase in Metric A, high variance in Metric C). Focus on strategic recommendations, risk mitigation, and maintain a highly professional tone."
}

# 2. Define Validation Schema
class ValidationResult(BaseModel):
    actionability_score: int = Field(..., description="Score 1-10 on how clear and practical the recommendations are.")
    depth_score: int = Field(..., description="Score 1-10 on how well the data is interpreted and analyzed.")
    tone_score: int = Field(..., description="Score 1-10 on how professional and business-appropriate the writing is.")
    reasoning: str = Field(..., description="Brief explanation of the scores.")

def generate_report(prompt_text, iteration):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a data analyst."},
            {"role": "user", "content": f"{prompt_text}\n\nPlease generate variation #{iteration} of this report."}
        ],
        temperature=0.8
    )
    return response.choices[0].message.content

def validate_report(report_text):
    system_prompt = """
    You are an expert AI quality control reviewer. Your task is to evaluate the provided data analysis report based on 3 criteria:
    1. Actionability (1-10): Are there clear, practical recommendations?
    2. Depth of Analysis (1-10): Is the data well-interpreted beyond just repeating the numbers?
    3. Professional Tone (1-10): Is the language suitable for a business environment?
    """
    
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please evaluate the following report:\n\n{report_text}"}
        ],
        response_format=ValidationResult,
        temperature=0.0
    )
    return response.choices[0].message.parsed

import concurrent.futures

def process_single_report(prompt_name, prompt_text, i):
    print(f"Generating and validating report {i+1}/{NUM_REPORTS_PER_PROMPT} for {prompt_name}...")
    report_content = generate_report(prompt_text, i)
    
    safe_name = prompt_name.split(" ")[0] + "_" + prompt_name.split(" ")[1].strip("()")
    file_path = f"reports/{safe_name}_report_{i+1}.txt"
    with open(file_path, "w") as f:
        f.write(report_content)
        
    validation = validate_report(report_content)
    total_score = validation.actionability_score + validation.depth_score + validation.tone_score
    
    return {
        "Prompt": prompt_name,
        "Report_ID": i + 1,
        "Actionability": validation.actionability_score,
        "Depth": validation.depth_score,
        "Tone": validation.tone_score,
        "Total_Score": total_score,
        "Reasoning": validation.reasoning
    }

def main():
    print("Starting AI Report Generation and Validation Pipeline...")
    results = []
    
    tasks = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for prompt_name, prompt_text in PROMPTS.items():
            for i in range(NUM_REPORTS_PER_PROMPT):
                tasks.append(executor.submit(process_single_report, prompt_name, prompt_text, i))
        
        for future in concurrent.futures.as_completed(tasks):
            results.append(future.result())

    # 3. Save Results
    df = pd.DataFrame(results)
    df.to_csv("validation_results.csv", index=False)
    print("\nResults saved to validation_results.csv")
    
    # 4. Statistical Analysis (ANOVA)
    print("\n--- Statistical Analysis (ANOVA) ---")
    groups = [group["Total_Score"].values for name, group in df.groupby("Prompt")]
    f_stat, p_value = stats.f_oneway(*groups)
    
    print(f"F-statistic: {f_stat:.4f}")
    print(f"P-value: {p_value:.4e}")
    
    if p_value < 0.05:
        print("Result: SIGNIFICANT difference in performance between prompts.")
    else:
        print("Result: NO significant difference between prompts.")
        
    print("\nMean Scores by Prompt:")
    print(df.groupby("Prompt")["Total_Score"].mean())

    # 5. Visualization
    plt.figure(figsize=(10, 6))
    sns.boxplot(x="Prompt", y="Total_Score", data=df, hue="Prompt", palette="Set2")
    plt.title(f"Report Validation Scores by Prompt\nANOVA p-value = {p_value:.4e}")
    plt.ylabel("Total Validation Score (Out of 30)")
    plt.tight_layout()
    plt.savefig("validation_results.png")
    print("Boxplot saved to validation_results.png")
    
    # Save a sample report and its validation output to a separate text file for screenshots
    sample_row = df.iloc[-1]
    with open("sample_validation_output.txt", "w") as f:
        f.write(f"PROMPT USED:\n{sample_row['Prompt']}\n\n")
        f.write("SCORES:\n")
        f.write(f"Actionability: {sample_row['Actionability']}/10\n")
        f.write(f"Depth: {sample_row['Depth']}/10\n")
        f.write(f"Tone: {sample_row['Tone']}/10\n")
        f.write(f"Total: {sample_row['Total_Score']}/30\n\n")
        f.write("REASONING:\n")
        f.write(f"{sample_row['Reasoning']}\n")
    print("Sample validation output saved to sample_validation_output.txt")

if __name__ == "__main__":
    main()
