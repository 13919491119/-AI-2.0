# 微信公众平台与 Celestial Nexus AI 系统集成配置指南

## 问题排查：Token验证失败

如果您在配置微信公众平台服务器时遇到"Token验证失败"的问题，请按照以下步骤操作：

### Ngrok认证错误（ERR_NGROK_105）

如果您看到类似以下错误：
```
ERR_NGROK_105
authentication failed: The authtoken you specified does not look like a proper ngrok authtoken.
```

这表明您的Ngrok令牌无效。请按照以下步骤解决：

1. 访问 https://dashboard.ngrok.com/get-started/your-authtoken 获取您的正确令牌
2. 使用正确的令牌重新运行集成选择器：
   ```bash
   ./wechat_integration_selector.sh
   ```
3. 选择选项1，并输入有效的Ngrok令牌

如果您没有Ngrok账户或不想使用Ngrok，可以选择本地模式（选项2），然后自行配置公网访问方式。

### 解决方案1：使用增强的验证逻辑

我们已经增强了微信验证逻辑，确保正确地按照微信官方规范计算签名。请按以下步骤操作：

1. 停止现有服务
   ```bash
   pkill -f "python wechat_server.py"
   ```

2. 使用配置助手脚本重新启动服务
   ```bash
   ./setup_wechat_integration.sh
   ```
   
3. 根据脚本输出的指南配置微信公众平台

### 解决方案2：手动配置

1. 确保您使用的Token是
   ```
   celestial_nexus_ai_token
   ```

2. 确保URL格式正确，应为
   ```
   https://[ngrok-subdomain].ngrok-free.dev/wechat
   ```
   
   您可以从日志中获取准确的URL：
   ```bash
   grep -o 'https://[^"]*' wechat_server.log | tail -1
   ```

3. 在微信公众平台配置时，确保：
   - URL包含"/wechat"路径
   - Token大小写正确
   - 选择"明文模式"作为消息加解密方式

### 解决方案3：重新启动Ngrok隧道

Ngrok免费版每次重启会生成新的URL，这可能导致之前的配置失效。

1. 确保您设置了正确的Ngrok令牌
   ```bash
   export NGROK_AUTH_TOKEN="您的令牌"
   ```

2. 重新启动微信集成服务
   ```bash
   ./start_wechat_integration.sh
   ```
   
3. 使用新生成的URL更新微信公众平台配置

## 验证配置成功

成功配置后，您可以在微信公众号中发送消息进行测试，系统应该会调用Celestial Nexus AI进行响应。

## 常见问题

1. **Q: 每次重启后都需要重新配置微信公众平台吗？**
   
   A: 是的，使用免费版Ngrok时，每次重启都会生成新的URL，需要更新配置。可以考虑升级到Ngrok付费版以获得固定URL。

2. **Q: 如何查看微信服务的运行状态？**
   
   A: 使用以下命令查看日志：
   ```bash
   tail -f wechat_server.log
   ```

3. **Q: 如何测试微信验证是否工作？**
   
   A: 运行测试脚本：
   ```bash
   python test_wechat_validation.py
   ```

## 生产环境建议

在生产环境中，建议：

1. 使用固定域名和HTTPS证书，而非Ngrok临时URL
2. 设置更复杂的自定义Token
3. 使用专用服务器部署微信服务
4. 考虑使用消息加密模式增强安全性