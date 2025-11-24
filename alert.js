// alert.js
// アラート表示用のコード

// 半角数字のみかどうかをチェック
function validateHalfWidthNumber(value) {
  if (!value || value.trim() === '') {
    return true; // 空の場合は有効とする
  }
  // 半角数字のみかチェック
  return /^[0-9]+$/.test(value);
}

// 月収入力のバリデーション
function validateMonthlyIncome(inputElement, errorElement) {
  const value = inputElement.value;
  
  if (validateHalfWidthNumber(value)) {
    // 有効な場合、エラーメッセージを非表示
    errorElement.textContent = '';
    errorElement.classList.remove('active');
    return true;
  } else {
    // 無効な場合、エラーメッセージを表示
    errorElement.textContent = '半角の数字を入れてください';
    errorElement.classList.add('active');
    return false;
  }
}

// 家賃入力のバリデーション
function validateRentInput(inputElement, errorElement) {
  const value = inputElement.value;
  
  if (validateHalfWidthNumber(value)) {
    // 有効な場合、エラーメッセージを非表示
    if (errorElement) {
      errorElement.textContent = '';
      errorElement.classList.remove('active');
    }
    return true;
  } else {
    // 無効な場合、エラーメッセージを表示
    if (errorElement) {
      errorElement.textContent = '半角の数字を入れてください';
      errorElement.classList.add('active');
    }
    return false;
  }
}

// 時間入力のバリデーション
function validateTimeInput(inputElement, errorElement) {
  const value = inputElement.value;
  
  if (validateHalfWidthNumber(value)) {
    // 有効な場合、エラーメッセージを非表示
    if (errorElement) {
      errorElement.textContent = '';
      errorElement.classList.remove('active');
    }
    return true;
  } else {
    // 無効な場合、エラーメッセージを表示
    if (errorElement) {
      errorElement.textContent = '半角の数字を入れてください';
      errorElement.classList.add('active');
    }
    return false;
  }
}
