# AutoCheck

多服务签到自动化工具，支持 YuChen、GlaDos、AirPort、JavBus 等服务的自动签到。

## 功能特性

- ✅ **配置与代码解耦** - 配置文件可使用任意字段名，代码自动映射
- ✅ **多账号支持** - 每个服务支持多个账号，一个失败不影响其他
- ✅ **双环境运行** - 支持在 Qinglong 面板或 GitHub Actions 中运行
- ✅ **错误隔离** - 单个账号失败不会影响其他账号和任务
- ✅ **详细日志** - 清晰的日志输出和失败详情
- ✅ **多种推送** - 支持 Gotify、Telegram、Webhook、邮件通知

## 环境要求

- Python 3.7+
- 依赖: `requests`, `pyyaml`

## 安装

```bash
pip install requests pyyaml
```

## 配置说明

### 配置文件结构

在 `config/` 目录下创建各服务的配置文件：

```
config/
├── yuchen.yaml      # 御厨签到配置
├── glados.yaml      # GlaDos 签到配置
├── airport.yaml     # AirPort 签到配置
├── javbus.yaml      # JavBus 签到配置
└── config.yaml      # 全局配置 (可选)
```

### 各服务配置示例

#### YuChen (御厨)

```yaml
accounts:
  - url: "https://your-yuchen-site.com/api/checkin"
    username: "your_username"
    password: "your_password"
  - url: "https://another-site.com/api/checkin"
    username: "user2"
    password: "pass2"
```

#### GlaDos

```yaml
accounts:
  - cookies: "glados.one 的登录 Cookie"
```

#### AirPort

```yaml
accounts:
  - base_url: "https://your-airport-site.com"
    email: "your_email@example.com"
    password: "your_password"
```

#### JavBus

```yaml
accounts:
  - url: "https://javbus.com"
    cookies: "登录 Cookie"
```

### 全局配置 (config.yaml)

```yaml
# 推送配置
push:
  type: "telegram"  # gotify/telegram/webhook/mail
  api_url: "https://api.telegram.org/bot<token>/sendMessage"
  chat_id: "your_chat_id"

# 自定义 User-Agent
user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

### 字段名灵活性

配置文件支持使用多种字段名，代码会自动映射：

| 标准字段 | 可用别名 |
|---------|---------|
| url | base_url, domain, site_url |
| username | user, account, email |
| password | pass, pwd |
| cookies | cookie |
| user_agent | user-agent, ua |

例如，以下配置都是等价的：

```yaml
# 方式1: 使用标准字段
accounts:
  - url: "https://example.com"
    username: "user"
    password: "pass"

# 方式2: 使用别名
accounts:
  - base_url: "https://example.com"
    account: "user"
    pass: "pass"

# 方式3: 混用
accounts:
  - site_url: "https://example.com"
    user: "user"
    pwd: "pass"
```

## 使用方法

### 本地运行

```bash
python3 main.py
```

### Qinglong 面板运行

1. 将项目文件上传到 Qinglong
2. 在 Qinglong 中添加环境变量或配置文件
3. 创建定时任务运行 `python3 main.py`

### GitHub Actions 运行

1. Fork 本项目
2. 在仓库 Settings → Secrets 中添加以下 secrets：

| Secret 名称 | 说明 | 格式 |
|------------|------|------|
| YUCHEN_ACCOUNTS | 御厨账号 | JSON 数组 |
| GLADOS_ACCOUNTS | GlaDos 账号 | JSON 数组 |
| AIRPORT_ACCOUNTS | AirPort 账号 | JSON 数组 |
| JAVBUS_ACCOUNTS | JavBus 账号 | JSON 数组 |
| PUSH_CONFIG | 推送配置 | JSON 对象 |
| USER_AGENT | User-Agent | 字符串 |

#### GitHub Secrets JSON 格式示例

```json
// YUCHEN_ACCOUNTS
[
  {
    "url": "https://your-site.com/api/checkin",
    "username": "your_username",
    "password": "your_password"
  }
]

// GLADOS_ACCOUNTS
[
  {
    "cookies": "glados登录cookie"
  }
]

// PUSH_CONFIG
{
  "type": "telegram",
  "api_url": "https://api.telegram.org/bot<TOKEN>/sendMessage",
  "chat_id": "<CHAT_ID>"
}
```

3. 启用 GitHub Actions 工作流 (默认每天 UTC 0:00 执行)
4. 可手动触发: 进入 Actions → Auto Checkin → Run workflow

## 输出示例

```
2024-01-01 00:00:00 - autocheck - INFO - ========== AutoCheck 开始 ==========
2024-01-01 00:00:00 - autocheck - INFO - ========== YuChen 开始签到 (共 2 个账号) ==========
2024-01-01 00:00:01 - autocheck - INFO - YuChen 开始签到: user1
2024-01-01 00:00:02 - autocheck - INFO - YuChen 签到成功: user1
2024-01-01 00:00:02 - autocheck - INFO - YuChen 开始签到: user2
2024-01-01 00:00:03 - autocheck - WARNING - YuChen 签到失败: user2 - 密码错误
2024-01-01 00:00:03 - autocheck - INFO - ========== YuChen 签到完成: 成功 1/2 ==========
...
2024-01-01 00:00:10 - autocheck - INFO - ========== 签到汇总 ==========
2024-01-01 00:00:10 - autocheck - INFO -   YuChen: 成功 1/2
2024-01-01 00:00:10 - autocheck - INFO -   GlaDos: 成功 2/2
2024-01-01 00:00:10 - autocheck - INFO -   AirPort: 成功 1/1
2024-01-01 00:00:10 - autocheck - INFO -   JavBus: 成功 0/1
2024-01-01 00:00:10 - autocheck - INFO - 总计: 成功 4, 失败 2
2024-01-01 00:00:10 - autocheck - INFO - ========== 全部完成 ==========
```

## 目录结构

```
autoCheck/
├── main.py              # 主程序入口
├── README.md            # 说明文档
├── TASKS.md             # 任务计划
├── requirements.txt     # Python 依赖
├── config/              # 配置文件目录
│   ├── yuchen.yaml
│   ├── glados.yaml
│   ├── airport.yaml
│   └── javbus.yaml
├── checkin/             # 签到模块
│   ├── __init__.py
│   ├── yuchen.py
│   ├── glados.py
│   ├── airport.py
│   └── javbus.py
└── utils/               # 工具模块
    ├── __init__.py
    ├── config.py
    ├── logger.py
    ├── gotify.py
    ├── telegram.py
    ├── webhook.py
    └── mail.py
```

## 常见问题

### Q: 如何获取 GlaDOS/JavBus 的 Cookie？

A: 在浏览器中登录后，按 F12 打开开发者工具 → Network → 找到任意请求 → 复制 Request Headers 中的 Cookie。

### Q: GitHub Actions 运行失败怎么办？

A: 检查 Secrets 配置是否正确，特别是 JSON 格式是否有效。可以手动触发 workflow 查看详细日志。

### Q: 一个账号失败了会怎样？

A: 单个账号失败不会影响其他账号和其他服务。每个账号的签到结果是独立的。

## License

MIT