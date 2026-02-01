# controllers/post_controller.py
from datetime import datetime
from fastapi import HTTPException, Response
from models.post_model import PostModel
from models.user_model import UserModel
from models.comment_model import CommentModel
from models.like_model import LikeModel
from utils import BaseResponse, PostCreateRequest, PostDetail, UserInfo, PostUpdateRequest, CommentSimple, AuthorDetail

class PostController:
    @staticmethod
    def get_posts(last_post_id: int, size: int, response: Response):
        """전체 게시글 목록을 가져오는 흐름 제어"""
        
        # [방어 코드] 0이나 음수가 들어오면 처음부터 보여주도록 None 처리
        actual_last_id = None if (last_post_id is None or last_post_id <= 0) else last_post_id
        
        # 1. 모델에서 데이터 가져오기
        posts = PostModel.get_all_posts(last_post_id=actual_last_id, size=size)

        # 2. 데이터가 없을 때 처리
        if not posts:
            response.status_code = 200
            return BaseResponse(
                message="NO_MORE_POSTS",
                data={"posts": [], "nextCursor": None}
            )
        
        # 3. [핵심] 다음 페이지의 기준점(nextCursor) 계산
        # 가져온 데이터의 마지막 항목 ID를 다음 요청 때 쓰라고 알려줍니다.
        # 만약 요청한 size보다 적게 가져왔다면 '더 이상 글이 없음'을 의미하므로 None을 줍니다.
        next_cursor = posts[-1]["postId"] if len(posts) == size else None

        response.status_code = 200
        return BaseResponse(
            message="POST_RETRIEVAL_SUCCESS",
            data={
                "posts": posts,
                "nextCursor": next_cursor
            }
        )

    @staticmethod
    def _prepare_post_summaries(posts, size):
        """게시글 상세 내용을 제거하고 요약본 생성"""
        
        summaries = []
        for post in posts[:size]:
            # content 필드를 제외한 post 생성
            summary = {
                "postId": post["postId"],
                "title": post["title"],
                "author": post["author"],
                "profileImage": post["profileImage"],
                "createdAt": post["createdAt"],
                "likeCount": post.get("likeCount", 0),
                "commentCount": post.get("commentCount", 0),
                "viewCount": post.get("viewCount", 0)
            }
            summaries.append(summary)

        return summaries
    
    @staticmethod
    def get_post_detail(post_id: int, response: Response) -> BaseResponse:
        """게시글 상세 조회 및 조회수 증가 (댓글은 별도 API에서 처리)"""
    
        # 1. 게시글과 작성자 정보를 한 번에 가져옴 (Model에서 Join 처리됨)
        post = PostModel.get_post_by_id(post_id)
        
        if not post:
            # 특정 글을 찍어서 들어왔는데 없으면 에러(Raise)가 정답!
            raise HTTPException(status_code=404, detail="POST_NOT_FOUND")
        
        # 2. 조회수 증가 (비즈니스 로직)
        PostModel.increase_view_count(post_id)
        
        response.status_code = 200
        return BaseResponse(
            message="POST_DETAIL_SUCCESS",
            data=post
        )

    @staticmethod
    def create_post(request: PostCreateRequest, user: UserInfo, response: Response):
        """새 게시글 작성"""

        new_post = {
            "title": request.title,       # 클라이언트가 보낸 제목
            "content": request.content,   # 클라이언트가 보낸 내용
            "image": request.image,       # 클라이언트가 보낸 이미지
            "author": user.nickname,      
            "profileImage": user.profileImage or "https://image.kr/img.jpg",
            "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "likeCount": 0, "commentCount": 0, "viewCount": 0
        }
        
        # Model에게 저장을 부탁함
        post_id = PostModel.create_post(new_post)

        response.status_code = 201
        return BaseResponse(
            message="POST_CREATE_SUCCESS",
            data={"postId": post_id}
        )
    
    @staticmethod
    def update_post(post_id: int, request: PostUpdateRequest, user: UserInfo, response: Response):
        """게시글 수정: 작성자 본인만 가능"""
        
        # 1. 게시글 존재 확인
        post = PostModel.get_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="POST_NOT_FOUND")
        
        # 2. [핵심 보안] 권한 체크 (내 글이 아니면 403 Forbidden)
        if post["author"] != user.nickname:
            raise HTTPException(status_code=403, detail="PERMISSION_DENIED")
        
        # 3. 업데이트 수행
        update_data = {
            "title": request.title,
            "content": request.content
        }
        PostModel.update_post(post_id, update_data)
        
        # 4. 응답
        return BaseResponse(
            message="POST_UPDATE_SUCCESS",
            data={"postId": post_id}
        )
    
    @staticmethod
    def delete_post(post_id: int, user: UserInfo, response: Response):
        """게시글 삭제: 작성자 본인만 가능"""
        
        # 1. 게시글 존재 확인
        post = PostModel.get_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="POST_NOT_FOUND")
        
        # 2. 권한 체크 (내 글이 아니면 403)
        if post["author"] != user.nickname:
            raise HTTPException(status_code=403, detail="PERMISSION_DENIED")
        
        # 3. 삭제 수행 (댓글, 좋아요도 함께 삭제)
        CommentModel.delete_comments_by_post_id(post_id)
        LikeModel.delete_likes_by_post_id(post_id)
        PostModel.delete_post(post_id)
        
        # 4. 응답
        return BaseResponse(
            message="POST_DELETE_SUCCESS",
            data=None
        )