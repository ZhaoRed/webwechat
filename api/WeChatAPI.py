#!/usr/bin/python
# -*- coding:UTF-8 -*-

import random
import time
import urllib
import urllib2
import re
import xml.dom.minidom
import json
import os
#from msg import Msg as msg
import sys


def _decode_data(data):
    """
    @brief      decode array or dict to utf-8
    @param      data   array or dict
    @return     utf-8
    """
    if isinstance(data, dict):
        rv = {}
        for key, value in data.iteritems():
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            rv[key] = _decode_data(value)
        return rv
    elif isinstance(data, list):
        rv = []
        for item in data:
            item = _decode_data(item)
            rv.append(item)
        return rv
    elif isinstance(data, unicode):
        return data.encode('utf-8')
    else:
        return data


class WeChatAPI(object):

    def __init__(self):
        self.hosts = {
            "weixin.qq.com":['login.weixin.qq.com','file.wx.qq.com','webpush.weixin.qq.com'],
            "wx2.qq.com":['login.wx2.qq.com','file.wx2.qq.com','webpush.wx2.qq.com'],
            "wx8.qq.com":['login.wx8.qq.com','file.wx8.qq.com','webpush.wx8.qq.com'],
            "qq.com":['login.wx.qq.com','file.wx.qq.com','webpush.wx.qq.com'],
            "wechat.com":['login.web.wechat.com','file.web.wechat.com','webpush.web.wechat.com'],
            "web2.wechat.com":['login.web2.wechat.com','file.web2.wechat.com','webpush.web2.wechat.com']
        }
        self.file_host = None
        self.appid = 'wx782c26e4c19acffb'
        self.uuid = ''
        self.redirect_uri = None
        self.skey = ''
        self.sid = ''
        self.uid = ''
        self.pass_ticket = ''
        self.is_grayscale = 0
        self.base_request = {}
        self.sync_key_dic = []
        self.sync_key = ''
        # device_id: 登录手机设备
        # web wechat 的格式为: e123456789012345 (e+15位随机数)
        # mobile wechat 的格式为: A1234567890abcde (A+15位随机数字或字母)
        self.device_id = 'e' + repr(random.random())[2:17]
        #the user had login
        self.user = []
        self.contact_list = []
        self.member_count = 0
        self.member_list = []
        #contactors
        self.contact_list = []
        #groups
        self.group_list = []
        self.fun = 'new'
        self.lang = 'zh_CN'
        self.version='0.1'
        self.wxversion = 'v2'

    def get_uuid(self):
        url = "https://login.weixin.qq.com/jslogin";
        params = {
            'appid': self.appid,
            'fun': self.fun,
            'lang': self.lang,
            '_': int(time.time())
        }
        request = urllib2.Request(url, urllib.urlencode(params))
        response = urllib2.urlopen(url=request, timeout=30)
        data = response.read()
        response.close()
        regx = r'wechat.QRLogin.code = (\d+); wechat.QRLogin.uuid = "(\S+?)"'
        if self.set_uuid(regx,data):
            pass
        else:
            regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
            if self.set_uuid(regx, data):
                pass
        '''
        pm = re.search(regx, data)
        if pm:
            code = pm.group(1)
            self.uuid = pm.group(2)
            print("code:" + code + ",uuid:" + self.uuid)
        else:
        '''
        return data

    def set_uuid(self,regx,data):
        pm = re.search(regx, data)
        if pm:
            code = pm.group(1)
            self.uuid = pm.group(2)
            return True
        else:
            return False

    def generate_qrcode(self):
        #print("self.uuid"+self.uuid)
        url = "https://login.weixin.qq.com/qrcode/" + self.uuid;
        params = {
            't': 'webwx',
            '_': int(time.time())
        }
        request = urllib2.Request(url, urllib.urlencode(params))
        response = urllib2.urlopen(url=request, timeout=30)
        data = response.read()
        response.close()

        image = os.environ['HOME']+"/.wechat/qrcode.jpg"
        #image = "/home/zhaohongxing/.wechat/qrcode.jpg"
        with open(image, 'wb') as image:
            image.write(data)
            return image

    '''
        tip = 0 已扫描
        tip = 1 未扫描
        turn
        408 timeout
        200
        201
    '''
    def wait4login(self,tip=1):
        url = "https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login" + "?tip=" + str(tip) + "&uuid=" + self.uuid + "&_" + str(int(time.time()))
        request = urllib2.Request(url)
        response = urllib2.urlopen(url=request, timeout=30)
        data = response.read()
        print(data)
        data = data.replace("\n","")
        data = data.replace("\r","")
        pm = re.search(r'wechat.code=(\d+);', data)
        if not pm:
            pm = re.search(r'window.code=(\d+);', data)
        code = pm.group(1)
        if code == '201':
            return True
        elif code == '200':
            pm = re.search(r'wechat.redirect_uri="(\S+?)";', data)
            if not pm:
                pm = re.search(r'window.redirect_uri="(\S+?)";', data)
            if not pm:
                return False
            rd_uri = pm.group(1) + '&fun='+self.fun + '&version=v2'
            self.redirect_uri = rd_uri
            return True
        elif code == '408':
            print("error 408")
        else:
            print("unknow error")

        return False

    '''
    return:
        <error>
            <ret>0</ret>
            <message>OK</message>
            <skey>xxx</skey>
            <wxsid>xxx</wxsid>
            <wxuin>xxx</wxuin>
            <pass_ticket>xxx</pass_ticket>
            <isgrayscale>1</isgrayscale>
        </error>
    '''
    def login(self):
        url = self.redirect_uri;
        print("redirect_uri="+url)
        request = urllib2.Request(url)
        response = urllib2.urlopen(url=request, timeout=30)
        data = response.read()
        response.close()
        doc = xml.dom.minidom.parseString(data)
        root = doc.documentElement
        for node in root.childNodes:
            for cn in node.childNodes:
                if node.nodeName == 'ret':
                    if cn.data != "0":
                        return False
                elif node.nodeName == 'skey':
                    self.skey = cn.data
                elif node.nodeName == 'wxsid':
                    self.sid = cn.data
                elif node.nodeName == 'wxuin':
                    self.uin = cn.data
                elif node.nodeName == 'pass_ticket':
                    self.pass_ticket = cn.data
                elif node.nodeName == 'isgrayscale':
                    self.isgrayscale = cn.data

        self.base_request = {
            'Uin': int(self.uin),
            'Sid': str(self.sid),
            'Skey': str(self.skey),
            'DeviceID': self.device_id,
        }
        return True

    def webwx_init(self):
        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit"+ \
            '?pass_ticket=%s&r=%s&lang=%s' % (
            self.pass_ticket, int(time.time()),self.lang
        )
        params = {
            'BaseRequest': self.base_request
        }
        headers = {
            'User-Agent': "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)",
            "Content-Type": "application/json; charset=UTF-8",
            'Connection': 'keep-alive',
            "Referer": "https://wx.qq.com"
        }

        request = urllib2.Request(url=url, data=json.dumps(params, ensure_ascii=False).encode('utf8'),headers=headers)
        request.add_header("Content-Type","application/json; charset=UTF-8")
        response = urllib2.urlopen(request, timeout=30)
        data = response.read()
        dict = json.loads(data,object_hook=_decode_data)
        response.close()
        #print("webwx_init response data:")
        #print(dict)
        self.user = dict['User']
        self.contact_list = dict['ContactList']
        self.sync_key_dic = dict['SyncKey']

        def foo(x):
            return str(x['Key']) + '_' + str(x['Val'])

        self.sync_key = '%7C'.join([foo(keyVal) for keyVal in self.sync_key_dic['List']])
        return dict

    def webwx_status_notify(self):
        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxstatusnotify" + \
              '?pass_ticket=%s&lang=%s' % (
                  self.pass_ticket, self.lang
              )
        params = {
            'BaseRequest': self.base_request,
            'Code' : 3,
            'FromUserName': self.user['UserName'],
            'ToUserName': self.user['UserName'],
            'ClientMsgId': int(time.time())
        }
        headers = {
            'User-Agent': "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)",
            "Content-Type": "application/json; charset=UTF-8",
            'Connection': 'keep-alive',
            "Referer": "https://wx.qq.com"
        }

        request = urllib2.Request(url=url, data=json.dumps(params, ensure_ascii=False).encode('utf8'), headers=headers)
        response = urllib2.urlopen(request, timeout=30)
        data = response.read()
        response.close()
        return data

    def webwx_get_contact(self):
        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact" + \
              '?pass_ticket=%s&lang=%s' % (
                  self.pass_ticket, self.lang
              )
        params = {
            'BaseRequest': self.base_request
        }
        headers = {
            'User-Agent': "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)",
            "Content-Type": "application/json; charset=UTF-8",
            'Connection': 'keep-alive',
            "Referer": "https://wx.qq.com"
        }

        request = urllib2.Request(url=url, data=json.dumps(params, ensure_ascii=False).encode('utf8'), headers=headers)
        response = urllib2.urlopen(request, timeout=30)
        data = response.read()
        response.close()
        dict = json.loads(data, object_hook=_decode_data)
        self.member_list = dict['MemberList']
        self.member_count = dict['MemberCount']
        
        return dict

    '''
        return wechat.synccheck={retcode:"xxx",selector:"xxx"}
        retcode:
            0:success
            1100:failed/logout
            1101:login otherwhere
            1102:?
    '''
    def sync_check(self):
        url = "https://webpush.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck"
        url = "https://webpush.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck" + \
              '?r=%d&skey=%s&sid=%s&uin=%d&deviceid=%s&synckey=%s&_=%d' % (
                  int(round(time.time() * 1000)),str(self.skey),str(self.sid),int(self.uin), str(self.device_id),str(self.sync_key),int(round(time.time() * 1000))
              )
        params = {
            'r': int(time.time()),
            'skey': str(self.skey),
            'sid': str(self.sid),
            'uin': int(self.uin),
            'deviceid': str(self.device_id),
            'synckey': str(self.sync_key),
            '_': int(time.time())
        }

        headers = {
            'User-Agent': "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)",
            'Connection': 'keep-alive',
            "Referer": "https://wx.qq.com/?&lang=zh_TW"
        }
        #url = url + '?' + urllib.urlencode(params)
        request = urllib2.Request(url=url)

        request.add_header('Connection', 'keep-alive')
        request.add_header('Referer', 'https://wx.qq.com/')
        #request.add_header("Content-Type","application/json; charset=UTF-8")
        response = urllib2.urlopen(request, timeout=60)
        print("full-url:"+response.geturl())
        print(response.getcode())
        data = response.read()
        response.close()
        print("sync_check response:")
        print(data)
        return data

    def webwx_sync(self):

        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsync" + \
            '?sid=%s&skey=%s&pass_ticket=%s' % (
                self.sid, self.skey, self.pass_ticket
            )
        params = {
            'BaseRequest': self.base_request,
            'SyncKey':self.sync_key_dic,
            'rr':~int(time.time())
        }
        headers = {
            'User-Agent': "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)",
            "Content-Type": "application/json; charset=UTF-8",
            "Referer": "https://wx.qq.com"
        }

        request = urllib2.Request(url=url, data=json.dumps(params, ensure_ascii=False).encode('utf8'), headers=headers)
        response = urllib2.urlopen(request, timeout=30)
        data = response.read()
        response.close()
        return data

    def webwx_send_msg(self,msg):
        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg" + \
              '?pass_ticket=%s' % (
                  self.pass_ticket
              )
        local_id = client_msg_id = str(int(time.time() * 1000)) + \
            str(random.random())[:5].replace('.', '')

        params = {
            'BaseRequest': self.base_request,
            'Msg': {
                "Type":msg.type,
                "Content":msg.content,
                "FromUserName":self.user['UserName'],
                "ToUserName":msg.to_user_name,
                "LocalID":local_id,
                "ClientMsgId":client_msg_id,
            }
        }
        headers = {
            'User-Agent': "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)",
            "Content-Type": "application/json; charset=UTF-8",
            "Referer": "https://wx.qq.com"
        }

        request = urllib2.Request(url=url, data=json.dumps(params, ensure_ascii=False).encode('utf8'), headers=headers)
        response = urllib2.urlopen(request, timeout=30)
        data = response.read()
        response.close()
        print(data)
        return data

    def webwx_revoke_msg(self,msg):
        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg" + \
              '?pass_ticket=%s' % (
                  self.pass_ticket
              )
        local_id = client_msg_id = str(int(time.time() * 1000)) + \
            str(random.random())[:5].replace('.', '')

        params = {
            'BaseRequest': self.base_request,
            'Msg': {
                "Type":msg.type,
                "Content":msg.content,
                "FromUserName":self.user['UserName'],
                "ToUserName":msg.to_user_name,
                "LocalID":local_id,
                "ClientMsgId":client_msg_id,
            }
        }
        headers = {
            'User-Agent': "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)",
            "Content-Type": "application/json; charset=UTF-8",
            "Referer": "https://wx.qq.com"
        }

        request = urllib2.Request(url=url, data=json.dumps(params, ensure_ascii=False).encode('utf8'), headers=headers)
        response = urllib2.urlopen(request, timeout=30)
        data = response.read()
        response.close()
        print(data)
        return data

if __name__ =="__main__":

    print(long(time.time()))
    #sys.exit(0)

    '''
    dd = 'window.code=200;\nwindow.redirect_uri="https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage?ticket=AX0Rc5T1YmYIooRoxiAzKO-0@qrticket_0&uuid=wY0ILqfpwA==&lang=zh_CN&scan=1514535338";'
    print(dd)
    pm = re.search(r'window.redirect_uri="(\S+?)";', dd)
    print pm.group(1)
    sys.exit(0)
    '''

    api = WeChatAPI()
    uuid = api.get_uuid()
    api.generate_qrcode()
    res = api.wait4login()
    print(res)
    if not api.redirect_uri:
        res = api.wait4login()
        print(res)
    res = api.login()
    #print(res)
    init_response = api.webwx_init()
    #print(init_response)
    api.webwx_status_notify()
    api.webwx_get_contact()
    api.sync_check()
    #da = api.webwx_sync()





