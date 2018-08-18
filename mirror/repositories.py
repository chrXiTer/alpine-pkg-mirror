
import os
from urllib import parse
import tarfile
import io

from utils import get_file

class Repository(object):
    def __init__(self, name, mirror_path,  **kwargs):
        self._name = name
        self._mirror_path = mirror_path
        self._details = kwargs

        if not os.path.exists(self._mirror_path):
            os.makedirs(self._mirror_path)
        self._index_path = os.path.join(self._mirror_path, 'APKINDEX.tar.gz')
        self.APKINDEX_FIELDS = {
            'P': 'package',
            'V': 'version',
            'A': 'architecture',
            'T': 'description',
            'L': 'licence',
            'U': 'project',
            'S': 'size',
            'o': 'origin',
            'm': 'maintaner',
            't': 'build-time',
            'c': 'commit',
            'I': 'installed-size',
        }

    @property
    def url(self):
        return self._details['url']

    @property
    def index_url(self):
        return parse.urljoin(self.url, 'APKINDEX.tar.gz')

    def get_next_packages_info(self):
        filename = self._index_path
        targz = tarfile.open(filename)
        apkindexB = targz.extractfile('APKINDEX')
        apkindex = io.TextIOWrapper(apkindexB, encoding="utf-8")
        pkg_info = dict()

        while True:
            data = apkindex.readline()
            if not data:
                break
            data2 = data.strip()
            if not data2:
                if pkg_info:
                    yield pkg_info
                    pkg_info = dict()
                continue
            k,v = data2.split(':', 1)
            pkg_info[self.APKINDEX_FIELDS.get(k, k)] = v
        if pkg_info:
            yield pkg_info

    def deleteOld(self):
        allInfo = {}
        for info in self.get_next_packages_info():
            fileName = "%s-%s.apk" % (info['package'], info['version'])
            allInfo[fileName] = info
        fileNames = os.listdir(self._mirror_path) 
        for fileName in fileNames:
            if fileName == "APKINDEX.tar.gz":
                continue
            filePath = os.path.realpath(os.path.join(self._mirror_path, fileName))
            fileSize = os.stat(filePath).st_size
            if fileName not in allInfo.keys() or int(allInfo[fileName]['size']) != fileSize:
                print("删除文件：%s" % fileName)
                os.remove(filePath)


    def getNeedUrlPaths(self):
        needUrlPaths = []
        for info in self.get_next_packages_info():
            file_name = "%s-%s.apk" % (info['package'], info['version'])
            file_path = os.path.realpath(os.path.join(self._mirror_path, file_name))
            if os.path.exists(file_path):
                file_size = os.stat(file_path).st_size
                if file_size == int(info['size']):
                    continue
            file_url = parse.urljoin(self.url, file_name)
            needUrlPaths.append({"url":file_url, "path":file_path})
        return needUrlPaths
    
    def splitUrlPath(self, num, urlPaths):
        urlPathsGroup = [[] for x in range(num)]
        for i in range(0, len(urlPaths)):
            urlPathsGroup[i % num].append(urlPaths[i])
        return urlPathsGroup

    def getNeedUrlPathsNGroup(self, num):
        needUrlPaths = self.getNeedUrlPaths()
        urlPathsGroup = self.splitUrlPath(num, needUrlPaths)
        print("*****%s*****" %len(needUrlPaths))
        return urlPathsGroup



    