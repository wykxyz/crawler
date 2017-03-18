#coding:utf-8
import re
import urllib
import urllib2
import socket
import httplib
import time
import cookielib
import os
import Queue
import cStringIO
from PIL import Image

class Spider:
    def __init__(self):
        self.init_page = "https://image.baidu.com/search/index?tn=baiduimage&ct=201326592&lm=-1&cl=2&ie=gbk&word=%C9%D9%B8%BE%B0%C9&fr=ala&ori_query=%E5%B0%91%E5%A6%87%E5%90%A7&ala=0&alatpl=sp&pos=0&hs=2&xthttps=111111"
        self.init_path = "G:/pic1/"
        self.urlQueue = Queue.Queue() #待访问的url队列
        self.vis = set() #保存访问过的url
        self.maxLayer = 5 #定义搜索的最大层数
        self.imgNum = 0
        self.folderNum = 144
        self.maxNumEachFolder = 1000 #定义每个文件夹最大图片数量

        timeOut = 20
        socket.setdefaulttimeout(timeOut) #对整个socket层设置超时时间

        self.mkdir(self.init_path + str(self.folderNum))
        self.headers = {'user-Agent':'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
        self.cookie = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie))


    def mkdir(self, path):
        path  = path.strip()
        if not os.path.exists(path):
            os.mkdir(path)

    def imageFilter(self, imgData): #imgData = urllib2.urlopen(imgUrl).read(); 将过小的图片过滤掉，该图片一般图标图片
        tmp = cStringIO.StringIO(imgData)
        try:
            img = Image.open(tmp)
        except IOError:
            return False
        if img.size[0] + img.size[1] <= 150 or img.size[0] <= 50 or img.size[1] <= 50: #过滤图片
            return False
        else:
            return True

    def getHtml(self, currentUrl): #获取网页html源码
        print currentUrl
        try:
            sleep_download_time = 4
            time.sleep(sleep_download_time)
            request = urllib2.Request(url=currentUrl,headers=self.headers)
            response = self.opener.open(request)
            return response.read()
        #except urllib2.URLError or httplib.HTTPException or socket.timeout:
        except:
            return False

    def checkUrl(self, currentUrl): #检查没用的url
        pattern  = re.compile(r'.zip|.avi|.mp4|.rmvb|.rm$', re.S)
        if re.search(pattern, currentUrl):
            return False
        else:
            return True

    def uniform(self, item, currentUrl): #将获取的url地址归一化为：http://abcd...
        pattern1 = re.compile(r'https?://')
        pattern2 = re.compile(r'//')
        pattern3 = re.compile(r'/')
        pattern4 = re.compile(r'./')
        pattern5 = re.compile(r'../')
        if re.match(pattern1, item):
            return str(item).rstrip('/')
        elif re.match(pattern2, item):
            return 'http:' + str(item).rstrip('/')
        elif re.match(pattern3, item):
            item = currentUrl + item
            return str(item).rstrip('/')
        elif re.match(pattern4, item):
            currentUrl = re.sub("/[^/]*?$", '', currentUrl, re.S) #./abc表示要先退回上层目录
            item = str(item).lstrip('.')
            item = currentUrl + item
            return str(item).rstrip('/')
        elif re.match(pattern5, item):
            currentUrl = re.sub("/[^/]*?/[^/]*?$", '', currentUrl, re.S) #../abc表示要先退回上上层目录
            item = str(item).lstrip('..')
            item = currentUrl + item
            return str(item).rstrip('/')
        else:
            return currentUrl + '/' + str(item).rstrip('/')

    def store(self, currentUrl): #存储当前页面的图片
        if not self.checkUrl(currentUrl):
            return False
        currentHtml = self.getHtml(currentUrl)
        if not currentHtml: #当前页面打不开
            return False
        pattern = re.compile(r'<img.*?src.*?=.*?"(.*?)"', re.S)
        imgsUrl = re.findall(pattern, currentHtml) #获取当前页面下所有img的src
        for imgUrl in imgsUrl:
            print imgUrl
            imgUrl = self.uniform(imgUrl, currentUrl)
            print imgUrl
            try:
                img = urllib2.urlopen(imgUrl)
                imgData = img.read()
            #except urllib2.URLError or socket.error or socket.timeout:
            except:
                continue
            if not self.imageFilter(imgData):
                continue
            if self.imgNum == self.maxNumEachFolder:
                self.folderNum += 1
                self.imgNum = 0
                self.mkdir(self.init_path + str(self.folderNum))
            fileName = self.init_path + str(self.folderNum) + '/' + str(self.imgNum) + '.' + 'jpg'
            f = open(fileName, 'wb')
            f.write(imgData)
            f.close()
            self.imgNum += 1
        return True

    def extractUrls(self, currentUrl): #提取出当前页面下的所有链接
        currentHtml = self.getHtml(currentUrl)
        nextUrls = []
        pattern = re.compile(r'<a href=.*?"(.*?)"', re.S)
        if not currentHtml:
            return nextUrls
        items = re.findall(pattern, currentHtml)
        for item in items:
            item = self.uniform(item, currentUrl)
            nextUrls.append(item)
        return nextUrls

    def bfs(self):
        initNode = [self.init_page.rstrip('/'), 1] #当前url和所属的层数
        self.urlQueue.put(initNode)
        self.vis.add(self.init_page)
        while not self.urlQueue.empty():
            currentNode = self.urlQueue.get()
            currentUrl = currentNode[0] #当前url
            currentLayer = currentNode[1] #当前层数
            flag = self.store(currentUrl) #存储当前页面的图片
            if flag == False:
                continue
            if currentLayer <= self.maxLayer:
                for nextUrl in self.extractUrls(currentUrl): #提取出当前页面下的所有链接
                    if nextUrl not in self.vis:
                        self.vis.add(nextUrl)
                        currentNode = [nextUrl, currentLayer + 1]
                        self.urlQueue.put(currentNode)

spider = Spider()
spider.bfs()