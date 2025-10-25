import React from 'react';
import { Layout, Menu, Tabs } from 'antd';
import {
  FundProjectionScreenOutlined,
  UserOutlined,
  PartitionOutlined,
  ApiOutlined,
} from '@ant-design/icons';
import SsqPredict from './components/SsqPredict';
import BaziChart from './components/BaziChart';
import Divination from './components/Divination';
import NameGenerator from './components/NameGenerator';
import Dashboard from './components/Dashboard';

const { Header, Content, Footer } = Layout;

export default function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529' }}>
        <div style={{ color: '#fff', fontSize: 22, fontWeight: 'bold' }}>
          玄机AI智能预测系统
        </div>
      </Header>
      <Content style={{ padding: 24 }}>
        <Tabs
          defaultActiveKey="1"
          items={[
            {
              key: '1',
              label: (
                <span><FundProjectionScreenOutlined /> 双色球预测</span>
              ),
              children: <SsqPredict />,
            },
            {
              key: '2',
              label: (
                <span><UserOutlined /> 八字排盘</span>
              ),
              children: <BaziChart />,
            },
            {
              key: '3',
              label: (
                <span><PartitionOutlined /> 占卜断事</span>
              ),
              children: <Divination />,
            },
            {
              key: '4',
              label: (
                <span><ApiOutlined /> 八字起名</span>
              ),
              children: <NameGenerator />,
            },
            {
              key: '5',
              label: (
                <span>仪表盘</span>
              ),
              children: <Dashboard />,
            },
          ]}
        />
      </Content>
      <Footer style={{ textAlign: 'center' }}>
        玄机AI系统 ©2025
      </Footer>
    </Layout>
  );
}
