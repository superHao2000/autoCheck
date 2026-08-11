# AutoCheck

轻量的多服务签到工具。目前内置 YuChen、GlaDos、AirPort 与 JavBus；每个服务独立运行，单个账号或服务失败不会阻断其余任务。

## 支持的网站

| 网站/服务 | 网站用途                                       | 本项目执行的操作               | 认证方式                 |
| --------- | ---------------------------------------------- | ------------------------------ | ------------------------ |
| YuChen    | 提供账号登录的 iOS 资源服务站点。              | 登录后调用每日签到接口。 | 账号、密码与站点首页 URL |
| GlaDos    | 提供网络服务与用户账户管理的平台。             | 调用官方用户签到接口。         | 登录 Cookie              |
| AirPort   | 泛指机场订阅服务面板；具体站点由用户自行填写。 | 登录面板后请求用户签到接口。   | 站点地址、邮箱、密码     |
| JavBus    | 影片资料检索网站。                             | 向站点签到地址发送已登录会话。 | 站点地址与登录 Cookie    |

> 不同 AirPort 站点的接口实现可能不同；本项目当前适配 `/auth/login` 和 `/user/checkin` 路径。请仅对你有权使用的账户和站点执行签到。

## 快速开始

要求：Python 3.9+。

```powershell
cd E:\Code\Github\autoCheck
py -m venv .venv
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
  "url": "https://your-yuchen-site.example/",
  "accounts": [
    {
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

YuChen 的多个账号共用同一站点时，可将 `url` 写在顶层；账号内单独填写的 `url` 会覆盖顶层值。

> 配置仅接受上表列出的标准字段名；`user`、`pass`、`cookie`、`site_url` 等旧字段不会自动转换，缺少标准字段的账号会被该服务跳过。

### 生产运行的配置来源优先级

每个服务会读取以下全部来源并按优先级合并账号：

1. 单服务环境变量，例如 `YUCHEN_ACCOUNTS`（最高优先级）；
2. 聚合环境变量 `AUTOCHECK_ACCOUNTS`；
3. 本地 `config/services/<服务>.json`（最低优先级）。

同一服务的账号会按上述顺序保留；重复账号只保留优先级更高的一项，日志会提示检测到重复账号，但不会输出账号或凭据。三个来源都没有有效账号时，服务才会被跳过。

> 此优先级仅适用于 `main.py`、GitHub Actions 和青龙的生产运行；下方的本地真实测试只读取本地 JSON，不读取环境变量。

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

### 离线测试

离线测试使用 Mock 验证请求和解析逻辑，不读取真实配置，也不会访问网站：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

### 本地真实签到

直接运行一个服务的测试文件时，只读取该服务对应的本地 JSON，不读取环境变量，也不会发送通知：

```powershell
.\.venv\Scripts\python.exe -m tests.test_yuchen
.\.venv\Scripts\python.exe -m tests.test_glados
.\.venv\Scripts\python.exe -m tests.test_airport
.\.venv\Scripts\python.exe -m tests.test_javbus
```

汇总测试只读取所有本地 JSON，不读取环境变量，也不发送通知：

```powershell
.\.venv\Scripts\python.exe main.py --local-only
```

文件不存在、账号为空或 JSON 格式错误时，程序会输出原因并跳过受影响的服务。

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

## 新增服务

无需修改 `main.py`：新增公开的 `checkin/example.py` 后，入口会自动发现它。服务模块必须声明元数据、标准字段，并仅在 `checkin()` 中实现本站请求和响应判断：

```python
from utils.service_runner import run_accounts

SERVICE_NAME = "Example"
CONFIG_FILENAME = "example.json"
ENV_KEY = "EXAMPLE_ACCOUNTS"
ACCOUNT_FIELDS = ("token",)


def checkin(token: str) -> dict:
    """执行本站请求并返回 success/message。"""
    return {"success": True, "message": "签到成功"}


def run(accounts: list) -> dict:
    """复用公共执行器完成账号校验、统计和失败隔离。"""
    return run_accounts(SERVICE_NAME, accounts, ACCOUNT_FIELDS, checkin)
```

再添加 `config/services/example.example.json` 模板，并为该服务补充独立离线测试。真实 `example.json` 会被现有 Git 忽略规则保护。`run_accounts()` 会校验标准必填字段，单账号异常不会阻断后续账号。

## 安全说明

- 不要提交 `config/services/*.json` 或 `config/push.json`；它们已在 `.gitignore` 中忽略。
- 仅提交 `*.example.json` 模板。
- 日志会显示 YuChen 用户名和 AirPort 邮箱，但不会输出密码或 Cookie。
- 不要将密码嵌入 URL，以免请求异常信息包含凭据。

## License

MIT
