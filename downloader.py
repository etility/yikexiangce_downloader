import multiprocessing as mp
import requests as req
import json
import time
import os

#bdstoken
bdstoken = ""
#yike_cookie_path一刻相册cookie列表json文件路径
yike_cookies_path=''
#保存路径
save_path = ""
#下载照片api，一般不用改，若失效则自行抓包修改
download_url = "https://photo.baidu.com/youai/file/v2/download"

headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    }
#进程数，太多容易异常封ip
num_process = 2

q = mp.Queue(maxsize=num_process * 2)
def request_download_thread(queue):
    jar = request_load_jar()
    while True:
        try:
            pic=queue.get(timeout=10)
        except:
            break
        print("got from queue")
        basename = os.path.basename(pic["path"])
        # 先看本地是否已经下载
        full_path = os.path.join(save_path, basename)
        if os.path.exists(full_path):
            print("path %s exists, continue" % full_path)
            pass
        else:
            print('未下载')
            params = {
                "clienttype": 70,
                "bdstoken": bdstoken,
                "fsid": pic["fsid"]
            }
            r = req.get(url=download_url, cookies=jar, params=params, headers=headers)
            ret_json = r.json()
            errno = ret_json["errno"]
            if errno != 0:
                print("errno 不为 0")
                print(ret_json)
                print(params)
                print(r.request.url)
                print(r.request.headers)
                print(r.cookies)
            dlink = ret_json["dlink"]
            pic_r = req.get(url=dlink, cookies=jar, params=params, headers=headers)
            write_size = 0
            with open(full_path, "wb") as f:
                write_size = f.write(pic_r.content)
            print("save %s ok, size %d k" % (full_path, write_size / 1024))

def request_load_jar():
    jar = req.cookies.RequestsCookieJar()
    with open("yike_cookies.json", encoding="utf8") as f:
        cookies = f.read()
        cookies = json.loads(cookies)
        for cookie in cookies:
            # jar.set(cookie["name"], cookie["value"], domain=cookie["domain"], path=cookie["path"])
            jar.set(cookie["name"], cookie["value"])
    # print(jar)
    return jar
     
def request_download():
    jar = request_load_jar()
    all_list = None
    with open("all_list.json", encoding="utf8") as f:
        all_list = json.loads(f.read())
    process = [mp.Process(target=request_download_thread, args=(q,)) for i in range(num_process)]
    [p.start() for p in process]  # 开启了进程
    print("subprocess start ok")
    for j in range(len(all_list)):
        print("put %d to queue" % j)
        q.put(all_list[j])
    print("waiting for subprocess to stop")
    [p.join() for p in process]  # 等待进程依次结束
    print("stop")

def request_get_list():
    jar = request_load_jar()
    cursor = ""
    has_more = 1
    all_list = []
    # 循环获取所有列表
    while has_more:
        print("cursor is ", cursor)
        list_url = "https://photo.baidu.com/youai/file/v1/list"
        params = {
            "clienttype": 70,
            "bdstoken": bdstoken,
            "need_thumbnail": 1,
            "need_filter_hidden": 0
        }
        if len(cursor) != 0:
            params["cursor"] = cursor

        r = req.get(url=list_url, cookies=jar, params=params, headers=headers)
        ret_json = r.json()
        errno = ret_json["errno"]
        if errno != 0:
            print("errno not 0")
            print(ret_json)
            print(r.status_code)
            print(r.request.url)
            print(r.request.headers)
            break
        has_more = ret_json["has_more"]
        cursor = ret_json["cursor"]
        num = len(ret_json["list"])
        print("获取了 %d 张图片信息" % num)
        all_list.extend(ret_json["list"])
        print("当前共计 %d 张图片信息" % len(all_list))
        print("第一张图片是 %s" % ret_json["list"][0]["path"])
        time.sleep(1)
        # print(ret_json)
    with open("all_list.json", "w", encoding="utf8") as f:
        f.write(json.dumps(all_list))

def request_load_jar():
    jar = req.cookies.RequestsCookieJar()
    with open(yike_cookies_path, encoding="utf8") as f:
        cookies = f.read()
        cookies = json.loads(cookies)
        for cookie in cookies:
            # jar.set(cookie["name"], cookie["value"], domain=cookie["domain"], path=cookie["path"])
            jar.set(cookie["name"], cookie["value"])
    # print(jar)
    return jar


if __name__ == '__main__':
    request_get_list()
    request_download()
