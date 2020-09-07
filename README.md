# BJUTnCoVDailyReporter

nCoV Daily reporter for BJUT (Report temperature three times a day)

[下载地址](releases)

## 简介

**BJUTnCoVDailyReporter:** 基于 python 的每日三次体温上报脚本（北工大适用）

本脚本包含的功能：
- **体温上报**: 上报当前体温值 (默认选择 36℃-36.5℃)
- **智能识别时间**: 智能识别当前是否为上报时间
- **智能识别状态**: 智能识别当前时间段是否已完成上报


## 运行环境与依赖

- **python**: Python 2 / Python 3 兼容 (Python 2.7/3.6/3.7 测试通过)
- **requests**: 需要安装 `requests` 库


## 使用方法

### 使用配置文件运行（**推荐**）
```
python DailyReport.py -c 配置文件路径 [-v]
```

#### 参数说明

| 参数短名称 | 参数名 | 备注 | 示例 |
| --------- | ----- |  --- | ---- |
| -c | --config-file= | 配置文件路径 | `-c config.json` |
| -v | --verbose | 启用详细模式（调试模式） | `-v` |

#### 配置文件格式
```
{
    "username": "19010101",             # 用户名
    "password": "password",             # 密码
    "eai_sess": "",                     # (可选) 脚本缓存的登录 cookie (一般无需填写)
    "timeout": 5,                       # (可选) HTTP 请求超时时间
    "proxy": "http://127.0.0.1:8888"    # (可选) 代理服务器
}
```

> 首次运行脚本时，如果指定的配置文件不存在，将会尝试创建。

### 指定参数运行
```
python DailyReport.py -u 用户名 -p 密码 [-x 代理服务器] [-v]
```

#### 参数说明

| 参数短名称 | 参数名 | 备注 | 示例 |
| --------- | ----- |  --- | ---- |
| -u | --user= | 填报系统用户名 | `-u 19010101` |
| -p | --pass= | 填报系统密码 | `-p password` |
| -x | --proxy= | 代理服务器地址 | `-x http://127.0.0.1:8888` |
| -v | --verbose | 启用详细模式（调试模式） | `-v` |

> 如果同时指定了参数 `-c` (`--config-file=`)，则此处的配置项会覆盖配置文件中的相应配置项。


## 自动化上报

推荐使用 Linux 系统的 cron 计划任务功能，添加如下内容使脚本每 30 分钟尝试一次填报（需修改脚本和配置文件路径）
```
*/30 * * * * python /home/report.py -c /home/report.json
```
