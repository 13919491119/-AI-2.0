# 配置公网访问指南 - Celestial Nexus AI 微信集成

本指南将详细说明如何为 Celestial Nexus AI 系统配置公网访问，以便与微信公众号进行集成，而无需使用 Ngrok。

## 方案概述

为了使微信公众号能够访问您的本地服务，您需要:
1. 有一个可以从互联网访问的服务器（公网IP或域名）
2. 将微信请求转发到您的本地服务器

以下是几种常见的配置方法，从最简单到最复杂：

## 方案1：使用云服务器直接部署

如果您有云服务器（阿里云、腾讯云、AWS等），最简单的方法是直接在该服务器上部署系统。

### 步骤:

1. **将代码部署到云服务器**
   ```bash
   git clone https://github.com/yourusername/celestial-nexus-ai.git
   cd celestial-nexus-ai
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置防火墙开放端口9090**
   - 阿里云/腾讯云：在安全组中添加入站规则，允许9090端口
   - AWS：在安全组中添加入站规则，允许9090端口
   - Linux：
     ```bash
     sudo ufw allow 9090/tcp
     ```

4. **启动本地模式服务**
   ```bash
   ./local_wechat_integration.sh
   ```

5. **配置微信公众号**
   - URL: `http://您的服务器IP:9090/wechat`
   - Token: `celestial_nexus_ai_token`

## 方案2：使用Frp内网穿透工具

Frp是一个开源的内网穿透工具，类似Ngrok但更灵活。

### 步骤:

1. **在公网服务器上安装Frp服务端**
   ```bash
   # 在公网服务器上
   wget https://github.com/fatedier/frp/releases/download/v0.45.0/frp_0.45.0_linux_amd64.tar.gz
   tar -zxvf frp_0.45.0_linux_amd64.tar.gz
   cd frp_0.45.0_linux_amd64
   ```

2. **配置Frp服务端**
   编辑 `frps.ini`:
   ```ini
   [common]
   bind_port = 7000
   token = your_token_here
   ```

3. **启动Frp服务端**
   ```bash
   ./frps -c frps.ini
   ```

4. **在本地安装Frp客户端**
   ```bash
   # 在本地开发机器上
   wget https://github.com/fatedier/frp/releases/download/v0.45.0/frp_0.45.0_linux_amd64.tar.gz
   tar -zxvf frp_0.45.0_linux_amd64.tar.gz
   cd frp_0.45.0_linux_amd64
   ```

5. **配置Frp客户端**
   编辑 `frpc.ini`:
   ```ini
   [common]
   server_addr = 您的公网服务器IP
   server_port = 7000
   token = your_token_here

   [wechat]
   type = http
   local_ip = 127.0.0.1
   local_port = 9090
   custom_domains = 您的域名或服务器IP
   ```

6. **启动本地Frp客户端**
   ```bash
   ./frpc -c frpc.ini
   ```

7. **启动本地微信集成服务**
   ```bash
   ./local_wechat_integration.sh
   ```

8. **配置微信公众号**
   - URL: `http://您的域名或IP:7000/wechat`
   - Token: `celestial_nexus_ai_token`

## 方案3：使用Nginx反向代理（推荐用于生产环境）

如果您拥有一个域名和公网服务器，使用Nginx反向代理是最专业的配置方式。

### 步骤:

1. **在公网服务器上安装Nginx**
   ```bash
   sudo apt update
   sudo apt install nginx
   ```

2. **配置Nginx反向代理**
   创建配置文件 `/etc/nginx/sites-available/celestial-nexus`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;  # 替换为您的域名

       location /wechat {
           proxy_pass http://您的本地服务器IP:9090/wechat;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **启用配置并重启Nginx**
   ```bash
   sudo ln -s /etc/nginx/sites-available/celestial-nexus /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

4. **配置SSL证书（强烈推荐）**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

5. **确保您的本地服务器和公网服务器网络连通**
   - 如果是内网环境，可能需要配置VPN或专线连接
   - 如果是同一网络内，确保防火墙允许相应端口

6. **启动本地微信集成服务**
   ```bash
   ./local_wechat_integration.sh
   ```

7. **配置微信公众号**
   - URL: `https://your-domain.com/wechat`
   - Token: `celestial_nexus_ai_token`

## 方案4：使用SSH隧道（临时测试使用）

如果您只是临时测试，可以使用SSH隧道进行端口转发。

### 步骤:

1. **在公网服务器上创建SSH隧道**
   ```bash
   # 在本地执行，将本地9090端口转发到公网服务器的9090端口
   ssh -R 9090:localhost:9090 user@your-server-ip
   ```

2. **在公网服务器上配置允许端口转发**
   编辑 `/etc/ssh/sshd_config`:
   ```
   GatewayPorts yes
   ```

3. **重启SSH服务**
   ```bash
   sudo systemctl restart sshd
   ```

4. **启动本地微信集成服务**
   ```bash
   ./local_wechat_integration.sh
   ```

5. **配置微信公众号**
   - URL: `http://您的公网服务器IP:9090/wechat`
   - Token: `celestial_nexus_ai_token`

## 故障排查

### 1. 无法连接到服务

检查以下几点：
- 确认端口是否开放（使用 `netstat -tulpn | grep 9090`）
- 确认防火墙规则是否正确
- 使用 `curl` 测试接口是否可访问：
  ```bash
  curl "http://localhost:9090/wechat?signature=test&timestamp=123&nonce=test&echostr=test"
  ```

### 2. 微信平台验证失败

- 确认URL格式是否正确（包含"/wechat"路径）
- 确认Token是否正确设置为 `celestial_nexus_ai_token`
- 检查服务器日志 `tail -f wechat_server.log`

### 3. 请求超时

微信平台验证请求有5秒超时限制：
- 检查网络延迟 `ping your-domain.com`
- 简化验证逻辑，减少处理时间
- 确保服务器有足够资源

## 安全建议

1. **使用HTTPS**
   - 微信官方强烈建议使用HTTPS
   - 使用免费的Let's Encrypt证书

2. **限制IP访问**
   - 配置防火墙仅允许微信服务器IP访问

3. **设置复杂Token**
   - 在生产环境中，修改默认Token为更复杂的值
   ```bash
   # 在wechat_server.py中修改
   TOKEN = '复杂的随机字符串'
   ```

## 更多资源

- [微信公众平台开发文档](https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Overview.html)
- [Frp官方文档](https://gofrp.org/docs/)
- [Nginx官方文档](https://nginx.org/en/docs/)