from fastapi import APIRouter, HTTPException, Depends
from pymongo.collection import Collection
from src.backend.database import announcements_collection
from datetime import datetime
from typing import List, Optional
from fastapi import status
from pydantic import BaseModel, Field
from src.backend.routers.auth import get_current_user

class Announcement(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    title: str
    message: str
    start_date: Optional[str] = None
    expiration_date: str
    created_by: str

class AnnouncementCreate(BaseModel):
    title: str
    message: str
    start_date: Optional[str] = None
    expiration_date: str

router = APIRouter(prefix="/announcements", tags=["announcements"])

@router.get("/", response_model=List[Announcement])
def list_announcements():
    now = datetime.utcnow().isoformat()
    anns = list(announcements_collection.find({
        "$or": [
            {"start_date": None},
            {"start_date": {"$lte": now}}
        ],
        "expiration_date": {"$gte": now}
    }))
    for ann in anns:
        ann["_id"] = str(ann["_id"])
    return anns

@router.post("/", response_model=Announcement, status_code=status.HTTP_201_CREATED)
def create_announcement(announcement: AnnouncementCreate, user=Depends(get_current_user)):
    doc = announcement.dict()
    doc["created_by"] = user["username"]
    result = announcements_collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc

@router.put("/{announcement_id}", response_model=Announcement)
def update_announcement(announcement_id: str, announcement: AnnouncementCreate, user=Depends(get_current_user)):
    result = announcements_collection.update_one(
        {"_id": announcement_id},
        {"$set": announcement.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    doc = announcements_collection.find_one({"_id": announcement_id})
    doc["_id"] = str(doc["_id"])
    return doc

@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(announcement_id: str, user=Depends(get_current_user)):
    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return None
