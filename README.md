# 飞牛影视+STUN+302跳转IP双栈解决方案

## 一、概要前提

### 1、环境：

* 硬件设备：家庭部署飞牛NAS系统（无公网IPv4，具备IPv6地址）
* 软件服务：运行MoviePilot+飞牛影视套件
* 客户端限制：终端设备仅支持IPv4网络

### 2. 核心痛点

- 传统IPv4中继ipv6方案存在带宽瓶颈（受限于VPS小水管）
- 无法实现全平台（PC/移动/TV）无感直连体验

### 3. 需求：

如何在客户端无v6的环境下，利用STUN打洞直连服务端，实现类似alist 302云盘的方案，同时支持PC/移动/TV客户端的无感stun访问。

### 4. 前置准备：

* 域名：`nas.com`（需托管至Cloudflare）
* 云服务器：腾讯/阿里云ECS（1核1G/200M带宽）
* 网络工具：Caddy Server + 自定义Python脚本

## 二、技术方案

```
A[客户端] -->|STUN请求| B(Cloudflare Worker)
    B -->|返回STUN IPV4:PORT | A
    A -->|媒体流直连| C[NAS STUN地址]
    A -->|API/静态资源| D[VPS中转]
```

## 三、部署教程

### 1. 部署cf worker实现stun地址302跳转

   参考链接：https://club.fnnas.com/forum.php?mod=viewthread&tid=6545

   效果：假设当前stun得到161.2.3.4:47125，域名为stun.nas.com，当访问https://stun.nas.com跳转到http://161.2.3.4:47125

   替代方案：内链通开源版 https://github.com/Linvery/lanjmp/tree/main
### 2. VPS上部署caddystun.py脚本实现仅媒体流路径302跳转

   在cloudflare上添加一个解析，stun.nas.com A记录到VPS IP

   首先VPS上部署一个Caddy，安装参考：[https://caddyserver.com/docs/install#debian-ubuntu-raspbian](https://caddy2.dengxiaolong.com/docs/install)

   在/etc/caddy/Caddyfile中最前面添加代码块，开启Caddy API：

   ```
   {
     admin 127.0.0.1:9707
   }

   ```

   然后执行systemctl restart caddy

   接着git拉取本项目

   ```
   git clone https://github.com/Linvery/caddy_stun_redir
   ```

   记得更换caddystun.py内变量fntv_domain和stun_domain

   ```
   fntv_domain = "http://fntv.nas.com:5666"
   stun_domain = "https://stun.nas.com"
   ```

   添加定时任务，每隔60秒更新一次

   ```
   sudo crontab -e
   # 在最末行添加下面配置，每隔60秒更新一次
   # 注意修改/path/to/路径
   */1 * * * * /usr/bin/python3 /path/to/caddystun.py >/dev/null 2>&1
   # 重启加载服务
   sudo systemctl restart cron
   ```

   也可以手动执行一次python3 caddystun.py，通过curl 查看是否存在302跳转

  ```
  root@VM-20-12-ubuntu:~/caddy_plugin# curl http://fntv.nas.com:5666/v/media/123 -v -4
  * Host fntv.nas.com:5666 was resolved.
  * IPv6: (none)
  * IPv4: x.x.x.x
  *   Trying x.x.x.x:5666...
  * Connected to fntv.nas.com (x.x.x.x) port 5666
  > GET /v/media/123 HTTP/1.1
  > Host: fntv.nas.com:5666
  > User-Agent: curl/8.5.0
  > Accept: */*
  > 
  < HTTP/1.1 302 Found
  < Location: http://x.x.x.x:16884/v/media/123
  < Server: Caddy
  < Date: Tue, 18 Mar 2025 19:29:38 GMT
  < Content-Length: 0
  < 
  * Connection #0 to host fntv.liangsec.com left intact
  
  ```

## 四、效果验证以及技术分析

### 1. 客户端访问地址：`http://fntv.nas.com:5666`
### 2. 流量：

   * API请求：通过VPS中转（181.2.3.4）
   * 媒体流（/v/media/\*）：302重定向直连NAS STUN IPv4
### 3. 带宽：

   ```
   [API流量] VPS反向代理
   [媒体流量] STUN直连（节省VPS带宽）
   ```

### 4、技术分析：
   仓库里有两个文件，caddystun.py负责通过request获取第一步stun.nas.com 302跳转的stun ip:port，然后在动态修改CaddyFile配置，实现分流，截取示例如下：

  ```
  http://fntv.nas.com:5666 {
  	reverse_proxy {replace_url}
  	handle /v/media/* {
  		redir http://{replace_url}{uri} 302
  	}
  }
  ```
  
  清楚看到，前端静态文件以及API接口等全部通过reverse_proxy反代，飞牛影视移动/TV客户端正常鉴权登录。在ts流的uri中使用redir实现媒体流302跳转到stun地址，不走中转服务器。
