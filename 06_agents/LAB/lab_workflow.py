# lab_workflow.py
# Multi-Agent Weather Report System
# Danny Atik - SYSEN 5381 Lab
#
# This script implements a 3-agent sequential workflow:
#   Agent 1 (Meteorologist):        Extracts structured weather data from a raw forecast
#   Agent 2 (Public Safety Advisor): Converts analysis into a public advisory
#   Agent 3 (Social Media Writer):   Condenses advisory into a shareable social post
#
# Each agent's output becomes the next agent's input, demonstrating multi-agent orchestration.

# 0. SETUP ###################################

import sys
import os
import yaml

# Add parent directory to path so we can import functions.py
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from functions import agent_run

# Select model
MODEL = "smollm2:1.7b"

# 1. LOAD RULES ###################################

rules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab_rules.yaml")
with open(rules_path, "r") as f:
    rules = yaml.safe_load(f)

rules_weather = rules["rules"]["weather_analyst"][0]
rules_advisory = rules["rules"]["public_advisory"][0]
rules_social = rules["rules"]["social_media"][0]


def format_rules(ruleset):
    """Format a ruleset dictionary into a string for the system prompt."""
    return f"{ruleset['name']}\n{ruleset['description']}\n\n{ruleset['guidance']}"


# 2. RAW WEATHER DATA (simulated input) ###################################

raw_weather = """
NATIONAL WEATHER SERVICE FORECAST — ITHACA, NY
Issued: March 15, 2026, 6:00 AM EDT

TODAY: Winter Storm Warning in effect from noon today through late tonight.
Heavy snow expected with accumulations of 8-12 inches. Temperatures falling
from a morning high of 34°F to 18°F by evening. Northeast winds 25 to 35 mph
with gusts up to 50 mph. Wind chill values as low as -5°F after dark.
Visibility dropping below 1/4 mile in heavy snow bands.

TONIGHT: Snow tapering off after midnight. Low around 12°F. Winds diminishing
to 10-15 mph. Additional accumulation of 1-3 inches possible.

SUNDAY: Partly cloudy and cold. High near 25°F. Wind chill -10°F in the morning.
Roads expected to remain hazardous through midday Sunday.

HAZARDS: Travel strongly discouraged after noon today. Power outages possible
due to heavy wet snow on power lines. Roof collapse risk for flat-roofed
structures with existing snow load.
"""

print("=" * 65)
print("🌨️  MULTI-AGENT WEATHER REPORT SYSTEM")
print("=" * 65)
print()
print("📥 RAW INPUT (National Weather Service Forecast):")
print(raw_weather)

# 3. AGENT 1 — Meteorologist ###################################

print("=" * 65)
print("🤖 AGENT 1: Meteorologist — Extracting Key Data")
print("=" * 65)

role1 = (
    "You are a meteorologist. You receive raw weather forecasts and extract "
    "the key data points into a structured summary. Focus only on the facts."
    f"\n\n{format_rules(rules_weather)}"
)

task1 = f"Extract and summarize the key weather data from this forecast:\n{raw_weather}"

result1 = agent_run(role=role1, task=task1, model=MODEL, output="text")

print(result1)
print()

# 4. AGENT 2 — Public Safety Advisor ###################################

print("=" * 65)
print("🤖 AGENT 2: Public Safety Advisor — Writing Advisory")
print("=" * 65)

role2 = (
    "You are a public safety communications officer. You receive weather "
    "analysis data and write clear, actionable public safety advisories "
    "that everyday people can understand and act on."
    f"\n\n{format_rules(rules_advisory)}"
)

task2 = f"Write a public safety advisory based on this weather analysis:\n\n{result1}"

result2 = agent_run(role=role2, task=task2, model=MODEL, output="text")

print(result2)
print()

# 5. AGENT 3 — Social Media Writer ###################################

print("=" * 65)
print("🤖 AGENT 3: Social Media Writer — Creating Post")
print("=" * 65)

role3 = (
    "You are a social media content creator for a local government agency. "
    "You receive public safety advisories and condense them into a single, "
    "shareable social media post."
    f"\n\n{format_rules(rules_social)}"
)

task3 = f"Create a social media post based on this public safety advisory:\n\n{result2}"

result3 = agent_run(role=role3, task=task3, model=MODEL, output="text")

print(result3)
print()

# 6. WORKFLOW SUMMARY ###################################

print("=" * 65)
print("✅ WORKFLOW COMPLETE")
print("=" * 65)
print()
print("Flow: Raw Forecast → Meteorologist → Public Safety Advisor → Social Media Post")
