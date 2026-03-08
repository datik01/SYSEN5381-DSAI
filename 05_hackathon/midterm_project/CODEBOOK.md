# Codebook: City Congestion Tracker

This document describes the structure and variables of the Supabase PostgreSQL database used to power the City Congestion Tracker application.

## 1. Table: `locations`

This table stores the fixed geographic entities being monitored by the system.

| Variable Name | Data Type | Description | Example |
|---------------|-----------|-------------|---------|
| `id` | UUID (Primary Key) | Auto-generated unique identifier for the location. | `34c83de4-297b-45c4-a170...` |
| `name` | TEXT | Common name of the intersection or highway segment. | `"Downtown Crossing"`, `"West End Bridge"` |
| `zone` | TEXT | General city region the location belongs to. | `"Central"`, `"North"`, `"South"` |

---

## 2. Table: `congestion_readings`

This table stores the time-series observational data representing the real-time congestion at a specific location.

| Variable Name | Data Type | Description | Example |
|---------------|-----------|-------------|---------|
| `id` | UUID (Primary Key) | Auto-generated unique identifier for the reading. | `f829db2a-8211-47c2-9a3b...` |
| `location_id` | UUID (Foreign Key) | The ID of the `locations` table this reading corresponds to. | `34c83de4-297b-45c4-a170...` |
| `timestamp` | TIMESTAMPTZ | The exact date and time the reading was recorded. | `2026-03-08 14:43:04+00` |
| `severity_level` | INTEGER | An integer from `1` to `5` indicating traffic severity. | `4` |

### Severity Level Index
*   **1 - Clear**: Free-flowing traffic at or above speed limits.
*   **2 - Minor Delay**: Normal traffic volume, slight speed reduction.
*   **3 - Moderate**: Noticeable slow-downs, dense clustering of vehicles.
*   **4 - Heavy**: Stop-and-go conditions, significant delays.
*   **5 - Gridlock**: Complete standstill, emergency reporting required.

---

## Data Generation Methodology

The dataset is synthetically generated using entirely simulated histories via the `/database/seed_data.py` script.
*   The script generates **7 days** of historical data.
*   It generates exactly **1 reading per hour** for every location.
*   It implements a "Rush Hour" logic constraint: Readings taken between `07:00-09:00` and `16:00-18:00` have a higher base severity (Avg `4`), while readings taken between `00:00-05:00` have a lower base severity (Avg `1`). A +/- `1` randomness factor is applied to simulate natural variance.
