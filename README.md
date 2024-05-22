# 自用签到脚本

## 支持网站

1. [雨晨ios资源网站](https://yuchen.tonghuaios.com/)
2. [Glados](https://glados.rocks/)
3. 飞机场
4. [javbus](https://www.javbus.com)

## 功能

- [x] 多账号
- [x] 推送
- [ ] docker

## 使用说明

### 青龙面板

1. 在青龙面板的订阅管理中点击 新建订阅 ，将下方命令参数复制到新建订阅窗口的 名称 中后手动设置定时规则，指定类型为 interval
   每 1 天 后点击确定，然后运行订阅

   ```angular2html
    ql repo https://github.com/superHao2000/autoCheck.git "main" "" "utils|config" "master" "py|yaml"
   ```

2. 在青龙面板的定时任务中运行名称为 auto_Check 的任务，查看日志检查确定生成了配置文件 config.yaml

3. 在青龙面板的脚本管理中找到 superHao2000_autoCheck_master 文件夹，填写config.yaml配置文件

4. 在依赖管理添加依赖
    ```
   PyYAML~=6.0.1
   loguru~=0.7.2
   requests~=2.31.0
   beautifulsoup4~=4.12.2
   urllib3~=2.1.0
   pydantic~=2.6.4
   lxml~=5.2.2
   ```
5. 重新运行 auto_Check 任务，查看日志检查确定成功运行，每天8.30自动运行
