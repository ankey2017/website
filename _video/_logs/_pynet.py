import urllib.request, ssl, socket, time
res=[]
for url in ["https://speech.platform.bing.com/","https://pypi.org/simple/"]:
    t=time.time()
    try:
        r=urllib.request.urlopen(url, timeout=10)
        res.append(f"{url} OK {r.status} {time.time()-t:.1f}s")
    except Exception as e:
        res.append(f"{url} ERR {type(e).__name__}: {e} ({time.time()-t:.1f}s)")
res.append("proxy env: " + str({k:v for k,v in __import__("os").environ.items() if "PROXY" in k.upper()}))
open(r"E:\vscode\zhouji\webHome\_video\_logs\_pynet.txt","w",encoding="utf-8").write("\n".join(res))
