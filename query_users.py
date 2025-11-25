"""SQLクエリを実行してユーザーデータを確認するスクリプト"""
from database import get_db_cursor

def execute_query(query: str):
    """SQLクエリを実行して結果を表示"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute(query)
            
            # SELECT文の場合
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                
                if not results:
                    print("結果がありません。")
                    return
                
                # カラム名を取得
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # ヘッダーを表示
                if columns:
                    print("\n" + "=" * 80)
                    header = " | ".join(f"{col:<20}" for col in columns)
                    print(header)
                    print("-" * 80)
                    
                    # データを表示
                    for row in results:
                        values = [str(row[col] if col in row else row.get(col, ''))[:20] for col in columns]
                        print(" | ".join(f"{val:<20}" for val in values))
                    
                    print("=" * 80)
                    print(f"合計: {len(results)} 行\n")
            else:
                # INSERT, UPDATE, DELETEなどの場合
                print(f"✓ クエリが正常に実行されました。")
                
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")


def show_all_users():
    """すべてのユーザーを表示"""
    execute_query("SELECT id, username, created_at, updated_at FROM users ORDER BY id")


def show_table_info():
    """テーブル構造を表示"""
    query = """
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position;
    """
    execute_query(query)


def show_database_info():
    """データベース情報を表示"""
    query = """
        SELECT 
            datname as database_name,
            pg_size_pretty(pg_database_size(datname)) as size
        FROM pg_database
        WHERE datname NOT IN ('template0', 'template1', 'postgres')
        ORDER BY datname;
    """
    execute_query(query)


def show_table_size():
    """テーブルサイズを表示"""
    query = """
        SELECT 
            pg_size_pretty(pg_total_relation_size('users')) as total_size,
            pg_size_pretty(pg_relation_size('users')) as table_size,
            pg_size_pretty(pg_indexes_size('users')) as indexes_size;
    """
    execute_query(query)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'users' or command == 'list':
            show_all_users()
        elif command == 'info' or command == 'table':
            show_table_info()
        elif command == 'db' or command == 'database':
            show_database_info()
        elif command == 'size':
            show_table_size()
        elif command == 'query' and len(sys.argv) > 2:
            # カスタムクエリを実行
            query = " ".join(sys.argv[2:])
            execute_query(query)
        else:
            print("使用法:")
            print("  python query_users.py users      # すべてのユーザーを表示")
            print("  python query_users.py info       # テーブル構造を表示")
            print("  python query_users.py db         # データベース情報を表示")
            print("  python query_users.py size       # テーブルサイズを表示")
            print("  python query_users.py query \"SELECT * FROM users\"  # カスタムクエリ")
    else:
        # デフォルトでユーザー一覧を表示
        show_all_users()
        print("\n" + "-" * 80)
        print("その他のコマンド:")
        print("  python query_users.py info    # テーブル構造を表示")
        print("  python query_users.py size    # テーブルサイズを表示")

