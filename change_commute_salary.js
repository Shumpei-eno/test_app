// change_commute_salary.js
// 通勤時間の分給換算チャート関連のコード

// グローバル変数（HTMLファイル内の変数と共有）
let salaryChart = null;
let currentMinuteSalary = null; // 現在の分給を保存

// 分給換算チャートを表示
async function displaySalaryChart(stations, times, transfers) {
  const salaryChartContainer = document.getElementById('salary-chart-container');
  
  if (!salaryChartContainer) {
    console.error('salary-chart-containerが見つかりません');
    return;
  }

  // 既存のチャートを破棄
  if (salaryChart) {
    salaryChart.destroy();
    salaryChart = null;
  }

  // チャートコンテナを表示
  salaryChartContainer.classList.add('active');

  // 分給が設定されていない場合は空のチャートを表示
  if (currentMinuteSalary === null || currentMinuteSalary === undefined) {
    const emptySalaryValues = stations ? stations.map(() => 0) : [];
    const emptyStations = stations && stations.length > 0 ? stations : [];
    
    const ctx = document.getElementById('salaryChart');
    salaryChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: emptyStations,
        datasets: [{
          label: '給料換算（円）',
          data: emptySalaryValues,
          backgroundColor: 'rgba(95, 179, 211, 0.8)',
          borderColor: 'rgba(95, 179, 211, 1)',
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
                return `給料換算: ${Math.round(context.parsed.y).toLocaleString()}円`;
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
              text: '給料換算（円）'
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

  // 分給換算値を計算
  const salaryValues = stations.map((station, index) => {
    const time = times && times[index] !== null && times[index] !== undefined ? times[index] : 0;
    const transfer = transfers && transfers[index] !== null && transfers[index] !== undefined ? transfers[index] : 0;
    // 時間 + (乗換回数 × 7)
    const adjustedTime = (time + (transfer * 7)) * 2;
    // 分給 × 調整後の時間
    return currentMinuteSalary * adjustedTime;
  });

  // チャートを作成
  const ctx = document.getElementById('salaryChart');
  salaryChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: stations,
      datasets: [{
        label: '給料換算（円）',
        data: salaryValues,
        backgroundColor: 'rgba(95, 179, 211, 0.8)',
        borderColor: 'rgba(95, 179, 211, 1)',
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
                return `給料換算: ${Math.round(context.parsed.y).toLocaleString()}円`;
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
              text: '給料換算（円）'
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
}

// 分給を設定する関数（外部から呼び出し可能）
function setMinuteSalary(salary) {
  currentMinuteSalary = salary;
}

// 現在の分給を取得する関数（外部から呼び出し可能）
function getMinuteSalary() {
  return currentMinuteSalary;
}

