import React, { useState } from 'react';
import { Card, Form, Input, DatePicker, TimePicker, Select, Button, message } from 'antd';
import axios from 'axios';

const { Option } = Select;

export default function NameGenerator() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const params = {
        gender: values.gender,
        calendar: values.calendar,
        year: values.date.year(),
        month: values.date.month() + 1,
        day: values.date.date(),
        hour: values.time.hour(),
        minute: values.time.minute(),
        surname: values.surname,
      };
      const res = await axios.post('/api/name_generate', params);
      setResult(res.data);
    } catch (e) {
      message.error('起名失败，请检查输入或稍后重试');
    }
    setLoading(false);
  };

  const now = new Date();
  return (
    <Card title="八字起名" bordered={false} style={{ maxWidth: 600, margin: '0 auto' }}>
      <Form
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          gender: '女',
          calendar: '阳历',
          date: now,
          time: now,
          surname: '',
        }}
      >
        <Form.Item label="性别" name="gender" initialValue="女"> <Select><Option value="女">女</Option><Option value="男">男</Option></Select> </Form.Item>
        <Form.Item label="历法" name="calendar" initialValue="阳历"> <Select><Option value="阳历">阳历</Option><Option value="阴历">阴历</Option></Select> </Form.Item>
        <Form.Item label="出生日期" name="date" rules={[{ required: true }]}> <DatePicker /> </Form.Item>
        <Form.Item label="出生时辰" name="time" rules={[{ required: true }]}> <TimePicker format="HH:mm" /> </Form.Item>
        <Form.Item label="姓氏" name="surname" rules={[{ required: true }]}> <Input placeholder="请输入姓氏" /> </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>起名</Button>
        </Form.Item>
      </Form>
      {result && (
        <Card type="inner" title="起名结果" style={{ marginTop: 16 }}>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </Card>
      )}
    </Card>
  );
}
