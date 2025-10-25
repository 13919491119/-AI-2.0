import React, { useState } from 'react';
import { Card, Form, Input, DatePicker, TimePicker, Select, Button, message } from 'antd';
import axios from 'axios';
import moment from 'moment';

const { Option } = Select;

export default function SsqPredict() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const onFinish = async (values) => {
    setLoading(true);
    try {
      // 构造API参数
      const params = {
        date: values.date.format('YYYY-MM-DD'),
        time: values.time.format('HH:mm'),
        period: values.period,
        calendar: values.calendar,
        predict_time: values.predict_time.format('YYYY-MM-DD HH:mm'),
        mode: values.mode,
      };
      // 假设API为 /api/ssq_predict
      const res = await axios.post('/api/ssq_predict', params);
      setResult(res.data);
    } catch (e) {
      message.error('预测失败，请检查输入或稍后重试');
    }
    setLoading(false);
  };

  const now = moment();
  const defaultPeriod = `${now.year()}001`;
  return (
    <Card title="双色球预测" bordered={false} style={{ maxWidth: 600, margin: '0 auto' }}>
      <Form
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          date: now,
          time: now,
          period: defaultPeriod,
          calendar: '阳历',
          predict_time: now,
          mode: 'AI融合预测',
        }}
      >
        <Form.Item label="开奖日期" name="date" rules={[{ required: true }]}> <DatePicker /> </Form.Item>
        <Form.Item label="开奖时间" name="time" rules={[{ required: true }]}> <TimePicker format="HH:mm" /> </Form.Item>
        <Form.Item label="期次" name="period" rules={[{ required: true }]}> <Input placeholder="如2025201" /> </Form.Item>
        <Form.Item label="历法" name="calendar" initialValue="阳历"> <Select><Option value="阳历">阳历</Option><Option value="阴历">阴历</Option></Select> </Form.Item>
        <Form.Item label="预测时刻" name="predict_time" rules={[{ required: true }]}> <DatePicker showTime format="YYYY-MM-DD HH:mm" /> </Form.Item>
        <Form.Item label="预测模式" name="mode" initialValue="AI融合预测"> <Select>
          <Option value="小六爻">小六爻</Option>
          <Option value="小六壬">小六壬</Option>
          <Option value="奇门遁甲">奇门遁甲</Option>
          <Option value="紫薇奇数">紫薇奇数</Option>
          <Option value="AI融合预测">AI融合预测</Option>
        </Select> </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>预测</Button>
        </Form.Item>
      </Form>
      {result && (
        <Card type="inner" title="预测结果" style={{ marginTop: 16 }}>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </Card>
      )}
    </Card>
  );
}
