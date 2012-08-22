# -*- coding: utf-8 -*-

import hmac, base64, hashlib
import json
import os
import urllib

try:
    from bae.api import logging
except:
    import logging

from httpc import HttplibHTTPC

ERR_OK       = 0
ERR_RESPONSE = -1

class BaeBCS(object):
    def __init__(self, host=None, ak=None, sk=None, httpclient_class=None):
        """���캯��
        ����:            
            host(str):       BCS��������ַ
            ak(str):         access key
            sk(str):         secret key
            httpclient_class:  ��BCS������������HTTP�ӿ��࣬Ĭ��ΪHttplibHTTPC
        """
        self.host = host
        self.ak   = ak
        self.sk   = sk
        if self.host.endswith('/') :
            self.host = host[:-1]
        if not self.host.startswith('http'):
            self.host = "http://" + self.host
        hc_class = (httpclient_class if httpclient_class else HttplibHTTPC)
        self.httpc = hc_class()
        self.get_url = self._sign('GET', '', '/')

    def list_buckets(self):
        """�о������Լ���buckets
        ������
        ����ֵ��
            ����ֵΪ (errcode, response)��ʽ��tuple
            ����errcodeΪ�����룬ERR_OK��ʾ�ɹ���������ʾʧ��
            �ɹ�����£�responseΪbucket name�б�
            ʧ������£�response�Ƿ��������ص�ԭʼ��Ϣ
        �쳣��
            httplib.HTTPException:  ͬ��˽��������г����������
        """

        r = self.httpc.get(self.get_url)
        e, d = self._handle_response(r, 2)
        if e != ERR_OK:
            return (e, d)
        return (e, [b['bucket_name'].encode('utf8') for b in d])

    def put_object(self, bname, oname, data):
        """�ϴ����ݵ�ָ��object
        ������
            bname(str):     bucket name������Ԥ�ȴ���
            oname(str):     object name
            data��          ���ϴ�������
        ����ֵ��
            ����ֵΪ (errcode, response)��ʽ��tuple
            ����errcodeΪ�����룬ERR_OK��ʾ�ɹ���������ʾʧ��
            �ɹ�����£�responseΪNone
            ʧ������£�response�Ƿ��������ص�ԭʼ��Ϣ
        �쳣��
            httplib.HTTPException:  ͬ��˽��������г����������
        """
        url = self._sign('PUT', bname, oname)
        r = self.httpc.put(url, data, headers={})
        return self._handle_response(r)
 
    def get_object(self, bname, oname):
        """����object
        ������
            bname(str):     bucket name������Ԥ�ȴ���
            oname(str):     object name
        ����ֵ��
            ����ֵΪ (errcode, response)��ʽ��tuple
            ����errcodeΪ�����룬ERR_OK��ʾ�ɹ���������ʾʧ��
            �ɹ�����£�responseΪobject��Ӧ������
            ʧ������£�responseΪ���������ص�ԭʼ��Ϣ
        �쳣��
            httplib.HTTPException:  ͬ��˽��������г����������
        """
        url = self._sign('GET', bname, oname)
        r = self.httpc.get(url, headers={})
        return self._handle_response(r, 1)

    def del_object(self, bname, oname):        
        """ɾ��object
        ������
            bname(str):     bucket name������Ԥ�ȴ���
            oname(str):     object name
        ����ֵ��
            ����ֵΪ (errcode, response)��ʽ��tuple
            ����errcodeΪ�����룬ERR_OK��ʾ�ɹ���������ʾʧ��
            �ɹ�����£�responseΪNone
            ʧ������£�response�Ƿ��������ص�ԭʼ��Ϣ
        �쳣��
            httplib.HTTPException:  ͬ��˽��������г����������
        """
        url = self._sign('DELETE', bname, oname)
        r = self.httpc.delete(url, headers={})
        return self._handle_response(r)

    def list_objects(self, bname, prefix='', start=0, limit=100):
        """�о�ָ��bucket�µ�����object
        ������
            bname(str):     bucket name������Ԥ�ȴ���
            prefix(str)��   ��ָ������ֻ���ط���prefix��object
            start(int):     list��ʼ�±꣬Ĭ��Ϊ0
            limit(int):     ���ؽ����������Ĭ��Ϊ100
        ����ֵ��
            ����ֵΪ (errcode, response)��ʽ��tuple
            ����errcodeΪ�����룬ERR_OK��ʾ�ɹ���������ʾʧ��
            �ɹ�����£�responseΪobject name�б�
            ʧ������£�responseΪ���������ص�ԭʼ��Ϣ
        �쳣��
            httplib.HTTPException:  ͬ��˽��������г����������
        """
        params = { 'start': start, 'limit': limit}
        if prefix:
            params.update ({'prefix': prefix})
        url = self._sign('GET', bname, '/') + '&' + urllib.urlencode(params)
        r = self.httpc.get(url)
        e, d = self._handle_response(r, 2)
        if e != ERR_OK:
            return (e, d)
        return (e, [o['object'].encode('utf-8') for o in d['object_list'] ]) 

    def copy_object(self, src_bname, src_oname, dst_bname, dst_oname):
        """ ����object
        ������
            src_bname(str):     Դbucket name
            src_oname(str):     Դobject name
            dst_bname(str):     Ŀ��bucket name
            dst_oname(str):     Ŀ��object name
        ����ֵ��
            ����ֵΪ (errcode, response)��ʽ��tuple
            ����errcodeΪ�����룬ERR_OK��ʾ�ɹ���������ʾʧ��
            �ɹ�����£�responseΪNone
            ʧ������£�response�Ƿ��������ص�ԭʼ��Ϣ
        �쳣��
            httplib.HTTPException:  ͬ��˽��������г����������
        """
        headers = {}
        headers.update( {
                'x-bs-copy-source': src_oname,
                'x-bs-copy-source-directive': 'copy', # copy or replace
                })
        url = self._sign('PUT', dst_bname, dst_oname)
        r = self.httpc.put(url, '', headers)
        return self._handle_response(r)

    def put_superfile(self, bname, oname, objlist):
        """�ϴ�superfile
        ������
            bname(str):     bucket name������Ԥ�ȴ���
            oname(str):     object name
            objlist(list)�� ���superfile��object�б���ʽΪ [('bucket1', '/obj1'), ('bucket2', '/obj2')]          
        ����ֵ��
            ����ֵΪ (errcode, response)��ʽ��tuple
            ����errcodeΪ�����룬ERR_OK��ʾ�ɹ���������ʾʧ��
            �ɹ�����£�responseΪNone
            ʧ������£�response�Ƿ��������ص�ԭʼ��Ϣ
        �쳣��
            httplib.HTTPException:  ͬ��˽��������г����������
        """
        l = []
        try:
            for idx, (b, o) in enumerate(objlist):
                r = self._head_object(b, o)
                etag = r['header']['etag']
                l.append('"part_%d": {"url": "bs://%s/%s", "etag":"%s"}' % (
                    idx, b, o, etag))
        except Exception, e:
            return (ERR_RESPONSE, str(e))

        meta = '{"object_list": {%s}}' % (  ','.join(l)  )
        url = self._sign('PUT', bname, oname) + '&superfile=1'
        r = self.httpc.put(url, meta, headers={})
        return self._handle_response(r)

    def set_acl(self, bname, oname, acl):
        """ ����bucket����object��ACL
        ������
            bname(str):     bucket name������Ԥ�ȴ���
            oname(str):     object name����Ϊ''����ʾ����bucket��ACL����������object��ACL
            acl(str)��      ����ָ��bucket��object��ACL���ַ���
        ����ֵ��
            ����ֵΪ (errcode, response)��ʽ��tuple
            ����errcodeΪ�����룬ERR_OK��ʾ�ɹ���������ʾʧ��
            �ɹ�����£�responseΪNone
            ʧ������£�response�Ƿ��������ص�ԭʼ��Ϣ
        �쳣��
            httplib.HTTPException:  ͬ��˽��������г����������
        """
        url = self._sign('PUT', bname, oname) + '&acl=1'
        r = self.httpc.put(url, acl, headers={})
        return self._handle_response(r)

    def get_acl(self, bname, oname):
        """ ��ȡbucket����object��ACL
        ������
            bname(str):     bucket name������Ԥ�ȴ���
            oname(str):     object name����Ϊ'',��ʾ��ȡbucket��ACL�������ȡobject��ACL
        ����ֵ��
            ����ֵΪ (errcode, response)��ʽ��tuple
            ����errcodeΪ�����룬ERR_OK��ʾ�ɹ���������ʾʧ��
            �ɹ�����£�responseΪ����bucket��object��Ӧ��ACL���ַ���
            ʧ������£�responseΪ���������ص�ԭʼ��Ϣ
        �쳣��
            httplib.HTTPException:  ͬ��˽��������г����������
        """
        url = self._sign('GET', bname, oname) + '&acl=1'
        r = self.httpc.get(url, headers={})
        return self._handle_response(r, 1)

    def put_file(self, bname, oname, filename):
        """�ϴ��ļ���ָ����object
        ������
            bname(str):     bucket name������Ԥ�ȴ���
            oname(str):     object name
            filename(str)�� ���ϴ����ļ�
        ����ֵ��
            ����ֵΪ (errcode, response)��ʽ��tuple
            ����errcodeΪ�����룬ERR_OK��ʾ�ɹ���������ʾʧ��
            �ɹ�����£�responseΪNone
            ʧ������£�response�Ƿ��������ص�ԭʼ��Ϣ
        �쳣��
            httplib.HTTPException:  ͬ��˽��������г����������
        """
        if not os.path.isfile(filename):
            raise Exception(filename + ' is not a file')

        url = self._sign('PUT', bname, oname)
        r = self.httpc.put_file(url, filename, headers={})
        return self._handle_response(r)

    def get_to_file(self, bname, oname, filename):
        """ ����ָ��object�����ݣ������浽ָ���ļ���
        ������
            bname(str):     bucket name������Ԥ�ȴ���
            oname(str):     object name
            filename(str)�� ���ڱ������ݵ��ļ�
        ����ֵ��
            ����ֵΪ (errcode, response)��ʽ��tuple
            ����errcodeΪ�����룬ERR_OK��ʾ�ɹ���������ʾʧ��
            �ɹ�����£�responseΪNone
            ʧ������£�response�Ƿ��������ص�ԭʼ��Ϣ
        �쳣��
            httplib.HTTPException:  ͬ��˽��������г����������
        """
        url = self._sign('GET', bname, oname)
        r = self.httpc.get_file(url, filename, headers={})
        return self._handle_response(r)

    def make_public(self, bname, oname, user=None):
        """ ����ָ��user����ָ����bucket��object
        ������
            bname(str):     bucket name������Ԥ�ȴ���
            oname(str):     object name
            user(str)��     ��Ȩ���û����ƣ�����ָ�������ʾ�����û�
        ����ֵ��
            ����ֵΪ (errcode, response)��ʽ��tuple
            ����errcodeΪ�����룬ERR_OK��ʾ�ɹ���������ʾʧ��
            �ɹ�����£�responseΪNone
            ʧ������£�response�Ƿ��������ص�ԭʼ��Ϣ
        �쳣��
            httplib.HTTPException:  ͬ��˽��������г����������
        """

        acl = '{"statements":[{"action":["*"],"effect":"allow","resource":["%s%s"],"user":["%s"]}]}' % (
            bname, oname, (user if user else "*"))
        return self.set_acl(bname, oname, acl)


    ### internal functions        
    def _sign(self, M, B, O, T=None, I=None, S=None):
        flag = ''
        s =  ''
        if M :   flag+='M'; s += 'Method=%s\n' % M; 
        if B :   flag+='B'; s += 'Bucket=%s\n' % B; 
        if O :   flag+='O'; s += 'Object=%s\n' % O; 
        if T :   flag+='T'; s += 'Time=%s\n'   % T; 
        if I :   flag+='I'; s += 'Ip=%s\n'     % I; 
        if S :   flag+='S'; s += 'Size=%s\n'   % S; 

        s = '\n'.join([flag, s])
        
        def h(sk, body):
            digest = hmac.new(sk, body, hashlib.sha1).digest()
            t = base64.encodestring(digest)
            return urllib.quote(t.strip())

        sign = h(self.sk, s)
        url = '%s/%s%s?sign=%s:%s:%s' % (
                self.host, B, '/' + urllib.quote(O[1:]), 
                flag, self.ak, sign)
        if T :      url += '&time=%s'   % T;
        if I :      url += '&ip=%s'     % I; 
        if S :      url += '&size=%s'   % S; 
        return url

    def _head_object(self, bname, oname):
        url = self._sign('HEAD', bname, oname)
        return self.httpc.head(url, headers={})

    def _handle_response(self, r, body=0):
        if not isinstance(r, dict):
            return (ERR_RESPONSE, r)

        try:
            status = r['status']
            if status not in [200, 206]:
                j = json.loads(r['body'])
                return (int(j['Error']['code']), r)

            ### success
            if body == 0:
                return (ERR_OK, None)
            elif body == 1:
                return (ERR_OK, r['body'])
            else:
                return (ERR_OK, json.loads(r['body']))
        except Exception, e:
            logging.warning("_handle_response exception: %s" % str(e))
            return (ERR_RESPONSE, r)

