from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_extractor import extract_pdf, PdfExtractionError

router = APIRouter()

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="กรุณาอัปโหลดไฟล์นามสกุล .pdf เท่านั้น")

    try:
        extraction_result = extract_pdf(file.file)
        
        raw_text = extraction_result.full_text
        total_pages = extraction_result.page_count
        warnings = [w.message for w in extraction_result.warnings]

    except PdfExtractionError as e:
        raise HTTPException(status_code=400, detail=f"เกิดข้อผิดพลาดในการอ่าน PDF: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    return {
        "status": "draft_ready",
        "filename": file.filename,
        "extraction_info": {
            "page_count": total_pages,
            "warnings": warnings
        },
        "project_metadata": {
            "title": "รอ AI สกัดชื่อเรื่อง...",
            "author": "รอ AI สกัดผู้จัดทำ...",
            "year": "รอ AI สกัดปี..."
        },
        "draft_markdown": f"## ข้อความดิบที่ดึงมาได้ (รอส่งต่อให้ LLM)\n\n{raw_text[:1000]}...\n\n---\n*หมายเหตุ: สกัดข้อความสำเร็จจากทั้งหมด {total_pages} หน้า*"
    }