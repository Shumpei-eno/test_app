// real_rent_fee.js
// 実質家賃チャート関連のコード

let realRentChart = null;

// 初期状態で空のチャートを表示
function initRealRentChart() {
  const realRentChartContainer = document.getElementById('real-rent-chart-container');
  
  if (!realRentChartContainer) {
    console.error('real-rent-chart-containerが見つかりません');
    return;
  }

  // 既存のチャートを破棄
  if (realRentChart) {
    realRentChart.destroy();
    realRentChart = null;
  }

  // チャートコンテナを表示
  realRentChartContainer.classList.add('active');

  // 空のチャートを作成
  const ctx = document.getElementById('realRentChart');
  realRentChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [{
        label: '実質家賃（円）',
        data: [],
        backgroundColor: 'rgba(255, 165, 0, 0.8)', // オレンジ
        borderColor: 'rgba(255, 165, 0, 1)', // オレンジ
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `実質家賃: ${context.parsed.y.toLocaleString()}円`;
            }
          }
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: '駅名'
          },
          ticks: {
            maxRotation: 45,
            minRotation: 45
          }
        },
        y: {
          title: {
            display: true,
            text: '実質家賃（円）'
          },
          beginAtZero: true
        }
      }
    }
  });
}

// 実質家賃チャートを表示
async function displayRealRentChart(stations, rents, times, transfers) {
  const realRentChartContainer = document.getElementById('real-rent-chart-container');
  
  if (!realRentChartContainer) {
    console.error('real-rent-chart-containerが見つかりません');
    return;
  }

  // 既存のチャートを破棄
  if (realRentChart) {
    realRentChart.destroy();
    realRentChart = null;
  }

  // チャートコンテナを表示
  realRentChartContainer.classList.add('active');

  // 分給を取得（change_commute_salary.jsから）
  const minuteSalary = getMinuteSalary();
  
  // データがない場合、または分給が設定されていない場合は空のチャートを表示
  if (!stations || stations.length === 0 || minuteSalary === null || minuteSalary === undefined) {
    const ctx = document.getElementById('realRentChart');
    realRentChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: stations && stations.length > 0 ? stations : [],
        datasets: [{
          label: '実質家賃（円）',
          data: stations && stations.length > 0 ? stations.map(() => 0) : [],
          backgroundColor: 'rgba(255, 165, 0, 0.8)', // オレンジ
          borderColor: 'rgba(255, 165, 0, 1)', // オレンジ
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `実質家賃: ${Math.round(context.parsed.y).toLocaleString()}円`;
              }
            }
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: '駅名'
            },
            ticks: {
              maxRotation: 45,
              minRotation: 45
            }
          },
          y: {
            title: {
              display: true,
              text: '実質家賃（円）'
            },
            beginAtZero: true,
            ticks: {
              callback: function(value) {
                return Math.round(value).toLocaleString();
              }
            }
          }
        }
      }
    });
    return;
  }

  // 実質家賃を計算
  // 家賃相場（万円）× 10000 + 通勤時間の分給換算（円）× 20
  const realRentValues = stations.map((station, index) => {
    // 家賃相場（万円）を円に変換
    const rentInYen = (rents && rents[index] !== null && rents[index] !== undefined) 
      ? rents[index] * 10000 
      : 0;
    
    // 通勤時間の分給換算を計算
    const time = times && times[index] !== null && times[index] !== undefined ? times[index] : 0;
    const transfer = transfers && transfers[index] !== null && transfers[index] !== undefined ? transfers[index] : 0;
    // 時間 + (乗換回数 × 7)
    const adjustedTime = (time + (transfer * 7)) * 2;
    
    // 通勤時間の分給換算（円）
    const commuteSalaryValue = minuteSalary * adjustedTime;
    
    // 実質家賃 = 家賃相場（円）+ 通勤時間の分給換算（円）× 20
    return Math.round(rentInYen + (commuteSalaryValue * 20));
  });

  // チャートを作成
  const ctx = document.getElementById('realRentChart');
  realRentChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: stations,
      datasets: [{
        label: '実質家賃（円）',
        data: realRentValues,
        backgroundColor: 'rgba(255, 165, 0, 0.8)', // オレンジ
        borderColor: 'rgba(255, 165, 0, 1)', // オレンジ
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `実質家賃: ${context.parsed.y.toLocaleString()}円`;
            }
          }
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: '駅名'
          },
          ticks: {
            maxRotation: 45,
            minRotation: 45
          }
        },
        y: {
          title: {
            display: true,
            text: '実質家賃（円）'
          },
          beginAtZero: true
        }
      }
    }
  });
}

// 実質家賃の表を表示
function displayRealRentTable(stations, rents, times, transfers, minuteSalary) {
  const tableContainer = document.getElementById('real-rent-table-container');
  
  if (!tableContainer) {
    console.error('real-rent-table-containerが見つかりません');
    return;
  }

  // 表を常に表示
  tableContainer.classList.add('active');

  // カラム名を固定表示するヘッダーを追加
  let html = '<div class="real-rent-table-header">';
  html += '<div class="real-rent-table-header-cell">駅名</div>';
  html += '<div class="real-rent-table-header-cell">実質家賃（円）</div>';
  html += '</div>';

  // データがない場合、または分給が設定されていない場合は空の表を表示
  if (!stations || stations.length === 0 || !minuteSalary) {
    html += '<table class="real-rent-table">';
    html += '<tbody>';
    html += '</tbody>';
    html += '</table>';
    tableContainer.innerHTML = html;
    return;
  }

  // 実質家賃を計算
  // 家賃相場（万円）× 10000 + 通勤時間の分給換算（円）× 20
  const realRentValues = stations.map((station, index) => {
    // 家賃相場（万円）を円に変換
    const rentInYen = (rents && rents[index] !== null && rents[index] !== undefined) 
      ? rents[index] * 10000 
      : 0;
    
    // 通勤時間の分給換算を計算
    const time = times && times[index] !== null && times[index] !== undefined ? times[index] : 0;
    const transfer = transfers && transfers[index] !== null && transfers[index] !== undefined ? transfers[index] : 0;
    // 時間 + (乗換回数 × 7)
    const adjustedTime = time + (transfer * 7);
    
    // 通勤時間の分給換算（円）
    const commuteSalaryValue = minuteSalary * adjustedTime;
    
    // 実質家賃 = 家賃相場（円）+ 通勤時間の分給換算（円）× 20
    return Math.round(rentInYen + (commuteSalaryValue * 20));
  });

  // 表のHTMLを生成
  html += '<table class="real-rent-table">';
  html += '<tbody>';
  
  stations.forEach((station, index) => {
    html += '<tr>';
    html += `<td>${station}</td>`;
    html += `<td>${realRentValues[index].toLocaleString()}</td>`;
    html += '</tr>';
  });
  
  html += '</tbody>';
  html += '</table>';

  tableContainer.innerHTML = html;
}
