# routes/post_route.py
from fastapi import APIRouter, Query, Response
from controllers.post_controller import PostController
from utils import BaseResponse

router = APIRouter(prefix="/api/v1")

@router.get("/posts", response_model=BaseResponse)
async def get_all_posts(
    response: Response,
    offset: int = Query(1, ge=1, description="조회 시작 게시글 ID"),
    size: int = Query(10, ge=0, le=100, description="가져올 게시글 개수")
):
    # Controller를 통해 데이터를 가져옵니다.    
    return PostController.get_posts(offset, size, response)