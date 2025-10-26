import React, { useState } from 'react';
import { Card, Form, Input, DatePicker, TimePicker, Select, Button, message } from 'antd';
import axios from 'axios';

const { Option } = Select;

export default function Divination() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const params = {
        event: values.event,
        calendar: values.calendar,
        date: values.date.format('YYYY-MM-DD'),
        time: values.time.format('HH:mm'),
        mode: values.mode,
      };
      const res = await axios.post('/api/divination', params);
      setResult(res.data);
    } catch (e) {
      message.error('占卜失败，请检查输入或稍后重试');
    }
    setLoading(false);
  };

  const now = new Date();
  return (
    <Card title="占卜断事" bordered={false} style={{ maxWidth: 600, margin: '0 auto' }}>
      <Form
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          event: '',
          calendar: '阳历',
          date: now,
          time: now,
          mode: 'AI融合',
        }}
      >
        <Form.Item label="所断何事" name="event" rules={[{ required: true }]}> <Input /> </Form.Item>
        <Form.Item label="起盘历法" name="calendar" initialValue="阳历"> <Select><Option value="阳历">阳历</Option><Option value="阴历">阴历</Option></Select> </Form.Item>
        <Form.Item label="起盘日期" name="date" rules={[{ required: true }]}> <DatePicker /> </Form.Item>
        <Form.Item label="起盘时辰" name="time" rules={[{ required: true }]}> <TimePicker format="HH:mm" /> </Form.Item>
        <Form.Item label="占卜模式" name="mode" initialValue="AI融合"> <Select>
          <Option value="小六爻">小六爻</Option>
          <Option value="小六壬">小六壬</Option>
          <Option value="奇门遁甲">奇门遁甲</Option>
          <Option value="紫薇奇数">紫薇奇数</Option>
          <Option value="AI融合">AI融合</Option>
        </Select> </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>起盘断事</Button>
        </Form.Item>
      </Form>
      {result && (
        <Card type="inner" title="占卜结果" style={{ marginTop: 16 }}>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </Card>
      )}
    </Card>
  );
}
