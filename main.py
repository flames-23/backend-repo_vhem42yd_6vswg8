import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List, Optional
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import CVProfile

from xhtml2pdf import pisa
from io import BytesIO

app = FastAPI(title="MakeMeHired.com API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "MakeMeHired Backend Running"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# ---------- CV Generation Helpers ----------

def skills_to_keywords(skills: List[str]) -> List[str]:
    return [s.strip() for s in skills if s and isinstance(s, str)]


def render_cv_html(data: CVProfile) -> str:
    # Safe formatting for ATS: one column, headings, bullet lists
    def bullet_list(items: Optional[List[str]]) -> str:
        if not items:
            return ""
        lis = "".join([f"<li>{p}</li>" for p in items if p])
        return f"<ul>{lis}</ul>"

    # Experience
    exp_html = ""
    for e in data.experience:
        ach_html = bullet_list(e.achievements)
        exp_html += f"""
        <div class='exp-item'>
            <div class='exp-header'><strong>{e.role}</strong> | {e.company} — <span class='muted'>{e.duration}</span></div>
            {ach_html}
        </div>
        """

    # Education
    edu_html = ""
    for ed in data.education:
        edu_html += f"<div class='edu-item'><strong>{ed.degree}</strong>, {ed.institution} — <span class='muted'>{ed.year}</span></div>"

    certs_html = bullet_list(data.certifications)
    projects_html = bullet_list(data.projects)
    languages_html = bullet_list(data.languages)
    interests_html = bullet_list(data.interests)

    skills_html = "".join([f"<span class='tag'>{s}</span>" for s in skills_to_keywords(data.skills)])

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<title>{data.full_name} — {data.job_title_target} CV</title>
<style>
  @page {{ size: A4; margin: 20mm; }}
  body {{ font-family: Arial, Helvetica, sans-serif; color: #111; font-size: 11pt; }}
  .header {{ border-bottom: 2px solid #111; padding-bottom: 6px; margin-bottom: 10px; }}
  .name {{ font-size: 20pt; font-weight: bold; }}
  .contact {{ font-size: 10pt; color: #333; }}
  h2 {{ font-size: 12.5pt; margin: 14px 0 6px; padding: 0; }}
  .section {{ margin-bottom: 8px; }}
  .muted {{ color: #555; }}
  ul {{ margin: 4px 0 0 18px; }}
  li {{ line-height: 1.35; margin: 2px 0; }}
  .tag {{ display: inline-block; border: 1px solid #999; padding: 2px 6px; border-radius: 3px; margin: 2px 6px 0 0; font-size: 9pt; }}
  .exp-item, .edu-item {{ margin-bottom: 6px; }}
</style>
</head>
<body>
  <div class='header'>
    <div class='name'>{data.full_name}</div>
    <div class='contact'>
      {data.phone} • {data.email}{' • ' + data.linkedin if data.linkedin else ''}
    </div>
  </div>

  <div class='section'>
    <h2>Professional Summary</h2>
    <p>{data.summary or f"Results-driven {data.job_title_target} with experience across key areas and strong focus on measurable impact."}</p>
  </div>

  <div class='section'>
    <h2>Core Skills</h2>
    <div>{skills_html}</div>
  </div>

  <div class='section'>
    <h2>Professional Experience</h2>
    {exp_html}
  </div>

  <div class='section'>
    <h2>Education</h2>
    {edu_html}
  </div>

  {f"<div class='section'><h2>Certifications</h2>{certs_html}</div>" if certs_html else ''}
  {f"<div class='section'><h2>Projects / Achievements</h2>{projects_html}</div>" if projects_html else ''}
  {f"<div class='section'><h2>Languages</h2>{languages_html}</div>" if languages_html else ''}
  {f"<div class='section'><h2>Interests</h2>{interests_html}</div>" if interests_html else ''}

</body>
</html>
"""
    return html


def html_to_pdf_bytes(html: str) -> bytes:
    # Convert HTML to PDF (A4) using xhtml2pdf
    pdf_io = BytesIO()
    pisa.CreatePDF(src=html, dest=pdf_io)
    pdf_io.seek(0)
    return pdf_io.read()


# ---------- API Endpoints ----------

@app.post("/api/cv/generate")
def generate_cv(profile: CVProfile):
    """Accept user input and return HTML + PDF bytes (base64) and a storage id."""
    # Persist to DB
    try:
        doc_id = create_document("cvprofile", profile)
    except Exception as e:
        # Proceed even if DB not configured, but note error
        doc_id = None

    html = render_cv_html(profile)
    pdf_bytes = html_to_pdf_bytes(html)

    # Encode PDF for transfer
    import base64
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    filename = f"{profile.full_name.replace(' ', '')}_{profile.job_title_target.replace(' ', '')}_MakeMeHiredCV.pdf"

    return {
        "id": doc_id,
        "filename": filename,
        "html": html,
        "pdf_base64": pdf_b64,
    }


@app.get("/api/cv/templates")
def get_templates():
    return {
        "templates": [
            {"id": "modern", "name": "Modern"},
            {"id": "minimal", "name": "Minimal"},
            {"id": "classic", "name": "Classic"}
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
