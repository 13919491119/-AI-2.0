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
