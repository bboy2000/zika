# -*- coding: utf-8 -*-
"""
微信云开发云存储批量上传——P4 笔顺数据版（改造自 upload_audio_wx.py）
源: E:/tmp/p4/strokes/<字>.json -> 云: strokes/<字>.json
用法:
  WX_APPID=xx WX_SECRET=xx WX_ENV=xx python tools/upload_strokes_wx.py [--limit N]
"""
import json, os, sys, time, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request

SRC = r'E:/tmp/p4/strokes'
OUT = r'E:/tmp/p4/fileid_map.json'   # 断点续传记录（发布不需要，fileID 运行时拼接）

APPID = os.environ.get('WX_APPID', '')
SECRET = os.environ.get('WX_SECRET', '')
ENV = os.environ.get('WX_ENV', '')
LIMIT = None
if '--limit' in sys.argv:
    LIMIT = int(sys.argv[sys.argv.index('--limit') + 1])

def log(msg):
    print(time.strftime('%H:%M:%S ') + msg, flush=True)

def http_json(url, data=None, timeout=30):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 method='POST' if data is not None else 'GET')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def get_token():
    u = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}'
    r = http_json(u)
    if 'access_token' not in r:
        raise RuntimeError(f'获取 token 失败: {r}')
    return r['access_token']

def cos_upload(token, local_path, cloud_path):
    r = http_json(f'https://api.weixin.qq.com/tcb/uploadfile?access_token={token}',
                  {'env': ENV, 'path': cloud_path})
    if r.get('errcode', 0) != 0:
        raise RuntimeError(f'uploadfile 失败: {r}')
    cred = r
    boundary = uuid.uuid4().hex
    body = b''
    for k, v in [('key', cloud_path), ('Signature', cred['authorization']),
                 ('x-cos-security-token', cred['token']),
                 ('x-cos-meta-fileid', cred['cos_file_id'])]:
        body += f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    with open(local_path, 'rb') as f:
        data = f.read()
    body += (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{os.path.basename(cloud_path)}"\r\n'
             f'Content-Type: application/json\r\n\r\n').encode() + data + f'\r\n--{boundary}--\r\n'.encode()
    req = urllib.request.Request(cred['url'], data=body, method='POST', headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(req, timeout=60) as r2:
        if r2.status not in (200, 204):
            raise RuntimeError(f'COS 上传 HTTP {r2.status}')

def main():
    chars = sorted(f for f in os.listdir(SRC) if f.endswith('.json'))
    done = set(json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else [])
    todo = [c for c in chars if c not in done]
    if LIMIT:
        todo = todo[:LIMIT]
    log(f'总 {len(chars)}  已完成 {len(done)}  待传 {len(todo)}')
    if not todo:
        log('无需上传')
        return
    token = get_token()
    log('token 获取成功')
    ok, fail = 0, []
    t0 = time.time()
    def worker(c):
        for attempt in range(3):
            try:
                cos_upload(token, os.path.join(SRC, c), 'strokes/' + c)
                return c
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(worker, c): c for c in todo}
        for fu in as_completed(futs):
            c = futs[fu]
            try:
                fu.result()
                done.add(c)
                ok += 1
            except Exception as e:
                fail.append((c, str(e)))
            if (ok + len(fail)) % 100 == 0:
                json.dump(sorted(done), open(OUT, 'w', encoding='utf-8'))
                rate = (ok + len(fail)) / max(time.time() - t0, 1)
                log(f'进度 {ok + len(fail)}/{len(todo)}  成功 {ok}  失败 {len(fail)}  速率 {rate:.1f}/s')
    json.dump(sorted(done), open(OUT, 'w', encoding='utf-8'))
    log(f'完成: 成功 {ok}  失败 {len(fail)}')
    for c, e in fail[:10]:
        log(f'FAIL {c}: {e}')

if __name__ == '__main__':
    main()
