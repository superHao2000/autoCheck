# AutoCheck

轻量的多服务签到工具。目前内置 YuChen、GlaDos、AirPort 与 JavBus；每个服务独立运行，单个账号或服务失败不会阻断其余任务。

## 支持的网站

| 网站/服务 | 网站用途                                       | 本项目执行的操作               | 认证方式                 |
| --------- | ---------------------------------------------- | ------------------------------ | ------------------------ |
| YuChen    | 提供账号登录的 iOS 资源服务站点。              | 向配置的签到接口提交账号密码。 | 账号、密码与站点签到 URL |
| GlaDos    | 提供网络服务与用户账户管理的平台。             | 调用官方用户签到接口。         | 登录 Cookie              |
| AirPort   | 泛指机场订阅服务面板；具体站点由用户自行填写。 | 登录面板后请求用户签到接口。   | 站点地址、邮箱、密码     |
| JavBus    | 影片资料检索网站。                             | 向站点签到地址发送已登录会话。 | 站点地址与登录 Cookie    |

> 不同 AirPort 站点的接口实现可能不同；本项目当前适配 `/auth/login` 和 `/user/checkin` 路径。请仅对你有权使用的账户和站点执行签到。

## 快速开始

要求：Python 3.9+。

```powershell
cd E:\Code\Github\autoCheck
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

程序会自动发现 `checkin/` 下的服务模块：已配置账号的服务会执行，未配置的服务会跳过。

## 配置

运行期配置统一使用 JSON。真实配置已被 Git 忽略，仓库只保留可安全提交的 `*.example.json` 模板。

```text
config/
├── push.example.json
└── services/
    ├── yuchen.example.json
    ├── glados.example.json
    ├── airport.example.json
    └── javbus.example.json
```

先复制需要的模板，再填写本地账号。例如 YuChen：

```powershell
Copy-Item config/services/yuchen.example.json config/services/yuchen.json
```

```json
{
  "accounts": [
    {
      "url": "https://your-yuchen-site.example/api/checkin",
      "username": "your_username",
      "password": "your_password"
    }
  ]
}
```

其他服务的账号字段如下：

| 服务    | 本地文件         | 必填字段                              |
| ------- | ---------------- | ------------------------------------- |
| YuChen  | `yuchen.json`  | `url`、`username`、`password`   |
| GlaDos  | `glados.json`  | `cookies`                           |
| AirPort | `airport.json` | `base_url`、`email`、`password` |
| JavBus  | `javbus.json`  | `url`、`cookies`                  |

每个文件均支持多账号：将多个对象加入 `accounts` 数组即可。

> 配置仅接受上表列出的标准字段名；`user`、`pass`、`cookie`、`site_url` 等旧字段不会自动转换，缺少标准字段的账号会被该服务跳过。

### 配置来源优先级

每个服务独立按以下顺序查找账号：

1. 单服务环境变量，例如 `YUCHEN_ACCOUNTS`；
2. 聚合环境变量 `AUTOCHECK_ACCOUNTS`；
3. 本地 `config/services/<服务>.json`；
4. 都没有时跳过该服务。

单服务环境变量的值是 JSON 数组：

```json
[
  {"url": "https://your-site.example/checkin", "username": "user", "password": "secret"}
]
```

聚合变量适合 GitHub Actions 新增服务，无须修改工作流：

```json
{
  "yuchen": [
    {"url": "https://your-site.example/checkin", "username": "user", "password": "secret"}
  ],
  "example": [
    {"token": "secret"}
  ]
}
```

### 推送配置（可选）

复制 `config/push.example.json` 为 `config/push.json` 后可配置通知。支持 Bark、Telegram、钉钉、PushPlus、企业微信与飞书。未配置任何渠道时不会发送通知。

```powershell
Copy-Item config/push.example.json config/push.json
```

也可在调度器中使用 `PUSH_CONFIG` 环境变量传入同样的 JSON 对象。

## 运行与测试

运行全部已配置服务：

```powershell
.\.venv\Scripts\python.exe main.py
```

每个服务都有独立的离线 Mock 测试，不会访问网站：

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_yuchen -v
.\.venv\Scripts\python.exe -m unittest tests.test_glados -v
.\.venv\Scripts\python.exe -m unittest tests.test_airport -v
.\.venv\Scripts\python.exe -m unittest tests.test_javbus -v
```

填写本地 JSON 后，显式开启某一个服务的真实测试：

```powershell
$env:RUN_LIVE_CHECKIN_TESTS = 'true'
.\.venv\Scripts\python.exe -m unittest tests.test_yuchen -v
```

真实测试只运行指定服务，不会触发汇总推送。

## GitHub Actions 与青龙

GitHub Actions 工作流每天 UTC 00:00 执行，也支持手动触发。请在仓库的 **Settings → Secrets and variables → Actions** 中配置账号，不要提交真实 JSON 文件。

| Secret                 | 用途                   |
| ---------------------- | ---------------------- |
| `YUCHEN_ACCOUNTS`    | YuChen 账号数组        |
| `GLADOS_ACCOUNTS`    | GlaDos 账号数组        |
| `AIRPORT_ACCOUNTS`   | AirPort 账号数组       |
| `JAVBUS_ACCOUNTS`    | JavBus 账号数组        |
| `AUTOCHECK_ACCOUNTS` | 任意服务的聚合账号对象 |
| `PUSH_CONFIG`        | 推送配置对象           |
| `USER_AGENT`         | 全局 User-Agent        |

青龙同样可使用这些环境变量；未设置变量时程序会回退到本地 JSON 配置。

## 模块顶部还需导入：

```python
from utils.service_runner import run_accounts
```

`run_accounts()` 会按 `ACCOUNT_FIELDS` 校验标准必填字段，单账号异常不会阻断后续账号。站点专属的 URL、请求、登录和响应判断应继续只放在 `checkin()` 中。

## 安全说明

- 不要提交 `config/services/*.json` 或 `config/push.json`；它们已在 `.gitignore` 中忽略。
- 仅提交 `*.example.json` 模板。
- 日志会显示 YuChen 用户名和 AirPort 邮箱，但不会输出密码或 Cookie。
- 不要将密码嵌入 URL，以免请求异常信息包含凭据。

## License

MIT
