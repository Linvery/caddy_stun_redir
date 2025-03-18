import re
import os
import requests

# 获取当前脚本所在目录
current_work_dir = os.path.dirname(__file__)
def update_caddyfile(new_url):
    # 读取Caddy文件内容
    with open(f'{current_work_dir}/Caddyfile', 'r') as f:
        content = f.read()
    
    # 使用正则表达式匹配旧IP并替换为新IP
    # 注意转义特殊字符，并保留{uri}部分
    pattern = r'\{replace_url\}'
    replacement = f'{new_url}'
    new_content = re.sub(pattern, replacement, content)
    print(new_content)
    
    # 将修改后的内容写回文件
    with open(f'{current_work_dir}/Caddyfile', 'w') as f:
        f.write(new_content)

if __name__ == '__main__':
    # 先获取301跳转前的地址
    r = requests.get('https://nas-link.nodsec.com/',allow_redirects=False)
    new_url = r.headers['Location'].split('/')[2]
    update_caddyfile(new_url)
    r = requests.post(url='http://127.0.0.1:9707/load',headers={'Content-Type':'text/caddyfile'},data=open('/root/caddy_plugin/Caddyfile','rb').read())
    print(r.text)
    print("Caddyfile 已更新！")