import re
import os
import requests

# 配置飞牛TV的域名
fntv_domain = "http://fntv.nas.com:5666"
stun_domain = "https://stun.nas.com"

# 获取当前脚本所在目录
current_work_dir = os.path.dirname(__file__)
def update_caddyfile(new_url):
    # 读取Caddy文件内容
    with open(f'{current_work_dir}/Caddyfile', 'r') as f:
        content = f.read()
        # 使用正则表达式匹配出需要替换的内容
        new_content = content.replace('{replace_url}',new_url).replace('{fntv_domain}',fntv_domain)
        print(new_content)
    
    # 将修改后的内容写回文件
    with open(f'{current_work_dir}/CaddyfileNew', 'w') as f:
        f.write(new_content)

if __name__ == '__main__':
    
    # 先获取301跳转前的地址
    r = requests.get(stun_domain,allow_redirects=False)
    new_url = r.headers['Location'].split('/')[2]
    update_caddyfile(new_url)
    r = requests.post(url='http://127.0.0.1:9707/load',headers={'Content-Type':'text/caddyfile'},data=open(f'{current_work_dir}/CaddyfileNew','rb').read())
    print(r.text)
    print("Caddyfile 已更新！")