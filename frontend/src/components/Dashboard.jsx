import React from 'react';
import { Card, Statistic, Row, Col } from 'antd';

export default function Dashboard() {
  // 可扩展为API动态获取系统状态
  return (
    <Card title="系统仪表盘" bordered={false} style={{ maxWidth: 900, margin: '0 auto' }}>
      <Row gutter={16}>
        <Col span={8}><Statistic title="累计学习周期" value={1927} /></Col>
        <Col span={8}><Statistic title="知识增长量" value={1927} /></Col>
        <Col span={8}><Statistic title="系统优化进度" value={1931} /></Col>
      </Row>
      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={8}><Statistic title="预测准确率" value="91.5%" /></Col>
        <Col span={8}><Statistic title="系统健康评分" value={85} /></Col>
        <Col span={8}><Statistic title="系统稳定性" value="99.9%" /></Col>
      </Row>
    </Card>
  );
}

// 增加简单操作按钮
export function DashboardControls() {
  const triggerOptimize = async () => {
    try {
      const res = await fetch('/api/optimize_models', { method: 'POST' });
      alert('已触发模型优化任务（后台执行）');
    } catch (e) {
      alert('触发失败');
    }
  };
  const predictStock = async () => {
    const sym = prompt('输入股票代码，例如 000001');
    if (!sym) return;
    const res = await fetch('/api/predict_stock', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({symbol: sym}) });
    const j = await res.json();
    alert(JSON.stringify(j));
  };
  const predictWeather = async () => {
    const loc = prompt('输入地点，例如 Beijing');
    if (!loc) return;
    const res = await fetch('/api/predict_weather', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({location: loc}) });
    const j = await res.json();
    alert(JSON.stringify(j));
  };
  return (
    <div style={{ marginTop: 24 }}>
      <button onClick={triggerOptimize} style={{ marginRight: 8 }}>触发模型优化</button>
      <button onClick={predictStock} style={{ marginRight: 8 }}>股票预测(测试)</button>
      <button onClick={predictWeather}>天气预测(测试)</button>
    </div>
  );
}
