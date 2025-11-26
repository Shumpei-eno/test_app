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
    """データベースの初期化（ユーザーテーブルと物件テーブルの作成）"""
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
        
        # 物件テーブルの作成（ユーザーIDを外部キーとして持つ）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                mansion_name VARCHAR(255),
                address VARCHAR(500),
                layout VARCHAR(50),
                area DECIMAL(10, 2),
                rent INTEGER,
                time_to_station INTEGER,
                real_rent DECIMAL(10, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 物件テーブルのインデックス作成
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_properties_user_id ON properties(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_properties_created_at ON properties(created_at DESC)
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


def get_all_users() -> list:
    """すべてのユーザーを取得"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id, username, created_at, updated_at
                FROM users
                ORDER BY created_at DESC
            """)
            users = cursor.fetchall()
            
            result = []
            for user in users:
                result.append({
                    "id": user["id"],
                    "username": user["username"],
                    "created_at": user["created_at"].isoformat() if user["created_at"] else None,
                    "updated_at": user["updated_at"].isoformat() if user["updated_at"] else None
                })
            return result
    except Exception as e:
        return [{"error": f"ユーザー一覧の取得に失敗しました: {str(e)}"}]


def create_property(user_id: int, mansion_name: str = None, address: str = None, 
                    layout: str = None, area: float = None, rent: int = None,
                    time_to_station: int = None, real_rent: float = None) -> dict:
    """物件情報を作成（ユーザーIDに紐づける）"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO properties (user_id, mansion_name, address, layout, area, rent, time_to_station, real_rent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, user_id, mansion_name, address, layout, area, rent, time_to_station, real_rent, created_at
            """, (user_id, mansion_name, address, layout, area, rent, time_to_station, real_rent))
            result = cursor.fetchone()
            return {
                "id": result["id"],
                "user_id": result["user_id"],
                "mansion_name": result["mansion_name"],
                "address": result["address"],
                "layout": result["layout"],
                "area": float(result["area"]) if result["area"] else None,
                "rent": result["rent"],
                "time_to_station": result["time_to_station"],
                "real_rent": float(result["real_rent"]) if result["real_rent"] else None,
                "created_at": result["created_at"].isoformat() if result["created_at"] else None
            }
    except Exception as e:
        return {"error": f"物件登録に失敗しました: {str(e)}"}


def get_properties_by_user_id(user_id: int) -> list:
    """特定のユーザーの物件一覧を取得"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, mansion_name, address, layout, area, rent, time_to_station, real_rent, created_at, updated_at
                FROM properties
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            properties = cursor.fetchall()
            
            result = []
            for prop in properties:
                result.append({
                    "id": prop["id"],
                    "user_id": prop["user_id"],
                    "mansion_name": prop["mansion_name"],
                    "address": prop["address"],
                    "layout": prop["layout"],
                    "area": float(prop["area"]) if prop["area"] else None,
                    "rent": prop["rent"],
                    "time_to_station": prop["time_to_station"],
                    "real_rent": float(prop["real_rent"]) if prop["real_rent"] else None,
                    "created_at": prop["created_at"].isoformat() if prop["created_at"] else None,
                    "updated_at": prop["updated_at"].isoformat() if prop["updated_at"] else None
                })
            return result
    except Exception as e:
        return [{"error": f"物件一覧の取得に失敗しました: {str(e)}"}]


def delete_property(user_id: int, mansion_name: str) -> dict:
    """物件を削除（user_idとmansion_nameの両方が一致するデータを削除）"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                DELETE FROM properties
                WHERE user_id = %s AND mansion_name = %s
                RETURNING id, mansion_name
            """, (user_id, mansion_name))
            result = cursor.fetchone()
            
            if result:
                return {
                    "message": "物件を削除しました",
                    "id": result["id"],
                    "mansion_name": result["mansion_name"]
                }
            else:
                return {"error": "物件が見つからないか、削除権限がありません"}
    except Exception as e:
        return {"error": f"物件削除に失敗しました: {str(e)}"}

