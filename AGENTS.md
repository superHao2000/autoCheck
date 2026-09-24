# AutoCheck 智能体约定

## 项目结构

- `main.py` 自动发现并运行 `checkin/` 中的签到服务。
- 各站点的请求、认证、响应解析留在自己的服务模块；稳定共用逻辑放入 `utils/`。
- 服务配置使用 JSON；可提交模板放在 `config/services/*.example.json`，真实配置不得提交。
- `Test` 保留完整代码、测试和智能体资料；`master` 只保留生产文件。

## 分支流程

- 新功能、修复和重构从 `Test` 创建开发分支，验证后合回 `Test`。
- 发布时将已验证的生产改动同步到 `master`，排除 `tests/`、`.agents/`、根目录 `AGENTS.md` 及测试专用配置。
- `master` 上的排除操作不合回 `Test`；生产分支上的修复按需选择性同步。
- 操作前检查分支与工作区，保留用户已有改动。

## 服务与配置

- 服务模块声明 `SERVICE_NAME`、`CONFIG_FILENAME`、`ENV_KEY`、`ACCOUNT_FIELDS`，并提供 `checkin()` 和 `run()`。
- `run()` 复用 `utils.service_runner.run_accounts()`；单个账号或服务失败不得中断其他任务。
- 账号来源优先级为单服务环境变量、`AUTOCHECK_ACCOUNTS`、本地 JSON；仅接受标准字段名。
- 日志、异常和通知不得暴露密码、Cookie、Token 或未经清理的认证响应。
- 真实签到可能改变账号状态，仅在用户明确要求时执行。

## 修改与验证

- 先读相关实现和调用方。瘦身优先删除冗余，避免为未来需求添加抽象。
- 行为、配置或命令变化时，同步更新 README 中的相关说明。
- 离线测试只在 `Test` 及其开发分支运行，不得读取真实凭据或意外访问外网：

  ```powershell
  .\.venv\Scripts\python.exe -m unittest discover -s tests -t . -v
  ```

- 提交验证范围按当前任务要求执行；真实签到测试仅在用户明确要求时运行。

## 协作偏好

- 使用简体中文，表达简洁；先自行核实可查信息，只在确需用户决策时提问。
- 提交前展示文件、摘要和完整提交信息，待用户确认后提交；仅在用户明确要求时推送。
- 用户要求结构分析时优先使用 Filescope；其 Python 依赖识别需交叉核对，`.filescope/` 分析数据不纳入提交。
