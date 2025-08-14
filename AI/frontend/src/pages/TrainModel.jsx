import React, { useState, useEffect } from 'react';
import { 
  getTrainStatus, 
  startTrain, 
  stopTrain, 
  getTrainResult,
  getTrainConfig,
  updateTrainConfig,
  getTrainLogs
} from '../services/api';

const TrainModel = () => {
  const [trainStatus, setTrainStatus] = useState('idle');
  const [trainConfig, setTrainConfig] = useState({});
  const [trainResult, setTrainResult] = useState(null);
  const [trainLogs, setTrainLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [logInterval, setLogInterval] = useState(null);

  // 获取训练状态
  useEffect(() => {
    fetchTrainStatus();
    fetchTrainConfig();
    
    // 组件卸载时清理定时器
    return () => {
      if (logInterval) {
        clearInterval(logInterval);
      }
    };
  }, []);

  const fetchTrainStatus = async () => {
    try {
      const status = await getTrainStatus();
      setTrainStatus(status.status);
      
      // 如果正在训练，则开始获取日志
      if (status.status === 'training') {
        startLogPolling();
      }
    } catch (error) {
      console.error('获取训练状态失败:', error);
    }
  };

  const fetchTrainConfig = async () => {
    try {
      const config = await getTrainConfig();
      setTrainConfig(config);
    } catch (error) {
      console.error('获取训练配置失败:', error);
    }
  };

  const fetchTrainLogs = async () => {
    try {
      const logs = await getTrainLogs();
      setTrainLogs(logs);
    } catch (error) {
      console.error('获取训练日志失败:', error);
    }
  };

  const startLogPolling = () => {
    if (!logInterval) {
      const interval = setInterval(fetchTrainLogs, 3000);
      setLogInterval(interval);
    }
  };

  const stopLogPolling = () => {
    if (logInterval) {
      clearInterval(logInterval);
      setLogInterval(null);
    }
  };

  const handleStartTrain = async () => {
    setLoading(true);
    try {
      await startTrain(trainConfig);
      setTrainStatus('training');
      startLogPolling();
    } catch (error) {
      console.error('启动训练失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStopTrain = async () => {
    setLoading(true);
    try {
      await stopTrain();
      setTrainStatus('stopped');
      stopLogPolling();
    } catch (error) {
      console.error('停止训练失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfigChange = (key, value) => {
    setTrainConfig({
      ...trainConfig,
      [key]: value
    });
  };

  const handleSaveConfig = async () => {
    setLoading(true);
    try {
      await updateTrainConfig(trainConfig);
      alert('配置保存成功');
    } catch (error) {
      console.error('保存配置失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGetResult = async () => {
    setLoading(true);
    try {
      const result = await getTrainResult();
      setTrainResult(result);
    } catch (error) {
      console.error('获取训练结果失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="train-model">
      <h2>模型训练</h2>
      
      {/* 训练状态 */}
      <div className="status-section">
        <h3>训练状态</h3>
        <p>当前状态: {trainStatus}</p>
        <div className="status-actions">
          <button 
            onClick={handleStartTrain} 
            disabled={loading || trainStatus === 'training'}
          >
            {loading && trainStatus !== 'training' ? '启动中...' : '开始训练'}
          </button>
          <button 
            onClick={handleStopTrain} 
            disabled={loading || trainStatus !== 'training'}
          >
            {loading && trainStatus === 'training' ? '停止中...' : '停止训练'}
          </button>
          <button 
            onClick={fetchTrainStatus}
            disabled={loading}
          >
            刷新状态
          </button>
        </div>
      </div>

      {/* 训练配置 */}
      <div className="config-section">
        <h3>训练配置</h3>
        <div className="config-form">
          <div className="form-group">
            <label>学习率:</label>
            <input 
              type="number" 
              value={trainConfig.learning_rate || ''} 
              onChange={(e) => handleConfigChange('learning_rate', parseFloat(e.target.value))}
              step="0.001"
            />
          </div>
          <div className="form-group">
            <label>批次大小:</label>
            <input 
              type="number" 
              value={trainConfig.batch_size || ''} 
              onChange={(e) => handleConfigChange('batch_size', parseInt(e.target.value))}
            />
          </div>
          <div className="form-group">
            <label>训练轮数:</label>
            <input 
              type="number" 
              value={trainConfig.epochs || ''} 
              onChange={(e) => handleConfigChange('epochs', parseInt(e.target.value))}
            />
          </div>
          <div className="form-group">
            <label>优化器:</label>
            <select 
              value={trainConfig.optimizer || ''} 
              onChange={(e) => handleConfigChange('optimizer', e.target.value)}
            >
              <option value="adam">Adam</option>
              <option value="sgd">SGD</option>
              <option value="rmsprop">RMSprop</option>
            </select>
          </div>
          <button onClick={handleSaveConfig} disabled={loading}>
            保存配置
          </button>
        </div>
      </div>

      {/* 训练结果 */}
      <div className="result-section">
        <h3>训练结果</h3>
        <button onClick={handleGetResult} disabled={loading}>
          获取训练结果
        </button>
        {trainResult && (
          <div className="result-content">
            <p>准确率: {trainResult.accuracy}</p>
            <p>损失值: {trainResult.loss}</p>
            <p>训练时间: {trainResult.training_time} 秒</p>
          </div>
        )}
      </div>

      {/* 训练日志 */}
      <div className="logs-section">
        <h3>训练日志</h3>
        <button onClick={fetchTrainLogs} disabled={loading}>
          刷新日志
        </button>
        <div className="logs-content">
          {trainLogs.map((log, index) => (
            <div key={index} className="log-entry">
              [{log.timestamp}] {log.message}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TrainModel;