# -*- coding: utf-8 -*-
# @Time    : 2021/4/30 11:25
# @Author  : Ryan

import json

import requests

from runtime_config import config


class Message:
    """
    钉钉消息通知类
    
    封装钉钉机器人API，用于发送交易相关的通知和告警信息。支持买入、卖出订单的
    自动通知以及异常情况的告警推送。可配置多个钉钉token实现分级通知。
    """

    def dingding_warn(self, text, isDefaultToken=True):
        """
        发送钉钉告警消息
        
        通过钉钉机器人Webhook发送文本消息。支持使用不同的token实现分级通知，
        当token未配置时会降级为控制台输出。
        
        :param text: 要发送的消息内容
        :param isDefaultToken: 是否使用默认token，True使用主token，False使用备用token
        """
        # 钉钉通知未启用，直接返回
        if not config.get('dingding.enabled', True):
            return

        tmpToken = config.get('dingding.token', '') if isDefaultToken else config.get('dingding.token2', '')
        if (tmpToken == ''):
            print('dingidng:' + text)
            return
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        api_url = "https://oapi.dingtalk.com/robot/send?access_token=%s" % tmpToken
        print("api_url=")
        print(api_url)
        json_text = self._msg(text + "\n______")
        response = requests.post(api_url, json.dumps(json_text), headers=headers).content
        print(response)

    def _msg(self, text):
        """
        构建钉钉消息JSON格式
        
        将文本内容封装为钉钉机器人API要求的JSON格式，包含@提醒配置。
        
        :param text: 消息文本内容
        :return: 符合钉钉API规范的字典对象
        """
        json_text = {
            "msgtype": "text",
            "at": {
                "atMobiles": [
                    "11111"
                ],
                "isAtAll": False
            },
            "text": {
                "content": text
            }
        }
        return json_text


if __name__ == "__main__":
    msg = Message()
    msg.dingding_warn("钉钉消息推送", True)
    msg.dingding_warn("钉钉消息推送token2", True)
