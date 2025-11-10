import os
from fastapi import FastAPI, HTTPException
from supabase import create_client, Client
from dotenv import load_dotenv
# New: ML + typing + asyncio
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import asyncio
# CV processing
import pdfplumber
import docx
import io

# Load environment variables from .env file: current directory 1-
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Get Supabase URL and Key from environment
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_KEY")

# Create Supabase client
supabase: Client = create_client(url, key)

# Load AI model for semantic embeddings (Sprint 17: v4 Engine)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Extract text from CV files (PDF or DOCX)
async def _extract_text_from_cv(cv_path: str) -> str:
    try:
        # Download CV from private storage bucket
        file_bytes = await asyncio.to_thread(
            lambda: supabase.storage.from_('cvs').download(cv_path)
        )
        
        text = ''
        
        if cv_path.endswith('.pdf'):
            # Extract text from PDF
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + ' '
        
        elif cv_path.endswith('.docx'):
            # Extract text from DOCX
            doc = docx.Document(io.BytesIO(file_bytes))
            for para in doc.paragraphs:
                text += para.text + ' '
        
        return text.strip()
    except Exception as e:
        # Return empty string if CV cannot be read
        print(f"Warning: Could not extract CV text from {cv_path}: {str(e)}")
        return ''

# New: Fetch all jobs and seekers and build a corpus-
async def _get_all_data() -> tuple[List[str], List[Dict]]:
    # Run synchronous Supabase calls in a thread to avoid blocking
    jobs_response = await asyncio.to_thread(
        lambda: supabase.from_("job_postings").select("id, title, description, required_skills, company_name").execute()
    )
    # SPRINT 18: JOIN with profiles to get full_name (avoid N+1 query)
    seekers_response = await asyncio.to_thread(
        lambda: supabase.from_("seeker_profiles").select("profile_id, bio, skills, cv_file_path, profiles(full_name)").execute()
    )

    corpus: List[str] = []
    documents: List[Dict] = []

    # Jobs -> documents
    for job in (jobs_response.data or []):
        title = job.get("title") or ""
        desc = job.get("description") or ""
        req_skills = job.get("required_skills") or []
        if isinstance(req_skills, list):
            skills_text = " ".join(map(str, req_skills))
        else:
            skills_text = str(req_skills)
        job_text = f"{title} {desc} {skills_text}".strip()
        corpus.append(job_text)
        # PERFORMANCE FIX: Store full job data
        documents.append({"id": str(job.get("id")), "type": "job", "data": job})

    # Seekers -> documents (with CV text)
    for seeker in (seekers_response.data or []):
        bio = seeker.get("bio") or ""
        skills = seeker.get("skills") or []
        if isinstance(skills, list):
            skills_text = " ".join(map(str, skills))
        else:
            skills_text = str(skills)
        
        # Extract CV text if available
        cv_text = ''
        if seeker.get('cv_file_path'):
            cv_text = await _extract_text_from_cv(seeker['cv_file_path'])
        
        # WEIGHTED MATCHING LOGIC (Sprint 16)
        # This is the "weighting" logic to prevent CV text from diluting keywords
        # We multiply bio 3x and skills 5x to boost their importance
        # Skills are the most important signal for matching
        seeker_text = (bio + ' ') * 3 + (skills_text + ' ') * 5 + cv_text
        seeker_text = seeker_text.strip()
        
        # SPRINT 18: Extract full_name from profiles JOIN
        full_name = "Unknown"
        profiles_data = seeker.get("profiles")
        if profiles_data and isinstance(profiles_data, dict):
            full_name = profiles_data.get("full_name", "Unknown")
        
        # Add full_name to seeker data for caching
        seeker_with_name = {**seeker, "full_name": full_name}
        
        corpus.append(seeker_text)
        # PERFORMANCE FIX: Store full seeker data with full_name
        documents.append({"id": str(seeker.get("profile_id")), "type": "seeker", "data": seeker_with_name})

    return corpus, documents

# Health check endpoint
@app.get("/")
async def read_root():
    return {"message": "TalentFlow Engine is running"}

# Test database connection endpoint
@app.get("/test_db")
async def test_db():
    try:
        # Fetch data from Supabase to test connection
        data = await asyncio.to_thread(lambda: supabase.table("profiles").select("id").limit(1).execute())
        return {"status": "success", "data": data.data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# New: Recommendations endpoint (TF-IDF + Cosine Similarity)
@app.get("/recommendations/{seeker_profile_id}")
async def get_recommendations(seeker_profile_id: str, limit: int = 10):
    corpus, documents = await _get_all_data()
    try:
        if not corpus:
            return {"status": "success", "recommendations": []}

        embedding_matrix = model.encode(corpus)

        seeker_index = next(
            i for i, doc in enumerate(documents)
            if doc["id"] == seeker_profile_id and doc["type"] == "seeker"
        )

        seeker_vector = embedding_matrix[seeker_index]
        cosine_similarities = cosine_similarity([seeker_vector], embedding_matrix).flatten()

        job_scores = []
        for i in range(len(documents)):
            if documents[i]["type"] == "job":
                job_scores.append((documents[i]["id"], float(cosine_similarities[i])))

        # Top-N by score
        sorted_jobs = sorted(job_scores, key=lambda x: x[1], reverse=True)
        top = sorted_jobs[: max(1, min(limit, 50))]

        # PERFORMANCE FIX: Use cached data from documents instead of DB query
        recommendations = []
        for job_id, score in top:
            job_doc = next((doc for doc in documents if doc['id'] == job_id), None)
            if job_doc:
                job_data = job_doc['data']
                recommendations.append({
                    "job_id": job_id,
                    "score": round(score, 4),
                    "title": job_data.get("title"),
                    "company_name": job_data.get("company_name"),
                    "description": job_data.get("description"),
                })

        return {"status": "success", "recommendations": recommendations}
    except StopIteration:
        raise HTTPException(status_code=404, detail="Seeker profile not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New: Recommend candidates for a job
@app.get("/recommendations/job/{job_id}")
async def get_candidate_recommendations(job_id: str, limit: int = 10):
    corpus, documents = await _get_all_data()
    try:
        if not corpus:
            return {"status": "success", "recommendations": []}

        embedding_matrix = model.encode(corpus)

        job_index = next(
            i for i, doc in enumerate(documents)
            if doc["id"] == job_id and doc["type"] == "job"
        )

        job_vector = embedding_matrix[job_index]
        cosine_similarities = cosine_similarity([job_vector], embedding_matrix).flatten()

        seeker_scores = []
        for i in range(len(documents)):
            if documents[i]["type"] == "seeker":
                seeker_scores.append((documents[i]["id"], float(cosine_similarities[i])))

        sorted_seekers = sorted(seeker_scores, key=lambda x: x[1], reverse=True)
        top_seekers = sorted_seekers[: max(1, min(limit, 50))]

        # SPRINT 18: Use cached data including full_name (no N+1 query)
        recommendations = []
        for seeker_id, score in top_seekers:
            seeker_doc = next((doc for doc in documents if doc['id'] == seeker_id), None)
            if seeker_doc:
                seeker_data = seeker_doc['data']
                
                recommendations.append({
                    "profile_id": seeker_id,
                    "score": round(score, 4),
                    "full_name": seeker_data.get("full_name", "Unknown"),
                    "bio": seeker_data.get("bio", ""),
                    "skills": seeker_data.get("skills", []),
                })

        return {"status": "success", "recommendations": recommendations}
    except StopIteration:
        raise HTTPException(status_code=404, detail="Job not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Debug: list seeker profiles with IDs
@app.get("/debug/seekers")
async def debug_seekers():
    resp = await asyncio.to_thread(
        lambda: supabase.from_("seeker_profiles").select("profile_id, bio, skills").execute()
    )
    return {"count": len(resp.data or []), "seekers": resp.data or []}

# Debug: list jobs (ids and titles)
@app.get("/debug/jobs")
async def debug_jobs():
    resp = await asyncio.to_thread(
        lambda: supabase.from_("job_postings").select("id, title").execute()
    )
    return {"count": len(resp.data or []), "jobs": resp.data or []}

# Convenience: recommend by auth user_id (maps to profile_id)
@app.get("/recommendations/by-user/{user_id}")
async def get_recommendations_by_user(user_id: str):
    # Find profile_id from user_id
    prof = await asyncio.to_thread(
        lambda: supabase.from_("profiles").select("id").eq("user_id", user_id).maybe_single().execute()  # type: ignore
    )
    profile_row = getattr(prof, "data", None)
    if not profile_row or not profile_row.get("id"):
        raise HTTPException(status_code=404, detail="Profile not found for user_id")

    profile_id = str(profile_row["id"])

    # Ensure seeker profile exists
    seeker = await asyncio.to_thread(
        lambda: supabase.from_("seeker_profiles").select("profile_id").eq("profile_id", profile_id).maybe_single().execute()  # type: ignore
    )
    seeker_row = getattr(seeker, "data", None)
    if not seeker_row:
        raise HTTPException(status_code=404, detail="Seeker profile not found. Complete seeker profile setup first.")

    # Reuse main recommender
    return await get_recommendations(profile_id) 
