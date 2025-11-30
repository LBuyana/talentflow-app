# TalentFlow Job Matching App

<p align="center">
  <img alt="Flutter" src="https://img.shields.io/badge/Frontend-Flutter-blue?style=for-the-badge&logo=flutter"/>
  <img alt="Python" src="https://img.shields.io/badge/Engine-Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img alt="Supabase" src="https://img.shields.io/badge/Backend-Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white"/>
  <img alt="Google Cloud" src="https://img.shields.io/badge/Deploy-Cloud%20Run-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white"/>
</p>

TalentFlow is the official job-matching application for our software company. It is designed to intelligently connect job seekers and recruiters using a custom AI-driven matching engine.

---

## Project Vision

TalentFlow aims to streamline hiring by providing personalized, efficient job and candidate recommendations.

### For Job Seekers

* Swipe to apply for jobs
* Receive AI-generated job recommendations
* Manage applications within the app

### For Recruiters

* Post job listings
* Swipe to save potential candidates
* View AI-ranked applicants
* Manage company and job profiles

---

## Key Features

* AI Matching Engine using SentenceTransformer (all-MiniLM-L6-v2)
* Swipe-based interface for job seekers and recruiters
* Role-based access control via Supabase RLS
* Resume parsing (PDF/DOCX text extraction)
* Cloud-native matching service deployed on Google Cloud Run
* Real-time features powered by Supabase

---

## Tech Stack

| Component       | Technology                              |
| --------------- | --------------------------------------- |
| Frontend        | Flutter (Material 3, go_router)         |
| Backend         | Supabase (Postgres, Auth, Storage, RLS) |
| Matching Engine | Python + FastAPI (Torch, Transformers)  |
| Deployment      | Docker & Google Cloud Run               |

---

## Repository Structure

```
/
├── app/                  # Flutter mobile application
│   ├── lib/              # Dart code (screens, widgets, models)
│   ├── assets/           # Images and icons
│   └── pubspec.yaml
│
├── engine/               # Python matching engine (FastAPI)
│   ├── main.py           # API endpoints and logic
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile        # Container configuration
│
├── supabase/             # Supabase configuration and migrations
│   └── migrations/
│
├── .github/workflows/    # CI/CD pipelines
└── README.md
```

---

## Project Status

| Service       | Build Status | Deployment            |
| ------------- | ------------ | --------------------- |
| Flutter App   | In Progress  | Local / Not Published |
| Python Engine | Stable       | Google Cloud Run      |

---

## Getting Started

This guide covers everything required to run the project locally.

---

### 1. Clone the Repository

```bash
git clone https://github.com/LBuyana/talentflow-app.git
cd talentflow-app
```

---

### 2. Set Up Supabase

1. Create a new project at [https://database.new](https://database.new)
2. Run the SQL scripts to create required tables:

   * profiles
   * job_postings
   * applications
   * company profiles
3. Enable Row Level Security (RLS) and required policies
4. Enable Google/GitHub authentication
5. Create storage buckets:

   * `avatars` (public)
   * `cvs` (private)

---

### 3. Run the Python Engine Locally

Requirements: Python 3.10+

```bash
cd engine

python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file:

```
SUPABASE_URL=your_url
SUPABASE_SERVICE_KEY=your_service_key
```

Start the server:

```bash
uvicorn main:app --reload
```

The engine will be available at:

```
http://127.0.0.1:8000
```

---

### 4. Run the Flutter App

Requirements: Flutter SDK

```bash
cd app
flutter pub get
```

Update configuration:

* `lib/constants.dart` → Engine URL (local or Cloud Run)
* `lib/main.dart` → Supabase URL and Anon Key

Run the app:

```bash
flutter run
```

---

## Contribution Guidelines

1. Create a feature branch

   ```bash
   git checkout -b feature/YourFeature
   ```
2. Commit changes

   ```bash
   git commit -m "Add YourFeature"
   ```
3. Push the branch

   ```bash
   git push origin feature/YourFeature
   ```
4. Open a Pull Request


