# models/post_model.py
from sqlalchemy import text
from database import engine

# posts_db = [
#     {
#         "postId": 1,
#         "title": "제목 1",
#         "author": "더미 작성자1",
#         "content": "이것은 1번 게시글의 아주 긴 상세 내용입니다. 목록에서는 보이지 않아야 합니다.",
#         "profileImage": "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png",
#         "createdAt": "2021-01-01 00:00:00",
#         "likeCount": 0,
#         "commentCount": 0,
#         "viewCount": 0
#     },
#     {
#         "postId": 2,
#         "title": "제목 2",
#         "author": "더미 작성자2",
#         "content": "2번 게시글의 내용입니다. 역시 목록 조회 시에는 제외됩니다.",
#         "profileImage": "https://cdn.pixabay.com/photo/2017/06/13/12/53/profile-2398782_1280.png",
#         "createdAt": "2021-01-01 00:00:00",
#         "likeCount": 5,
#         "commentCount": 2,
#         "viewCount": 10
#     }
# ]

class PostModel:
    @staticmethod
    def get_all_posts(last_post_id: int = None, size: int = 10):
        with engine.connect() as conn:
            if last_post_id is None:
                query = text("""
                    SELECT p.id as postId, p.title, u.nickname as author, -- 이름을 'author'로 설정
                        p.created_at as createdAt, p.view_count as viewCount,
                        u.profile_url as profileImage,
                        (SELECT COUNT(*) FROM post_likes pl WHERE pl.post_id = p.id) as likeCount,
                        (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id AND c.deleted_at IS NULL) as commentCount
                    FROM posts p
                    JOIN users u ON p.user_id = u.id
                    WHERE p.deleted_at IS NULL
                    ORDER BY p.id DESC LIMIT :size
                """)
                params = {"size": size}
            else:
                query = text("""
                    SELECT p.id as postId, p.title, u.nickname as author, -- 이름을 'author'로 설정
                        p.created_at as createdAt, p.view_count as viewCount,
                        u.profile_url as profileImage,
                        (SELECT COUNT(*) FROM post_likes pl WHERE pl.post_id = p.id) as likeCount,
                        (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id AND c.deleted_at IS NULL) as commentCount
                    FROM posts p
                    JOIN users u ON p.user_id = u.id
                    WHERE p.id < :last_id AND p.deleted_at IS NULL
                    ORDER BY p.id DESC LIMIT :size
                """)
                params = {"last_id": last_post_id, "size": size}
            
            result = conn.execute(query, params).fetchall()
            
            posts = []
            for row in result:
                r = row._mapping
                posts.append({
                    "postId": r["postId"],
                    "title": r["title"],
                    "createdAt": r["createdAt"],
                    "viewCount": r["viewCount"],
                    "likeCount": r["likeCount"],
                    "commentCount": r["commentCount"],
                    "author": {
                        "nickname": r["author"], # SQL 별칭과 똑같이 'author'로 수정!
                        "profileImage": r["profileImage"]
                    }
                })
            return posts

    @staticmethod
    def get_post_by_id(post_id: int):
        """특정 게시글 상세 조회 (작성자 정보 포함 JOIN)"""
        with engine.connect() as conn:
            query = text("""
                SELECT p.id as postId, p.title, p.content, 
                    p.created_at as createdAt, p.like_count as likeCount, 
                    p.comment_count as commentCount, p.view_count as viewCount,
                    u.id as userId, u.nickname as author, u.profile_url as profileImage
                FROM posts p
                JOIN users u ON p.user_id = u.id
                WHERE p.id = :post_id AND p.deleted_at IS NULL
            """)
            result = conn.execute(query, {"post_id": post_id}).fetchone()
            
            if not result:
                return None
                
            # 결과를 프론트엔드 형식에 맞게 가공 (author를 객체화)
            row = result._mapping
            return {
                "postId": row["postId"],
                "title": row["title"],
                "content": row["content"],
                "createdAt": row["createdAt"],
                "likeCount": row["likeCount"],
                "commentCount": row["commentCount"],
                "viewCount": row["viewCount"],
                "author": {
                    "userId": row["userId"],
                    "nickname": row["author"],
                    "profileImage": row["profileImage"]
                }
            }
    
    @staticmethod
    def create_post(post_data: dict):
        """새 게시물을 생성하고 저장합니다."""
        """DB에서 가장 큰 ID를 찾아 +1 하여 발급"""
        new_id = 1
        
        if posts_db:
            max_id = max(post["postId"] for post in posts_db)
            new_id = max_id + 1
            
        post_data["postId"] = new_id
        posts_db.append(post_data)
        
        return new_id
    
    @staticmethod
    def update_post(post_id: int, update_data: dict):
        """ID로 게시물을 찾아 내용을 업데이트합니다."""
        # 리스트에서 찾아서 업데이트 (레퍼런스 참조라 원본이 바뀜)
        for post in posts_db:
            if post["postId"] == post_id:
                # update_data에 있는 키들(title, content)만 덮어쓰기
                post.update(update_data)
                return True # 성공
        return False # 실패
    
    @staticmethod
    def delete_post(post_id: int):
        """ID로 게시물을 찾아 리스트에서 삭제"""
        for post in posts_db:
            if post["postId"] == post_id:
                posts_db.remove(post) # 리스트에서 해당 딕셔너리 제거
                return True
        return False
    
    @staticmethod
    def increase_view_count(post_id: int):
        """조회수 1 증가"""
        for post in posts_db:
            if post["postId"] == post_id:
                post["viewCount"] += 1
                return True
        return False