// chart_code.js
// チャート表示用のコード

let fixData = null;

// fix_data.jsonを読み込む
async function loadFixData() {
  if (fixData) {
    return fixData;
  }
  try {
    const response = await fetch('fix_data.json');
    fixData = await response.json();
    return fixData;
  } catch (error) {
    console.error('fix_data.jsonの読み込みに失敗しました:', error);
    return null;
  }
}

// 選択された鉄道(a)と沿線(b)から駅のリストを取得
function getStations(data, railway, line) {
  if (!data || !Array.isArray(data)) {
    return [];
  }

  // 沿線名から鉄道名の接頭辞を削除
  let cleanLine = line;
  if (line && railway) {
    cleanLine = line.replace(new RegExp(`^${railway}`), '').trim();
    cleanLine = cleanLine.replace(/^(JR|ＪＲ|東京メトロ|西武鉄道)/, '').trim();
  }

  const stations = new Set(); // 重複を避けるためにSetを使用

  // 配列をループして、駅名を抽出
  for (const row of data) {
    for (const key of Object.keys(row)) {
      const keyMatch = key.match(/^\('([^']+)',\s*'([^']+)',\s*'([^']+)'\)$/);
      if (!keyMatch) continue;

      const [, keyRailway, keyLine, keyItem] = keyMatch;

      // 鉄道名と路線名が一致するか確認
      const railwayMatch = keyRailway === railway;
      let lineMatch = false;
      if (keyLine === line || keyLine === cleanLine) {
        lineMatch = true;
      } else if (line.includes(keyLine) || cleanLine.includes(keyLine)) {
        lineMatch = true;
      } else if (keyLine.includes(cleanLine) || keyLine.includes(line.replace(railway, '').trim())) {
        lineMatch = true;
      }

      if (railwayMatch && lineMatch && keyItem === '駅') {
        const station = row[key];
        if (station && station !== null && station !== '') {
          stations.add(station);
        }
      }
    }
  }

  return Array.from(stations).sort(); // ソートして返す
}

// 選択された鉄道、沿線、駅から詳細情報を取得
function getStationDetails(data, railway, line, station) {
  if (!data || !Array.isArray(data) || !station) {
    return { time: null, transfers: null, rent: null };
  }

  // 沿線名から鉄道名の接頭辞を削除
  let cleanLine = line;
  if (line && railway) {
    cleanLine = line.replace(new RegExp(`^${railway}`), '').trim();
    cleanLine = cleanLine.replace(/^(JR|ＪＲ|東京メトロ|西武鉄道)/, '').trim();
  }

  let time = null;
  let transfers = null;
  let rent = null;

  // 配列をループして、該当する駅の情報を取得
  for (const row of data) {
    let foundStation = false;
    let rowTime = null;
    let rowTransfers = null;
    let rowRent = null;

    for (const key of Object.keys(row)) {
      const keyMatch = key.match(/^\('([^']+)',\s*'([^']+)',\s*'([^']+)'\)$/);
      if (!keyMatch) continue;

      const [, keyRailway, keyLine, keyItem] = keyMatch;

      // 鉄道名と路線名が一致するか確認
      const railwayMatch = keyRailway === railway;
      let lineMatch = false;
      if (keyLine === line || keyLine === cleanLine) {
        lineMatch = true;
      } else if (line.includes(keyLine) || cleanLine.includes(keyLine)) {
        lineMatch = true;
      } else if (keyLine.includes(cleanLine) || keyLine.includes(line.replace(railway, '').trim())) {
        lineMatch = true;
      }

      if (railwayMatch && lineMatch) {
        const value = row[key];

        // 駅名が一致する場合
        if (keyItem === '駅' && value === station) {
          foundStation = true;
        }
        // 神谷町までの時間(分)
        else if (keyItem === '神谷町までの時間(分)') {
          if (typeof value === 'string') {
            const timeMatch = value.match(/(\d+)/);
            if (timeMatch) {
              rowTime = parseFloat(timeMatch[1]);
            } else if (!isNaN(parseFloat(value))) {
              rowTime = parseFloat(value);
            }
          } else if (value !== null && value !== undefined && !isNaN(value)) {
            rowTime = parseFloat(value);
          }
        }
        // 乗換回数
        else if (keyItem === '乗換回数') {
          if (value !== null && value !== undefined && !isNaN(value)) {
            rowTransfers = parseFloat(value);
          }
        }
        // 家賃相場(万円)
        else if (keyItem === '家賃相場(万円)') {
          if (value !== null && value !== undefined && !isNaN(value)) {
            rowRent = parseFloat(value);
          }
        }
      }
    }

    // 同じ行に駅名が一致する場合、時間、乗換回数、家賃相場を取得
    if (foundStation) {
      if (rowTime !== null) {
        time = rowTime;
      }
      if (rowTransfers !== null) {
        transfers = rowTransfers;
      }
      if (rowRent !== null) {
        rent = rowRent;
      }
      break; // 見つかったら終了
    }
  }

  return { time, transfers, rent };
}

// 選択された鉄道(a)と沿線(b)からデータを抽出
function extractData(data, railway, line) {
  if (!data) {
    return { stations: [], rents: [], times: [], transfers: [] };
  }

  // データが配列形式かどうかを確認
  if (!Array.isArray(data)) {
    console.warn('データが配列形式ではありません');
    return { stations: [], rents: [], times: [], transfers: [] };
  }

  // 沿線名から鉄道名の接頭辞を削除（例：「JR山手線」→「山手線」）
  let cleanLine = line;
  if (line && railway) {
    // 「JR山手線」のような形式から「JR」を削除
    cleanLine = line.replace(new RegExp(`^${railway}`), '').trim();
    // 全角・半角の「JR」や「ＪＲ」も削除
    cleanLine = cleanLine.replace(/^(JR|ＪＲ|東京メトロ|西武鉄道)/, '').trim();
  }

  const stations = [];
  const rents = [];
  const times = [];
  const transfers = [];

  // 配列をループして、各行から駅、家賃、時間、乗換回数のデータを抽出
  for (const row of data) {
    let station = null;
    let rent = null;
    let time = null;
    let transfer = null;

    // オブジェクトのすべてのキーを確認
    for (const key of Object.keys(row)) {
      // キーが `('鉄道', '路線', '項目')` 形式か確認
      const keyMatch = key.match(/^\('([^']+)',\s*'([^']+)',\s*'([^']+)'\)$/);
      if (!keyMatch) continue;

      const [, keyRailway, keyLine, keyItem] = keyMatch;

      // 鉄道名と路線名が一致するか確認（接頭辞を考慮）
      const railwayMatch = keyRailway === railway;
      
      // 路線名のマッチング（複数のパターンを試す）
      let lineMatch = false;
      // パターン1: 完全一致
      if (keyLine === line || keyLine === cleanLine) {
        lineMatch = true;
      }
      // パターン2: 選択された路線名にキーの路線名が含まれる（例：「東京メトロ日比谷線」に「日比谷線」が含まれる）
      else if (line.includes(keyLine) || cleanLine.includes(keyLine)) {
        lineMatch = true;
      }
      // パターン3: キーの路線名に選択された路線名が含まれる（逆方向）
      else if (keyLine.includes(cleanLine) || keyLine.includes(line.replace(railway, '').trim())) {
        lineMatch = true;
      }

      if (railwayMatch && lineMatch) {
        const value = row[key];
        
        // 項目が「駅」の場合
        if (keyItem === '駅' && value && value !== null && value !== '') {
          station = value;
        }
        // 項目が「家賃相場(万円)」の場合
        else if (keyItem === '家賃相場(万円)' && value !== null && value !== undefined && !isNaN(value)) {
          rent = parseFloat(value);
        }
        // 項目が「神谷町までの時間(分)」の場合
        else if (keyItem === '神谷町までの時間(分)') {
          // 「14分」のような形式から数値のみを抽出
          if (typeof value === 'string') {
            const timeMatch = value.match(/(\d+)/);
            if (timeMatch) {
              time = parseFloat(timeMatch[1]);
            } else if (!isNaN(parseFloat(value))) {
              time = parseFloat(value);
            }
          } else if (value !== null && value !== undefined && !isNaN(value)) {
            time = parseFloat(value);
          }
        }
        // 項目が「乗換回数」の場合
        else if (keyItem === '乗換回数') {
          if (value !== null && value !== undefined && !isNaN(value)) {
            transfer = parseFloat(value);
          }
        }
      }
    }

    // 同じ行に駅と家賃の両方がある場合のみ追加（時間と乗換回数はオプション）
    if (station && rent !== null && !isNaN(rent)) {
      stations.push(station);
      rents.push(rent);
      times.push(time !== null && !isNaN(time) ? time : null);
      transfers.push(transfer !== null && !isNaN(transfer) ? transfer : null);
    }
  }

  if (stations.length === 0 || rents.length === 0) {
    console.warn(`データが見つかりません: railway="${railway}", line="${line}", cleanLine="${cleanLine}"`);
    console.log('検索条件:', { railway, line, cleanLine });
    if (data.length > 0) {
      console.log('データ構造のサンプル（最初の3行）:', data.slice(0, 3));
      // 実際のキーを確認
      const sampleKeys = Object.keys(data[0]).filter(k => k.startsWith('('));
      console.log('サンプルキー:', sampleKeys.slice(0, 10));
      
      // 実際の鉄道名と路線名を抽出して表示
      const foundRailways = new Set();
      const foundLines = new Set();
      for (const key of sampleKeys) {
        const keyMatch = key.match(/^\('([^']+)',\s*'([^']+)',\s*'([^']+)'\)$/);
        if (keyMatch) {
          foundRailways.add(keyMatch[1]);
          foundLines.add(keyMatch[2]);
        }
      }
      console.log('データ内の鉄道名:', Array.from(foundRailways));
      console.log('データ内の路線名（サンプル）:', Array.from(foundLines).slice(0, 10));
    }
  } else {
    console.log(`データ抽出成功: ${stations.length}件の駅データを取得（時間データ: ${times.filter(t => t !== null).length}件）`);
  }

  return {
    stations: stations,
    rents: rents,
    times: times,
    transfers: transfers
  };
}

// 乗換回数に応じた色を取得（3回まで、高コントラスト）
function getTransferColor(transfer) {
  if (transfer === null || transfer === undefined || isNaN(transfer)) {
    return 'rgba(128, 128, 128, 0.8)'; // グレー（データなし）
  }
  
  const transferValue = Math.floor(transfer);
  
  // 乗換回数に応じた色のマッピング（高コントラスト）
  const colorMap = {
    0: 'rgba(0, 123, 255, 0.8)',    // 鮮やかな青（0回）
    1: 'rgba(40, 167, 69, 0.8)',    // 鮮やかな緑（1回）
    2: 'rgba(255, 193, 7, 0.8)',    // 鮮やかな黄色（2回）
    3: 'rgba(220, 53, 69, 0.8)',    // 鮮やかな赤（3回以上）
  };
  
  // 3回以上は同じ色（赤）
  return colorMap[Math.min(transferValue, 3)] || colorMap[3];
}

// 乗換回数に応じたボーダー色を取得（3回まで、高コントラスト）
function getTransferBorderColor(transfer) {
  if (transfer === null || transfer === undefined || isNaN(transfer)) {
    return 'rgba(128, 128, 128, 1)';
  }
  
  const transferValue = Math.floor(transfer);
  
  const borderColorMap = {
    0: 'rgba(0, 123, 255, 1)',      // 鮮やかな青（0回）
    1: 'rgba(40, 167, 69, 1)',      // 鮮やかな緑（1回）
    2: 'rgba(255, 193, 7, 1)',      // 鮮やかな黄色（2回）
    3: 'rgba(220, 53, 69, 1)',      // 鮮やかな赤（3回以上）
  };
  
  return borderColorMap[Math.min(transferValue, 3)] || borderColorMap[3];
}

// 初期状態で空のチャートを作成
function initMainChart(ctx) {
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          type: 'bar',
          label: '家賃相場（万円）',
          data: [],
          backgroundColor: 'rgba(95, 179, 211, 0.6)',
          borderColor: 'rgba(95, 179, 211, 1)',
          borderWidth: 1,
          yAxisID: 'y'
        },
        {
          type: 'line',
          label: '神谷町までの時間（分）',
          data: [],
          borderColor: '#ff9f40',
          backgroundColor: 'rgba(255, 159, 64, 0.1)',
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#ff9f40',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        tooltip: {
          enabled: true,
          callbacks: {
            label: function(context) {
              const label = context.dataset.label || '';
              const value = context.parsed.y;
              // ラベルに「時間」や「分」が含まれている場合は「分」、それ以外は「万円」
              if (label.includes('時間') || label.includes('分')) {
                return `${label}: ${value.toFixed(1)}分`;
              } else {
                return `${label}: ${value.toFixed(1)}万円`;
              }
            }
          }
        },
        legend: {
          position: 'top',
          labels: {
            color: '#e0e4eb'
          }
        }
      },
      scales: {
        x: {
          ticks: {
            color: '#e0e4eb',
            maxRotation: 45,
            minRotation: 45
          },
          grid: {
            color: '#3a3d4e'
          }
        },
        y: {
          type: 'linear',
          position: 'left',
          ticks: {
            color: '#e0e4eb',
            callback: function(value) {
              return value + '万円';
            }
          },
          grid: {
            color: '#3a3d4e'
          },
          title: {
            display: true,
            text: '家賃相場（万円）',
            color: '#e0e4eb'
          }
        },
        y1: {
          type: 'linear',
          position: 'right',
          ticks: {
            color: '#ff9f40',
            callback: function(value) {
              return value + '分';
            }
          },
          grid: {
            drawOnChartArea: false,
            color: '#3a3d4e'
          },
          title: {
            display: true,
            text: '神谷町までの時間（分）',
            color: '#ff9f40'
          }
        }
      }
    }
  });
}

// チャートを作成
function createChart(ctx, stations, rents, times, transfers, label = '家賃相場（万円）') {
  const datasets = [];

  // 乗換回数に応じた色の配列を生成
  const backgroundColors = transfers && transfers.length > 0
    ? transfers.map(t => getTransferColor(t))
    : rents.map(() => 'rgba(95, 179, 211, 0.6)');
  
  const borderColors = transfers && transfers.length > 0
    ? transfers.map(t => getTransferBorderColor(t))
    : rents.map(() => 'rgba(95, 179, 211, 1)');

  // 家賃を棒グラフとして追加
  datasets.push({
    type: 'bar',
    label: label,
    data: rents,
    backgroundColor: backgroundColors,
    borderColor: borderColors,
    borderWidth: 1,
    yAxisID: 'y'
  });

  // 時間データがある場合、線グラフとして追加
  if (times && times.length > 0 && times.some(t => t !== null)) {
    datasets.push({
      type: 'line',
      label: '神谷町までの時間（分）',
      data: times,
      borderColor: '#ff9f40',
      backgroundColor: 'rgba(255, 159, 64, 0.1)',
      tension: 0.4,
      pointRadius: 4,
      pointHoverRadius: 6,
      pointBackgroundColor: '#ff9f40',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      yAxisID: 'y1'
    });
  }

  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: stations,
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        tooltip: {
          enabled: true,
          callbacks: {
            label: function(context) {
              const label = context.dataset.label || '';
              const value = context.parsed.y;
              // ラベルに「時間」や「分」が含まれている場合は「分」、それ以外は「万円」
              if (label.includes('時間') || label.includes('分')) {
                return `${label}: ${value.toFixed(1)}分`;
              } else {
                return `${label}: ${value.toFixed(1)}万円`;
              }
            }
          }
        },
        legend: {
          position: 'top',
          labels: {
            color: '#e0e4eb'
          }
        }
      },
      scales: {
        x: {
          ticks: {
            color: '#e0e4eb',
            maxRotation: 45,
            minRotation: 45
          },
          grid: {
            color: '#3a3d4e'
          }
        },
        y: {
          type: 'linear',
          position: 'left',
          ticks: {
            color: '#e0e4eb',
            callback: function(value) {
              return value + '万円';
            }
          },
          grid: {
            color: '#3a3d4e'
          },
          title: {
            display: true,
            text: '家賃相場（万円）',
            color: '#e0e4eb'
          }
        },
        y1: {
          type: 'linear',
          position: 'right',
          ticks: {
            color: '#ff9f40',
            callback: function(value) {
              return value + '分';
            }
          },
          grid: {
            drawOnChartArea: false,
            color: '#3a3d4e'
          },
          title: {
            display: true,
            text: '神谷町までの時間（分）',
            color: '#ff9f40'
          }
        }
      }
    }
  });
}

// 通勤時間の分給換算値の表を表示
function displayCommuteSalaryTable(stations, times, transfers, minuteSalary) {
  const tableContainer = document.getElementById('commute-salary-table-container');
  
  if (!tableContainer) {
    console.error('commute-salary-table-containerが見つかりません');
    return;
  }

  // データがない場合は非表示
  if (!stations || stations.length === 0 || !minuteSalary) {
    tableContainer.classList.remove('active');
    tableContainer.innerHTML = '';
    return;
  }

  // 表を表示
  tableContainer.classList.add('active');

  // カラム名を固定表示するヘッダーを追加
  let html = '<div class="commute-salary-table-header">';
  html += '<div class="commute-salary-table-header-cell">駅名</div>';
  html += '<div class="commute-salary-table-header-cell">分給換算値（円）</div>';
  html += '</div>';

  // 分給換算値を計算
  const salaryValues = stations.map((station, index) => {
    const time = times && times[index] !== null && times[index] !== undefined ? times[index] : 0;
    const transfer = transfers && transfers[index] !== null && transfers[index] !== undefined ? transfers[index] : 0;
    // 時間 + (乗換回数 × 7)
    const adjustedTime = time + (transfer * 7);
    // 分給 × 調整後の時間
    return Math.round(minuteSalary * adjustedTime);
  });

  // 表のHTMLを生成
  html += '<table class="commute-salary-table">';
  html += '<tbody>';
  
  stations.forEach((station, index) => {
    html += '<tr>';
    html += `<td>${station}</td>`;
    html += `<td>${salaryValues[index].toLocaleString()}</td>`;
    html += '</tr>';
  });
  
  html += '</tbody>';
  html += '</table>';

  tableContainer.innerHTML = html;
}
