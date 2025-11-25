"""登録済みユーザーを表示するスクリプト"""
from database import get_all_users

def view_all_users():
    """すべてのユーザーを表示"""
    try:
        users = get_all_users()
        
        if not users or (len(users) == 1 and "error" in users[0]):
            if users and "error" in users[0]:
                print(f"エラー: {users[0]['error']}")
            else:
                print("登録されているユーザーはありません。")
            return
        
        print("\n" + "=" * 80)
        print("登録済みユーザー一覧")
        print("=" * 80)
        print(f"{'ID':<5} {'ユーザーネーム':<30} {'登録日時':<25} {'更新日時':<25}")
        print("-" * 80)
        
        for user in users:
            print(f"{user['id']:<5} {user['username']:<30} {user['created_at'] or 'N/A':<25} {user['updated_at'] or 'N/A':<25}")
        
        print("=" * 80)
        print(f"合計: {len(users)} ユーザー\n")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    view_all_users()

