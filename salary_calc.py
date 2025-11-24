"""月収から分給を計算するモジュール"""
from __future__ import annotations
from typing import Optional


def process_monthly_income(monthly_income: float) -> dict:
    """
    月収から分給を計算する。
    
    Args:
        monthly_income: 月収（円）
    
    Returns:
        計算結果の辞書
    """
    if monthly_income < 0:
        return {"error": "月収は0以上の値である必要があります。"}
    
    if monthly_income == 0:
        return {"error": "月収は0より大きい値である必要があります。"}
    
    # 月の出勤日数：20日
    # 日の労働時間：7時間45分 = 7.75時間
    work_days_per_month = 20
    work_hours_per_day = 7.75
    
    # 月の総労働時間を計算
    total_work_hours = work_days_per_month * work_hours_per_day
    
    # 時間を分に変換
    total_work_minutes = total_work_hours * 60
    
    # 分給を計算（月収 ÷ 月の総労働時間（分））
    average_minute_salary = monthly_income / total_work_minutes
    
    print(f"月収: {monthly_income}円")
    print(f"月の出勤日数: {work_days_per_month}日")
    print(f"日の労働時間: {work_hours_per_day}時間")
    print(f"月の総労働時間: {total_work_hours}時間 ({total_work_minutes}分)")
    print(f"分給: {average_minute_salary:.2f}円/分")
    
    return {
        "monthly_income": monthly_income,
        "work_days_per_month": work_days_per_month,
        "work_hours_per_day": work_hours_per_day,
        "total_work_hours": total_work_hours,
        "total_work_minutes": total_work_minutes,
        "average_minute_salary": average_minute_salary
    }


def check_input_completion(rent_input: float, time_to_station: float, time_to_kamiyacho: Optional[float] = None, minute_salary: Optional[float] = None) -> dict:
    """
    家賃と対象駅までの時間の入力が完了したことを確認する。
    
    Args:
        rent_input: 家賃に入力した数値（円）
        time_to_station: 対象駅までの時間に入力した時間の数値（分）
        time_to_kamiyacho: チェックを入れた駅の神谷町までの時間（分）。オプション。
        minute_salary: あなたの分給で算出した数値（円/分）。オプション。
    
    Returns:
        処理結果の辞書
    """
    print("check_input_completion関数が呼び出されました。")
    
    # バリデーション
    if rent_input is None:
        return {"error": "家賃を指定してください。"}
    
    if time_to_station is None:
        return {"error": "対象駅までの時間を指定してください。"}
    
    try:
        rent_input = float(rent_input)
        time_to_station = float(time_to_station)
        if time_to_kamiyacho is not None:
            time_to_kamiyacho = float(time_to_kamiyacho)
        if minute_salary is not None:
            minute_salary = float(minute_salary)
    except (ValueError, TypeError):
        return {"error": "数値である必要があります。"}
    
    if rent_input < 0:
        return {"error": "家賃は0以上の値である必要があります。"}
    
    if time_to_station < 0:
        return {"error": "対象駅までの時間は0以上の値である必要があります。"}
    
    if time_to_kamiyacho is not None and time_to_kamiyacho < 0:
        return {"error": "神谷町までの時間は0以上の値である必要があります。"}
    
    if minute_salary is not None and minute_salary < 0:
        return {"error": "分給は0以上の値である必要があります。"}
    
    print(f"家賃: {rent_input}円")
    print(f"対象駅までの時間: {time_to_station}分")
    if time_to_kamiyacho is not None:
        print(f"神谷町までの時間: {time_to_kamiyacho}分")
    if minute_salary is not None:
        print(f"分給: {minute_salary}円/分")
    
    # 実質家賃の計算
    real_rent_fee = rent_input
    if minute_salary is not None and time_to_kamiyacho is not None:
        # 通勤時間 = 神谷町までの時間 + 対象駅までの時間
        total_commute_time = time_to_kamiyacho + time_to_station
        # 実質家賃 = 家賃 + (通勤時間 × 分給 × 20)
        real_rent_fee = rent_input + (total_commute_time * minute_salary * 20)
        print(f"実質家賃: {real_rent_fee}円")
    else:
        print("実質家賃の計算には分給と神谷町までの時間が必要です")
    
    print("入力が完了しました")
    
    result = {
        "status": "ok",
        "message": "入力が完了しました",
        "rent_input": rent_input,
        "time_to_station": time_to_station,
        "real_rent_fee": real_rent_fee
    }
    
    if time_to_kamiyacho is not None:
        result["time_to_kamiyacho"] = time_to_kamiyacho
    
    if minute_salary is not None:
        result["minute_salary"] = minute_salary
    
    return result