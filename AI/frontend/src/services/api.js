// 模拟API调用，实际项目中应替换为真实的API端点

// 获取训练状态
export const getTrainStatus = async () => {
  // 模拟API调用
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        status: 'idle' // idle, training, completed, stopped, error
      });
    }, 500);
  });
};

// 启动训练
export const startTrain = async (config) => {
  // 模拟API调用
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // 模拟50%成功率
      if (Math.random() > 0.5) {
        resolve({ success: true });
      } else {
        reject(new Error('启动训练失败'));
      }
    }, 1000);
  });
};

// 停止训练
export const stopTrain = async () => {
  // 模拟API调用
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true });
    }, 500);
  });
};

// 获取训练结果
export const getTrainResult = async () => {
  // 模拟API调用
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        accuracy: 0.95,
        loss: 0.05,
        training_time: 120
      });
    }, 500);
  });
};

// 获取训练配置
export const getTrainConfig = async () => {
  // 模拟API调用
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        learning_rate: 0.001,
        batch_size: 32,
        epochs: 10,
        optimizer: 'adam'
      });
    }, 300);
  });
};

// 更新训练配置
export const updateTrainConfig = async (config) => {
  // 模拟API调用
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // 模拟80%成功率
      if (Math.random() > 0.2) {
        resolve({ success: true });
      } else {
        reject(new Error('更新配置失败'));
      }
    }, 500);
  });
};

// 获取训练日志
export const getTrainLogs = async () => {
  // 模拟API调用
  return new Promise((resolve) => {
    setTimeout(() => {
      const logs = [];
      for (let i = 0; i < 10; i++) {
        logs.push({
          timestamp: new Date(Date.now() - (10-i) * 1000).toLocaleTimeString(),
          message: `训练日志信息 ${i+1}`
        });
      }
      resolve(logs);
    }, 300);
  });
};