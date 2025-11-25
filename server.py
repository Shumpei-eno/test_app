from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
import nbformat
from salary_calc import process_monthly_income, check_input_completion
from database import init_database, create_user, verify_user, get_all_users, get_user_by_username, create_property, get_properties_by_user_id, delete_property

BASE_DIR = Path(__file__).parent
NOTEBOOK_PATH = BASE_DIR / "line_search.ipynb"  # 存在しない場合はエラーになるが、/run-notebookエンドポイントが呼ばれた時のみ

app = Flask(__name__)

# アプリケーション起動時にデータベースを初期化
try:
    init_database()
    print("データベースの初期化が完了しました")
except Exception as e:
    print(f"データベースの初期化中にエラーが発生しました: {e}")


def _inject_parameter(nb: nbformat.NotebookNode, selected_line: str) -> None:
    """line_search.ipynb の parameters セルへ沿線名を差し込む。"""
    def is_parameter_cell(cell: nbformat.NotebookNode) -> bool:
        if cell.get("cell_type") != "code":
            return False
        tags = cell.get("metadata", {}).get("tags", [])
        if isinstance(tags, list) and "parameters" in tags:
            return True
        source = "".join(cell.get("source", []))
        return "# Parameters" in source and "selected_line" in source

    target_cell = next((cell for cell in nb.cells if is_parameter_cell(cell)), None)

    if target_cell is None:
        raise RuntimeError("parameters セルが見つかりません。")

    serialized = json.dumps(selected_line, ensure_ascii=False)
    target_cell["source"] = "# Parameters\nselected_line = " + serialized


def execute_notebook(selected_line: str) -> str:
    """ノートブックを実行し、テキスト出力をまとめて返す。"""
    if not NOTEBOOK_PATH.exists():
        raise FileNotFoundError(f"ノートブックファイルが見つかりません: {NOTEBOOK_PATH}")
    nb = nbformat.read(str(NOTEBOOK_PATH), as_version=4)
    _inject_parameter(nb, selected_line)

    client = NotebookClient(nb, timeout=60, kernel_name="python3")
    client.execute()

    outputs: list[str] = []
    for cell in nb.cells:
        for output in cell.get("outputs", []):
            if "text" in output:
                outputs.append(output["text"])
            elif "data" in output and "text/plain" in output["data"]:
                outputs.append(output["data"]["text/plain"])

    return "".join(outputs).strip()


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response


@app.route("/")
def index():
    """index.htmlを提供するエンドポイント"""
    import os
    index_path = os.path.join(str(BASE_DIR), "index.html")
    if not os.path.exists(index_path):
        return jsonify({"error": "index.htmlが見つかりません"}), 404
    return send_from_directory(str(BASE_DIR), "index.html", mimetype="text/html")


@app.route("/<path:filename>")
def serve_static(filename):
    """静的ファイル（JS、CSS、JSONなど）を提供するエンドポイント"""
    import os
    # APIエンドポイントのパスを除外
    api_paths = ["run-notebook", "check-input-completion", "set-minute-salary"]
    if filename in api_paths or filename.startswith("api/"):
        return jsonify({"error": "アクセスが拒否されました"}), 403
    
    # 許可するファイル拡張子
    allowed_extensions = {'.js', '.css', '.json', '.html', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico'}
    
    # ファイル拡張子をチェック
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        return jsonify({"error": "アクセスが拒否されました"}), 403
    
    # ファイルが存在するかチェック
    file_path = os.path.join(str(BASE_DIR), filename)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return jsonify({"error": "ファイルが見つかりません"}), 404
    
    return send_from_directory(str(BASE_DIR), filename)


@app.route("/run-notebook", methods=["POST", "OPTIONS"])
def run_notebook_endpoint():
    if request.method == "OPTIONS":
        return ("", 204)

    payload = request.get_json(silent=True) or {}
    selected_line = (payload.get("line") or "").strip()

    if not selected_line:
        return jsonify({"error": "line パラメータを指定してください。"}), 400

    try:
        result_text = execute_notebook(selected_line)
    except CellExecutionError as exc:
        app.logger.exception("ノートブック実行中にエラーが発生しました")  # noqa: G004
        return jsonify({"error": "ノートブックの実行に失敗しました。", "detail": str(exc)}), 500
    except Exception as exc:  # pylint: disable=broad-except
        app.logger.exception("サーバー内部エラーが発生しました")  # noqa: G004
        return jsonify({"error": "サーバー内部エラーが発生しました。", "detail": str(exc)}), 500

    return jsonify({"result": result_text})


@app.route("/set-salary", methods=["POST", "OPTIONS"])
def set_salary_endpoint():
    if request.method == "OPTIONS":
        return ("", 204)

    payload = request.get_json(silent=True) or {}
    monthly_income_str = payload.get("monthly_income", "").strip()

    if not monthly_income_str:
        return jsonify({"error": "月収を指定してください。"}), 400

    try:
        monthly_income = float(monthly_income_str)
    except ValueError:
        return jsonify({"error": "月収は数値である必要があります。"}), 400

    try:
        result = process_monthly_income(monthly_income)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as exc:  # pylint: disable=broad-except
        app.logger.exception("サーバー内部エラーが発生しました")  # noqa: G004
        return jsonify({"error": "サーバー内部エラーが発生しました。", "detail": str(exc)}), 500


@app.route("/check-input-completion", methods=["POST", "OPTIONS"])
def check_input_completion_endpoint():
    """家賃と対象駅までの時間の入力完了を確認するエンドポイント"""
    print("=" * 50)
    print("check-input-completionエンドポイントにリクエストが到達しました")
    print(f"リクエストメソッド: {request.method}")
    print("=" * 50)
    
    if request.method == "OPTIONS":
        print("OPTIONSリクエストを処理します")
        return ("", 204)

    print("=" * 50)
    print("check-input-completionエンドポイントが呼び出されました")
    print("=" * 50)
    
    payload = request.get_json(silent=True) or {}
    print("受信したペイロード:", payload)
    
    rent_input = payload.get("rent_input")
    time_to_station = payload.get("time_to_station")
    time_to_kamiyacho = payload.get("time_to_kamiyacho")
    minute_salary = payload.get("minute_salary")
    
    print(f"rent_input: {rent_input}, time_to_station: {time_to_station}, time_to_kamiyacho: {time_to_kamiyacho}, minute_salary: {minute_salary}")

    if rent_input is None:
        print("エラー: 家賃が指定されていません")
        return jsonify({"error": "家賃を指定してください。"}), 400
    if time_to_station is None:
        print("エラー: 対象駅までの時間が指定されていません")
        return jsonify({"error": "対象駅までの時間を指定してください。"}), 400

    print("check_input_completion関数を呼び出します")
    try:
        result = check_input_completion(rent_input=rent_input, time_to_station=time_to_station, time_to_kamiyacho=time_to_kamiyacho, minute_salary=minute_salary)
        print("check_input_completion関数の結果:", result)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as exc:  # pylint: disable=broad-except
        print("=" * 50)
        print("エラーが発生しました:", str(exc))
        print("=" * 50)
        app.logger.exception("サーバー内部エラーが発生しました")  # noqa: G004
        return jsonify({"error": "サーバー内部エラーが発生しました。", "detail": str(exc)}), 500


@app.route("/register", methods=["POST", "OPTIONS"])
def register_endpoint():
    """ユーザー登録エンドポイント"""
    if request.method == "OPTIONS":
        return ("", 204)
    
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "").strip()
    password = payload.get("password", "").strip()
    
    print(f"登録リクエスト受信: username={username}, password_length={len(password)}")
    
    # バリデーション
    if not username:
        error_msg = "ユーザーネームを入力してください"
        print(f"エラー: {error_msg}")
        return jsonify({"error": error_msg}), 400
    
    if len(username) < 3:
        error_msg = "ユーザーネームは3文字以上で入力してください"
        print(f"エラー: {error_msg}")
        return jsonify({"error": error_msg}), 400
    
    if not password:
        error_msg = "パスワードを入力してください"
        print(f"エラー: {error_msg}")
        return jsonify({"error": error_msg}), 400
    
    if len(password) < 6:
        error_msg = "パスワードは6文字以上で入力してください"
        print(f"エラー: {error_msg}")
        return jsonify({"error": error_msg}), 400
    
    try:
        result = create_user(username, password)
        if "error" in result:
            print(f"ユーザー作成エラー: {result['error']}")
            return jsonify(result), 400
        print(f"ユーザー登録成功: username={username}, id={result.get('id')}")
        return jsonify({"message": "ユーザー登録が完了しました", "user": result}), 201
    except Exception as exc:
        app.logger.exception("ユーザー登録中にエラーが発生しました")
        print(f"例外発生: {str(exc)}")
        return jsonify({"error": "サーバー内部エラーが発生しました。", "detail": str(exc)}), 500


@app.route("/login", methods=["POST", "OPTIONS"])
def login_endpoint():
    """ログインエンドポイント"""
    if request.method == "OPTIONS":
        return ("", 204)
    
    payload = request.get_json(silent=True) or {}
    username = payload.get("username", "").strip()
    password = payload.get("password", "").strip()
    
    # バリデーション
    if not username:
        return jsonify({"error": "ユーザーネームを入力してください"}), 400
    
    if not password:
        return jsonify({"error": "パスワードを入力してください"}), 400
    
    try:
        result = verify_user(username, password)
        if "error" in result:
            return jsonify(result), 401
        return jsonify({"message": "ログインに成功しました", "user": result}), 200
    except Exception as exc:
        app.logger.exception("ログイン中にエラーが発生しました")
        return jsonify({"error": "サーバー内部エラーが発生しました。", "detail": str(exc)}), 500


@app.route("/api/users", methods=["GET", "OPTIONS"])
def get_users_endpoint():
    """すべてのユーザーを取得するAPIエンドポイント"""
    if request.method == "OPTIONS":
        return ("", 204)
    
    try:
        users = get_all_users()
        if users and len(users) == 1 and "error" in users[0]:
            return jsonify(users[0]), 500
        return jsonify({"users": users, "count": len(users)}), 200
    except Exception as exc:
        app.logger.exception("ユーザー一覧取得中にエラーが発生しました")
        return jsonify({"error": "サーバー内部エラーが発生しました。", "detail": str(exc)}), 500


@app.route("/api/users/<username>", methods=["GET", "OPTIONS"])
def get_user_endpoint(username):
    """特定のユーザーを取得するAPIエンドポイント"""
    if request.method == "OPTIONS":
        return ("", 204)
    
    try:
        user = get_user_by_username(username)
        if user is None:
            return jsonify({"error": "ユーザーが見つかりません"}), 404
        if "error" in user:
            return jsonify(user), 500
        return jsonify({"user": user}), 200
    except Exception as exc:
        app.logger.exception("ユーザー取得中にエラーが発生しました")
        return jsonify({"error": "サーバー内部エラーが発生しました。", "detail": str(exc)}), 500


@app.route("/api/properties", methods=["POST", "OPTIONS"])
def create_property_endpoint():
    """物件情報を登録するAPIエンドポイント"""
    if request.method == "OPTIONS":
        return ("", 204)
    
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    
    if not user_id:
        return jsonify({"error": "ユーザーIDが必要です"}), 400
    
    try:
        result = create_property(
            user_id=user_id,
            mansion_name=payload.get("mansion_name"),
            address=payload.get("address"),
            layout=payload.get("layout"),
            area=payload.get("area"),
            rent=payload.get("rent"),
            time_to_station=payload.get("time_to_station"),
            real_rent=payload.get("real_rent")
        )
        
        if "error" in result:
            return jsonify(result), 400
        return jsonify({"message": "物件を登録しました", "property": result}), 201
    except Exception as exc:
        app.logger.exception("物件登録中にエラーが発生しました")
        return jsonify({"error": "サーバー内部エラーが発生しました。", "detail": str(exc)}), 500


@app.route("/api/properties/<int:user_id>", methods=["GET", "OPTIONS"])
def get_properties_endpoint(user_id):
    """特定のユーザーの物件一覧を取得するAPIエンドポイント"""
    if request.method == "OPTIONS":
        return ("", 204)
    
    try:
        properties = get_properties_by_user_id(user_id)
        if properties and len(properties) == 1 and "error" in properties[0]:
            return jsonify(properties[0]), 500
        return jsonify({"properties": properties, "count": len(properties)}), 200
    except Exception as exc:
        app.logger.exception("物件一覧取得中にエラーが発生しました")
        return jsonify({"error": "サーバー内部エラーが発生しました。", "detail": str(exc)}), 500


@app.route("/api/properties/<int:property_id>", methods=["DELETE", "OPTIONS"])
def delete_property_endpoint(property_id):
    """物件を削除するAPIエンドポイント"""
    if request.method == "OPTIONS":
        return ("", 204)
    
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    
    if not user_id:
        return jsonify({"error": "ユーザーIDが必要です"}), 400
    
    try:
        result = delete_property(property_id, user_id)
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result), 200
    except Exception as exc:
        app.logger.exception("物件削除中にエラーが発生しました")
        return jsonify({"error": "サーバー内部エラーが発生しました。", "detail": str(exc)}), 500


if __name__ == "__main__":
    # Renderなどのクラウド環境では環境変数PORTを使用
    # ローカルでは5001を使用（macOSのAirPlay Receiverが5000を使用するため）
    port = int(os.environ.get("PORT", 5001))
    # host="0.0.0.0"にすることで、同じネットワーク上の他のデバイスからもアクセス可能
    app.run(host="0.0.0.0", port=port, debug=False)

