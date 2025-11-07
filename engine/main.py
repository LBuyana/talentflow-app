import os
from fastapi import FastAPI, HTTPException
from supabase import create_client, Client
from dotenv import load_dotenv
# New: ML + typing + asyncio
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict
import asyncio

# Load environment variables from .env file: current directory 1
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Get Supabase URL and Key from environment
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_KEY")

# Create Supabase client
supabase: Client = create_client(url, key)

# New: Fetch all jobs and seekers and build a corpus
async def _get_all_data() -> (List[str], List[Dict[str, str]]):
    # Run synchronous Supabase calls in a thread to avoid blocking
    jobs_response = await asyncio.to_thread(
        lambda: supabase.from_("job_postings").select("id, title, description, required_skills").execute()
    )
    seekers_response = await asyncio.to_thread(
        lambda: supabase.from_("seeker_profiles").select("profile_id, bio, skills").execute()
    )

    corpus: List[str] = []
    documents: List[Dict[str, str]] = []

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
        documents.append({"id": str(job.get("id")), "type": "job"})

    # Seekers -> documents
    for seeker in (seekers_response.data or []):
        bio = seeker.get("bio") or ""
        skills = seeker.get("skills") or []
        if isinstance(skills, list):
            skills_text = " ".join(map(str, skills))
        else:
            skills_text = str(skills)
        seeker_text = f"{bio} {skills_text}".strip()
        corpus.append(seeker_text)
        documents.append({"id": str(seeker.get("profile_id")), "type": "seeker"})

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

        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(corpus)

        seeker_index = next(
            i for i, doc in enumerate(documents)
            if doc["id"] == seeker_profile_id and doc["type"] == "seeker"
        )

        seeker_vector = tfidf_matrix[seeker_index]
        cosine_similarities = cosine_similarity(seeker_vector, tfidf_matrix).flatten()

        job_scores = []
        for i in range(len(documents)):
            if documents[i]["type"] == "job":
                job_scores.append((documents[i]["id"], float(cosine_similarities[i])))

        # Top-N by score
        sorted_jobs = sorted(job_scores, key=lambda x: x[1], reverse=True)
        top = sorted_jobs[: max(1, min(limit, 50))]

        # Fetch details for top jobs in a single query
        top_ids = [jid for jid, _ in top]
        if not top_ids:
            return {"status": "success", "recommendations": []}

        details_resp = await asyncio.to_thread(
            lambda: supabase.from_("job_postings")
                .select("id, title, description, company_name")
                .in_("id", top_ids)
                .execute()
        )
        job_map = {str(j["id"]): j for j in (details_resp.data or [])}

        recommendations = [
            {
                "job_id": jid,
                "score": round(score, 4),
                "title": job_map.get(jid, {}).get("title"),
                "company_name": job_map.get(jid, {}).get("company_name"),
                "description": job_map.get(jid, {}).get("description"),
            }
            for jid, score in top
        ]

        return {"status": "success", "recommendations": recommendations}
    except StopIteration:
        raise HTTPException(status_code=404, detail="Seeker profile not found")
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