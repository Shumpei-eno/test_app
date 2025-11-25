"""データベース接続とユーザー管理のためのモジュール"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from contextlib import contextmanager


def get_db_connection():
    """PostgreSQLデータベースへの接続を取得"""
    # ローカル開発環境ではDATABASE_URL（外部接続用）を優先
    # 本番環境（Render）ではINTERNAL_DATABASE_URL（内部接続用）を使用
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('INTERNAL_DATABASE_URL')
    
    if not database_url:
        raise ValueError("DATABASE_URLまたはINTERNAL_DATABASE_URL環境変数が設定されていません")
    
    print(f"データベース接続URL: {database_url[:50]}...")  # デバッグ用（パスワード部分は表示しない）
    
    # RenderのPostgreSQL URLはpostgres://で始まるが、psycopg2はpostgresql://を期待する場合がある
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return psycopg2.connect(database_url)


@contextmanager
def get_db_cursor():
    """データベースカーソルをコンテキストマネージャーとして取得"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
    finally:
        conn.close()


def init_database():
    """データベースの初期化（ユーザーテーブルの作成）"""
    with get_db_cursor() as cursor:
        # ユーザーテーブルの作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # インデックスの作成
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
        """)


def create_user(username: str, password: str) -> dict:
    """新しいユーザーを作成"""
    try:
        # pbkdf2を使用してscryptの問題を回避
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (username, password_hash)
                VALUES (%s, %s)
                RETURNING id, username, created_at
            """, (username, password_hash))
            result = cursor.fetchone()
            return {
                "id": result["id"],
                "username": result["username"],
                "created_at": result["created_at"].isoformat() if result["created_at"] else None
            }
    except psycopg2.IntegrityError:
        return {"error": "このユーザーネームは既に登録されています"}
    except Exception as e:
        return {"error": f"ユーザー作成に失敗しました: {str(e)}"}


def verify_user(username: str, password: str) -> dict:
    """ユーザーの認証"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id, username, password_hash, created_at
                FROM users
                WHERE username = %s
            """, (username,))
            user = cursor.fetchone()
            
            if not user:
                return {"error": "ユーザーネームまたはパスワードが正しくありません"}
            
            if check_password_hash(user["password_hash"], password):
                return {
                    "id": user["id"],
                    "username": user["username"],
                    "created_at": user["created_at"].isoformat() if user["created_at"] else None
                }
            else:
                return {"error": "ユーザーネームまたはパスワードが正しくありません"}
    except Exception as e:
        return {"error": f"認証に失敗しました: {str(e)}"}


def get_user_by_username(username: str) -> dict:
    """ユーザーネームでユーザーを取得"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id, username, created_at
                FROM users
                WHERE username = %s
            """, (username,))
            user = cursor.fetchone()
            
            if user:
                return {
                    "id": user["id"],
                    "username": user["username"],
                    "created_at": user["created_at"].isoformat() if user["created_at"] else None
                }
            return None
    except Exception as e:
        return {"error": f"ユーザー取得に失敗しました: {str(e)}"}

