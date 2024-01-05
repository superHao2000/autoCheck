# new Env("YuChen_Check")
# cron 30 8 * * * main.py
import os.path

from utils.config import Config
from utils.logger import log
from utils.util import ObjDictTool
from utils.yuchen import Account

FILE_PATH = 'config.yaml'


def main():
    config = Config(FILE_PATH)
    if os.path.exists(FILE_PATH):
        config.read_config()
        accounts = config.Accounts
        log.info(f"检测到{len(accounts)}个账号")
        for i in range(len(accounts)):
            log.info(f"开始账号{i + 1}签到")
            account = Account(accounts[i])
            if account.user_agent == "" or account.username == "" or account.password == "":
                log.info("账号信息不完整，跳过此账号")
                continue
            ObjDictTool.to_obj(account, **accounts[i])
            is_a = account.yuchen_login()
            if is_a:
                account.yuchen_check()
                account.yuchen_info()
            else:
                continue
    else:
        log.info("配置文件不存在")
        config.write_config()
        log.info("请填写配置文件后重新启动")


if __name__ == '__main__':
    main()
