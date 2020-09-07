#!/usr/bin/python
# -*- coding: utf-8 -*-

"""@package BJUTDaily

BJUT Daily Three times Report
"""

import os
import sys
import requests
import re
import json
import traceback
import logging
import getopt


class BJUTReporter(object):
    BASE_URL = 'https://itsapp.bjut.edu.cn'
    API_LOGIN = '/uc/wap/login/check'
    API_PAGE = '/site/ncov/bjutdailyup'
    API_INDEX = '/xisuncov/wap/open-report/index'
    API_GET_SETTING = '/xisuncov/wap/open-report/get-setting'
    API_REPORT = '/xisuncov/wap/open-report/save'

    def __init__(self, cfg_path=None, cfg_dic=None, is_verbose=False, proxies=None):
        self.config = {
            'username': '',
            'password': '',
            'eai_sess': '',
            'timeout': 5,
            'proxy': None
        }
        self.login_status = False
        self.cfg_path = cfg_path

        # Log record
        self.logger = logging.getLogger("nCoVReporter")
        fmt = '[%(asctime)s][%(levelname)s]: %(message)s (%(filename)s:%(lineno)d)'
        formatter = logging.Formatter(fmt)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.formatter = formatter
        self.logger.addHandler(console_handler)
        if is_verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

        # Load config
        if not cfg_path and not cfg_dic:
            self.logger.error('Neither cfg_path nor cfg_dic is specified')
            sys.exit(0)

        if cfg_path:
            self._load_cfg_file(cfg_path)
        else:
            self.config.update(cfg_dic)

        # Initialize session
        self.session = requests.session()
        self.session.trust_env = False

        # Get domain (use to set cookie)
        if sys.version_info.major < 3:
            import urlparse
            res = urlparse.urlparse(self.BASE_URL)
        else:
            from urllib.parse import urlparse
            res = urlparse(self.BASE_URL)
        if res.netloc.find(':') > -1:
            self.base_domain = res.netloc[0:res.netloc.find(':')]
        else:
            self.base_domain = res.netloc

        # Set User-Agent
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        ua += "Chrome/79.0.3945.130 Safari/537.36"
        self.session.headers["User-Agent"] = ua

        if proxies:
            self.session.proxies = proxies
        elif self.config['proxy']:
            self.set_proxy(self.config['proxy'])

        # Ignore https error
        self.session.verify = False
        if sys.version_info.major < 3:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        else:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def set_proxy(self, proxy_url):
        if proxy_url:
            self.session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            self.logger.debug("Proxy set to: %s" % proxy_url)

    def _load_cfg_file(self, _path):
        if not os.path.exists(_path):
            cfg_template = {"username": "", "password": ""}
            try:
                with open(_path, 'w') as fp:
                    json.dump(cfg_template, fp, indent=4)
                    fp.close()
                self.logger.warning("First time run, please fill in the blank of config file (%s)" % _path)
            except:
                self.logger.error("Create config file (%s) failed" % _path)
                self.logger.error(traceback.format_exc())
            sys.exit(0)
        else:
            try:
                with open(_path, 'r') as fp:
                    cfg_tmp = json.load(fp)
                    if not isinstance(cfg_tmp, dict):
                        self.logger.error("Config file has wrong format, please try to delete it first")
                        sys.exit(0)
                    for cfg_key, cfg_val in cfg_tmp.items():
                        if not cfg_key in self.config.keys():
                            self.logger.warning("Invalid config key: %s" % cfg_key)
                            continue
                        self.config[cfg_key] = cfg_val
                    fp.close()
            except IOError:
                self.logger.error("Read config file (%s) failed" % _path)
                sys.exit(0)
            except:
                self.logger.error("Exception while reading config file (%s)" % _path)
                self.logger.error(traceback.format_exc())
                sys.exit(0)

    def _save_cfg_file(self, _path=None):
        data = self.config.copy()
        data.pop('timeout')
        file_path = _path if _path else self.cfg_path
        if not file_path:
            self.logger.debug("cfg_path not specified")
            return False
        try:
            with open(file_path, 'w') as fp:
                json.dump(data, fp, indent=4)
                fp.close()
            self.logger.debug("Finished writing config file")
        except:
            self.logger.warning("Exception while writing config file (%s)" % file_path)
            self.logger.warning(traceback.format_exc())
            sys.exit(0)

    def login_by_cookie(self, eai_sess=None):
        if not eai_sess:
            if "eai_sess" in self.config.keys():
                eai_sess = self.config["eai_sess"]
            else:
                self.logger.error("eai_sess not specified")
                return False
        if eai_sess != '':
            self.session.cookies.set('eai-sess', eai_sess, path='/', domain='.%s' % self.base_domain)
        else:
            self.logger.debug("eai_sess is empty")
            return False
        test_url = '%s%s' % (self.BASE_URL, self.API_GET_SETTING)
        try:
            res = self.session.get(test_url, allow_redirects=False, timeout=self.config['timeout'])
            res.raise_for_status()
            if res.text != '' and '{\"e\":0,' in res.text:
                self.logger.debug("cookie login finished")
                self.login_status = True
                self.config["eai_sess"] = eai_sess
                return True
            else:
                self.logger.debug("cookie login failed, session expired")
        except requests.exceptions.ReadTimeout:
            self.logger.warning("Request timed out while checking cookie")
        except:
            self.logger.warning("Exception while checking cookie")
            self.logger.warning(traceback.format_exc())
        return False

    def login(self, username=None, password=None):
        if 'eai_sess' in self.config.keys() and self.login_by_cookie(self.config['eai_sess']):
            return True

        if not username:
            if self.config['username'] == '':
                self.logger.error("username not specified")
                return False
            else:
                username = self.config['username']

        if not password:
            if self.config['password'] == '':
                self.logger.error("password not specified")
                return False
            else:
                password = self.config["password"]

        url = '%s%s' % (self.BASE_URL, self.API_LOGIN)
        params = {
            'username': username,
            'password': password
        }
        try:
            res = self.session.post(url, data=params, timeout=self.config['timeout'])
            res.raise_for_status()
            self.logger.debug("Login return JSON: %s" % res.text)
            res_json = json.loads(res.text, encoding='utf-8')
            if res_json['e'] != 0:
                if res_json['e'] == 1:
                    self.logger.error("Login failed, wrong username or password")
                else:
                    self.logger.error("Login failed, e = %d, m = %s" % (res_json['e'], res_json['m']))
                return False
            else:
                self.config["eai_sess"] = self.session.cookies.get("eai-sess")
                self.logger.debug("Login finished, eai-sess=%s" % (self.config["eai_sess"]))
                self._save_cfg_file()
                self.login_status = True
                return True
        except requests.exceptions.ReadTimeout:
            self.logger.warning("Request timed out while logging in")
        except Exception as e:
            self.logger.error("Login failed with exception: %s" % e)
            return False

    def report(self):
        url = '%s%s' % (self.BASE_URL, self.API_INDEX)
        try:
            res = self.session.get(url, timeout=self.config['timeout'])
            res.raise_for_status()
            index_json = json.loads(res.text)

            # Detect reporting time and status
            time_name = index_json['d']['date']
            on_time = index_json['d']['ontime']
            read_only = index_json['d']['realonly']
            if on_time and not read_only:
                # Do report
                url = '%s%s' % (self.BASE_URL, self.API_REPORT)
                params = {'tw': 1}
                res = self.session.post(url, data=params, timeout=self.config['timeout'])
                res.raise_for_status()
                report_json = json.loads(res.text)
                if report_json['e'] == 0:
                    self.logger.info("Report for [%s] finished" % time_name)
                    return True
                else:
                    self.logger.error("Report for [%s] failed! e = %s, m = %s" %
                                      (time_name, report_json['e'], report_json['m']))
            else:
                if on_time and read_only:
                    self.logger.info("Report for [%s] already done" % time_name)
                elif not on_time:
                    self.logger.info("Not in report time")
        except requests.exceptions.ReadTimeout:
            self.logger.warning("Request timed out while reporting")
        except:
            self.logger.error("Exception while reporting")
            self.logger.error(traceback.format_exc())
        return False


def print_help():
    print("""--------------------------------
BJUT Daily Three-time Reporter
V 0.1 Alpha (20200907)
--------------------------------

Usage: DailyReport [-c] config_json [-v]
       DailyReport [-u] username [-p] password [-x] proxy_url [-v]

Tips: Recommend to create a cron job for every 15-30 minutes.
      Will automatically detected reporting time and status, since the reporting time is up in the air.

-c (--config-file=) : Config file (in JSON format), will be automatically generated if not exists
-u (--user=)        : Username
-p (--pass=)        : Password
-x (--proxy=)       : Proxy server url (e.g. http://127.0.0.1:8888)
-v (--verbose)      : Verbose output (debug mode)
-h (--help)         : Show help message
    """)


if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], '-c:-u:-p:-proxy-v-h', ['config-file=', 'user=', 'pass=', 'proxy=', 'verbose', 'help'])

    cfg_path = None
    cfg_dic = {}
    is_verbose = False
    for key, val in opts:
        if key in ('-h', '--help'):
            print_help()
            sys.exit(0)
        elif key in ('-c', '--config-file'):
            cfg_path = val
        elif key in ('-u', '--user'):
            cfg_dic['username'] = val
        elif key in ('-p', '--pass'):
            cfg_dic['password'] = val
        elif key in ('-x', '--proxy'):
            cfg_dic['proxy'] = val
        elif key in ('-v', '--verbose'):
            is_verbose = True

    if cfg_path:
        reporter = BJUTReporter(cfg_path=cfg_path, is_verbose=is_verbose)
        reporter.config.update(cfg_dic)
        if 'proxy' in reporter.config.keys():
            reporter.set_proxy(reporter.config['proxy'])
    elif 'username' and 'password' in cfg_dic.keys():
        reporter = BJUTReporter(cfg_dic=cfg_dic, is_verbose=is_verbose)
    else:
        print("Error: Invalid arguments")
        print_help()
        sys.exit(0)

    if reporter.login():
        reporter.report()

