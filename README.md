# YuChen Check

一个签到攒积分换取ios的软件或者游戏的小脚本

[雨晨ios资源网站](https://yuchen.tonghuaios.com/)

新入手的ipad无奈没有游戏可玩，发现了这个网站可以签到攒积分换账号，写个签到脚本薅羊毛
写的很烂，仅能使用

### 使用说明

支持本地和青龙面版

### 青龙面板

1. 确保你已安装并配置好青龙面板
2. 在青龙面板的订阅管理中点击 新建订阅 ，将下方命令参数复制到新建订阅窗口的 名称 中后手动设置定时规则，指定类型为 interval
   每 1 天 后点击确定，然后运行订阅并禁用订阅的自动运行，如不禁用将导致配置文件被覆盖。

   ```angular2html
    ql repo https://github.com/superHao2000/yuchenCheck.git main utils|init utils|config master py|yaml
   ```

3. 在青龙面板的定时任务中运行名称为 YuChen_Check 的任务，查看日志检查确定成功后即可禁用然后进行下一步

4. 在青龙面板的脚本管理中点击 superHao2000_yuchenCheck_master 文件夹，选中config.yaml 文件，填写账号密码和浏览器UA

5. 在以来管理添加依赖
    ```
    PyYAML
   loguru
   requests
   beautifulsoup4
   ```
6. 在青龙面板的定时任务中运行名称为 YuChen_Check的任务，查看日志检查确定成功运行即可