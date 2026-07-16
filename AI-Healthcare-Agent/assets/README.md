# Screenshots & Assets

This directory contains screenshots and media assets for the AI Healthcare Platform.

## Required Screenshots

For a polished GitHub README, capture the following screenshots and place them in this directory:

| # | Screenshot | Description | File Name |
|---|-----------|-------------|-----------|
| 1 | **Patient Dashboard** | Full dashboard view with appointment summary, medicine adherence, and quick actions | `dashboard-patient.png` |
| 2 | **Doctor Dashboard** | Doctor view with patient list, adherence overview, and pending alerts | `dashboard-doctor.png` |
| 3 | **Medical Report Upload** | Drag-drop upload interface with processing pipeline visualization | `report-upload.png` |
| 4 | **Report Analysis View** | Extracted medicine details with dosage, frequency, and confidence indicators | `report-analysis.png` |
| 5 | **Chat Interface** | Conversation UI with inline citations, confidence scores, and suggested questions | `chat-interface.png` |
| 6 | **Citation View** | Source document references displayed within AI responses | `citation-view.png` |
| 7 | **Medicines Grid** | Filterable, sortable medicine table with adherence tracking | `medicines-grid.png` |
| 8 | **Demo Mode** | Guided walkthrough showing key platform features step-by-step | `demo-mode.png` |
| 9 | **Emergency Detection** | Symptom triage interface with urgency classification | `emergency-triage.png` |
| 10 | **Architecture Diagram** | High-level system architecture showing all layers | `architecture.png` |
| 11 | **Login Screen** | Clean login page with "Try Demo" option | `login-screen.png` |

## Image Guidelines

- Use **1920×1080** or **2880×1620** resolution
- Prefer **PNG** format for screenshots
- Keep file sizes under 500 KB each
- Crop to show only relevant content
- Enable dark mode for a professional look (where applicable)
- Avoid showing real patient data (use demo/seed data)

## How to Generate

1. Start the application (see [Quick Start](../README.md#quick-start))
2. Run the demo seed script to populate sample data
3. Navigate to each feature
4. Capture screenshots using your OS screenshot tool
5. Save files with the names listed above

## Demo Data

Use the demo mode to pre-populate the application with realistic sample data:

```bash
# Seed demo data
curl -X POST http://localhost:8000/api/demo/seed

# Login as demo patient
curl -X POST http://localhost:8000/api/demo/login
```

## Updating README Preview

After adding screenshots, update the Screenshots section in [README.md](../README.md) to reference the new images.
