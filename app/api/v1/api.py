from fastapi import APIRouter, Depends

from app.api.v1.endpoints import ai, auth, labels, notes, users
from app.core.deps import get_current_user

api_router = APIRouter()
api_router.include_router(
    ai.router, prefix="/ai", tags=["ai"], dependencies=[Depends(get_current_user)]
)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(
    labels.router, prefix="/labels", tags=["labels"], dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    notes.router, prefix="/notes", tags=["notes"], dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    users.router, prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)]
)
