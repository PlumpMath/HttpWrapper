#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import urllib,urllib2,cookielib,zlib
from gzip import GzipFile
from StringIO import StringIO

class HttpWrapperException(Exception): pass
class HttpWrapperResponseData:
    """
    Response data returned by HttpWrapper.Request
    """
    content = None
    url = None
    headers = None
    code = None #Response http code

    def __init__(self,content,url,headers,code):
        self.content = content
        self.url = url
        self.headers = headers
        self.code = code


class HttpWrapper:
    """
    A wrapper of http Request, integrated with cookie handler and content encoding handler
    Usage:
       h = HttpWrapper()
       res = h.Request(url)
       res = h.Request(url,data = dict)
    """

    def __init__(self):
        self.__opener = urllib2.build_opener()
        self.EnableCookieHandler()
        self.EnableConetntEncodingHandler()

    def __FindInstalledHandlers(self,handlerName):
        """
        Find installed handler by handler nameList
        if counldn't find the handler, return None
        if one or more handler find, return handlers list
        """
        nameList = [i.__class__.__name__ for i in self.__opener.handlers]
        if handlerName not in nameList: return None
        return [self.__opener.handlers[i] for i,n in enumerate(nameList) if n == handlerName]

    def __RemoveInstalledHandler(self,handlerName):
        """
        Remove Installed Handler
        """
        searchedHandlers = self.__FindInstalledHandlers(handlerName)
        if searchedHandlers :
            for i in searchedHandlers:
                self.__opener.handlers.remove(i)

                #remove handler error handles in dict cache
                for protocol in self.__opener.handle_error.keys(): #http,https...
                    handlerDict = self.__opener.handle_error[protocol]
                    #handlerDict like {302:[handler 1,handler 2,handler 3],307:[handler 1,handler 2]}
                    for dictKey in handlerDict:
                        for item in handlerDict.get(dictKey):
                            if item == i:
                                handlerDict.get(dictKey).remove(item)

                #remove handler in dict cache
                self.__RemoveHandlerInDictList(self.__opener.handle_error,i)
                self.__RemoveHandlerInDictList(self.__opener.process_request,i)
                self.__RemoveHandlerInDictList(self.__opener.process_response,i)



    def __RemoveHandlerInDictList(self,dictList,handlerWantRemove):
        for protocol in dictList.keys():
            handlerList = self.__opener.handle_open[protocol]
            for item in handlerList:
                if item  == handlerWantRemove:
                    handlerList.remove(item)


    def EnableProxyHandler(self,proxyDict):
        """
        enable proxy handler
        params:
            proxyDict:proxy info for connect, eg. {'http':'10.182.45.231:80','https':'10.182.45.231:80'}
        """
        if proxyDict == None:
            raise HttpWrapperException('you must specify proxyDict when enabled Proxy')
        self.__opener.add_handler(urllib2.ProxyHandler(proxyDict))

    def ShowInstalledHandlers(self):
        """
        get all installed handler for current opener
        """
        print '\r\n====================================================='
        print 'handlers:'
        print [i.__class__.__name__ for i in self.__opener.handlers]
        print '====================================================='
        print 'error_handlers:'
        print self.__opener.handle_error
        print '====================================================='
        print 'process_request:'
        print self.__opener.process_request
        print '====================================================='
        print 'process_response:'
        print self.__opener.process_response
        print '=====================================================\r\n'

    def DisableProxyHandler(self):
        """
        disable proxy handler
        """
        self.__RemoveInstalledHandler('ProxyHandler')

    def EnableAutoRedirectHandler(self):
        """
        enable auto redirect 301,302... pages
        """
        self.__opener.add_handler(urllib2.HTTPRedirectHandler())

    def DisableAutoRedirectHandler(self):
        """
        disable AutoRedirect handler
        """
        self.__RemoveInstalledHandler('HTTPRedirectHandler')

    def EnableCookieHandler(self):
        """
        enable cookie, need this after your login
        """
        cj = cookielib.CookieJar()
        self.__opener.add_handler(urllib2.HTTPCookieProcessor(cj))

    def DisableCookieHandler(self):
        """
        disable cookie handler
        """
        self.__RemoveInstalledHandler('HTTPCookieProcessor')

    def EnableConetntEncodingHandler(self):
        """
        enable content encoding when transmite content, support gzip and deflate
        """
        self.__opener.add_handler(self.__ContentEncodingProcessor())

    def DisableContentEncodingHandler(self):
        """
        disable content encoding handler
        """
        self.__RemoveInstalledHandler('ContentEncodingProcessor')

    class __ContentEncodingProcessor(urllib2.BaseHandler):
        """
        A handler to add gzip capabilities to urllib2 requests
        """

        # add headers to requests
        def http_request(self, req):
            import pdb; pdb.set_trace() ### XXX BREAKPOINT
            req.add_header("Accept-Encoding", "gzip,deflate")
            return req

        # decode
        def http_response(self, req, resp):
            old_resp = resp
            # gzip
            if resp.headers.get("content-encoding") == "gzip":
                gz = GzipFile( fileobj = StringIO(resp.read()), mode="r")
                resp = urllib2.addinfourl(gz, old_resp.headers, old_resp.url, old_resp.code)
                resp.msg = old_resp.msg
            # deflate
            if resp.headers.get("content-encoding") == "deflate":
                gz = StringIO(self.deflate(resp.read()) )
                resp = urllib2.addinfourl(gz, old_resp.headers, old_resp.url, old_resp.code)  # 'class to add info() and
                resp.msg = old_resp.msg
            return resp

        def deflate(self,data):   # zlib only provides the zlib compress format, not the deflate format;
            try:               # so on top of all there's this workaround:
                return zlib.decompress(data, -zlib.MAX_WBITS)
            except zlib.error:
                return zlib.decompress(data)

    def Request(self,url,data=None,headers={}):
        """
        send a request using specified url
        params:
            url     : url you want to send
            data    : additional post data
            headers : headers you want to attach, eg. {'referer' : 'http : //www.baiud.com'}
        """
        #setup request info
        if url is None or url == '':
            raise HttpWrapperException("url can't be empty!")
        if 'user-agent' not in headers:
            headers['user-agent'] = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16'
        self.__opener.addheaders = headers.items()

        try:
            if data is not None:
                req = self.__opener.open(url,data = urllib.urlencode(data))
            else:
                req = self.__opener.open(url)

            resData = HttpWrapperResponseData(req.read(),req.geturl(),req.info().dict,req.getcode())
            req.close()
            return resData
        except urllib2.HTTPError,e:
            return HttpWrapperResponseData(e.fp.read(),'',e.headers,e.code)
            #print e.code
            #print e.msg
            #print e.headers
            #print e.fp.read()
            #print u"error happended:\r\n Location: HttpWrapper.__SendRequest \r\n Error Information:",  sys.exc_info()[1]

if __name__ == '__main__':
    r = HttpWrapper()
    d = r.Request('http://www.baidu.com')
    print d.content
