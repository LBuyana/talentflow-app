TalentFlow Job Matching App

<p align="center">
<img alt="Flutter" src="https://img.shields.io/badge/Frontend-Flutter-blue?style=for-the-badge&logo=flutter"/>
<img alt="Python" src="https://www.google.com/search?q=https://img.shields.io/badge/Engine-Python-3776AB%3Fstyle%3Dfor-the-badge%26logo%3Dpython"/>
<img alt="Supabase" src="https://www.google.com/search?q=https://img.shields.io/badge/Backend-Supabase-3ECF8E%3Fstyle%3Dfor-the-badge%26logo%3Dsupabase"/>
<img alt="Google Cloud" src="https://www.google.com/search?q=https://img.shields.io/badge/Deploy-Cloud%2520Run-4285F4%3Fstyle%3Dfor-the-badge%26logo%3Dgooglecloud"/>
</p>

Welcome to the official repository for the TalentFlow Job Matching App!
This project is the flagship product for our software company, designed to connect job seekers and recruiters efficiently using intelligent AI matching.

Project Vision

Our mission is to build a smart, intuitive platform that leverages modern technology to streamline the hiring process. This app serves two main user groups:

Job Seekers: Swipe to apply for jobs, view personalized AI recommendations based on CV analysis, and manage applications.

Recruiters: Post jobs, swipe to save candidates, view AI-ranked applicants, and manage company profiles.

Key Features

AI Matching Engine: Custom Python engine using SentenceTransformer (all-MiniLM-L6-v2) to semantically match CVs to Job Descriptions.

Swipe Interface: "Tinder-style" card swiping for quick saving/applying.

Role-Based Access: Secure separate flows for Seekers and Recruiters using Supabase RLS.

Resume Parsing: Automatic text extraction from PDF/DOCX resumes.

Cloud Native: Auto-scaling Python engine hosted on Google Cloud Run.

Tech Stack

This project is built using a modern, scalable technology stack:

Frontend (Mobile): Flutter — Cross-platform (iOS & Android) app with Material 3 design and go_router navigation.

Backend (BaaS): Supabase — Postgres database, Authentication (Email + OAuth), Storage (Avatars/CVs), and Real-time features.

Matching Engine (Service): Python — FastAPI service running torch and transformers for ML inference. Deployed via Docker.

Repository Structure

/
├── app/                  # Flutter mobile application
│   ├── lib/              # Dart code (Screens, Widgets, Models)
│   ├── assets/           # Images and Icons
│   ├── pubspec.yaml      # Dependencies
│   └── ...
├── engine/               # Python matching engine (FastAPI)
│   ├── main.py           # API Endpoints & Logic
│   ├── requirements.txt  # Python dependencies (Torch, Scikit-learn, etc.)
│   ├── Dockerfile        # Container configuration
│   └── ...
├── supabase/             # Supabase configuration
│   └── migrations/       # Database schema & RLS policies
├── .github/              # GitHub-specific files
│   └── workflows/        # CI/CD pipeline (deploy_engine.yml)
├── .gitignore
└── README.md


Project Status

Service

Build Status

Deployment

Flutter App



Local / Store Release

Python Engine





Getting Started

Follow these instructions to run the project locally.

1. Clone the Repository

git clone [https://github.com/LBuyana/talentflow-app.git](https://github.com/LBuyana/talentflow-app.git)
cd talentflow-app


2. Set Up Supabase

Create a new project at database.new.

Run the SQL scripts provided in the documentation to create tables (profiles, job_postings, applications, etc.) and set up Row Level Security (RLS).

Enable Google/GitHub Authentication providers.

Create Storage buckets for avatars (public) and cvs (private).

3. Run the Python Engine (Local)

You need Python 3.10+ installed.

cd engine
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

# Install dependencies (Warning: downloads PyTorch ~2GB)
pip install -r requirements.txt

# Setup environment variables
# Create a .env file with SUPABASE_URL and SUPABASE_SERVICE_KEY

# Run the server
uvicorn main:app --reload


The engine will run at http://127.0.0.1:8000

4. Run the Flutter App

You need the Flutter SDK installed.

cd app
# Install dependencies
flutter pub get

# Setup configuration
# Update lib/constants.dart with your Engine URL (Local or Cloud Run)
# Update lib/main.dart with your Supabase Anon Key & URL

# Run on emulator or device
flutter run


Contribution Guidelines

Create a feature branch (git checkout -b feature/AmazingFeature).

Commit your changes (git commit -m 'Add some AmazingFeature').

Push to the branch (git push origin feature/AmazingFeature).

Open a Pull Request.
