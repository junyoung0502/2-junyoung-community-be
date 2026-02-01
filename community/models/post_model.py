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
                SELECT p.id as postId, p.title, p.content, p.created_at as createdAt, p.view_count as viewCount,
                   u.id as userId, u.nickname as author, u.profile_url as profileImage,
                   (SELECT COUNT(*) FROM post_likes pl WHERE pl.post_id = p.id) as likeCount,
                   (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id AND c.deleted_at IS NULL) as commentCount
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
        """[DB 방식] 새 게시물을 생성하고 저장합니다."""
        with engine.connect() as conn:
            query = text("""
                INSERT INTO posts (user_id, title, content, created_at, updated_at)
                VALUES (:user_id, :title, :content, NOW(), NOW())
            """)
            result = conn.execute(query, {
                "user_id": post_data["userId"],
                "title": post_data["title"],
                "content": post_data["content"]
            })
            conn.commit() # INSERT 작업 후엔 꼭 commit을 해줘야 DB에 저장됩니다.
            return result.lastrowid # 방금 생성된 게시글의 ID를 반환합니다.
    
    @staticmethod
    def update_post(post_id: int, update_data: dict):
        """[DB 방식] ID로 게시물을 찾아 내용을 업데이트합니다."""
        with engine.connect() as conn:
            query = text("""
                UPDATE posts 
                SET title = :title, content = :content, updated_at = NOW()
                WHERE id = :post_id AND deleted_at IS NULL
            """)
            result = conn.execute(query, {
                "title": update_data["title"],
                "content": update_data["content"],
                "post_id": post_id
            })
            conn.commit()
            return result.rowcount > 0 # 수정된 행이 있으면 True 반환
    
    @staticmethod
    def delete_post(post_id: int):
        """[DB 방식] 실제 삭제 대신 deleted_at에 시간을 기록하는 '소프트 삭제'를 수행합니다."""
        with engine.connect() as conn:
            query = text("""
                UPDATE posts 
                SET deleted_at = NOW() 
                WHERE id = :post_id
            """)
            result = conn.execute(query, {"post_id": post_id})
            conn.commit()
            return result.rowcount > 0
    
    @staticmethod
    def increase_view_count(post_id: int):
        """[DB 방식] 게시글 조회 시 view_count 컬럼을 1 증가시킵니다."""
        with engine.connect() as conn:
            query = text("""
                UPDATE posts 
                SET view_count = view_count + 1 
                WHERE id = :post_id
            """)
            result = conn.execute(query, {"post_id": post_id})
            conn.commit()
            return result.rowcount > 0