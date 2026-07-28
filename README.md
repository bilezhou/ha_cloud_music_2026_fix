# 云音乐

> 本仓库是针对 Home Assistant Core 2026.2+ 的兼容修复版本。
> 修复了组件路径依赖进程工作目录导致配置流无法加载，以及登录 Cookie
> 写入错误目录、重启后需要重新登录的问题。原项目版权归原作者所有。

在Home Assistant里使用的网易云音乐插件

[![hacs_badge](https://img.shields.io/badge/Home-Assistant-%23049cdb)](https://www.home-assistant.io/)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
![visit](https://visitor-badge.laobi.icu/badge?page_id=shaonianzhentan.ha_cloud_music&left_text=visit)

---
## 历史旧版本项目，请点击链接访问安装
https://github.com/shaonianzhentan/cloud_music

---

## 安装

安装完成重启HA，刷新一下页面，在集成里搜索`云音乐`

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=ha_cloud_music)

> 接口说明

接口服务是开源免费的，但需要自己进行部署，然后持续进行更新升级，如果遇到接口相关的问题，请去`NeteaseCloudMusicApi`项目中查找问题

https://github.com/Binaryify/NeteaseCloudMusicApi

不想动手不想操心，也可以付费使用由我部署维护的接口服务（每年30）

**注意：关联媒体播放器调整为在集成选项中选择**

## 使用 - [插件图片预览](https://github.com/shaonianzhentan/image/blob/main/ha_cloud_music/README.md)

> **指定ID播放**

- 播放网易云音乐歌单 `cloudmusic://163/playlist?id=25724904`
- 播放网易云音乐电台 `cloudmusic://163/radio/playlist?id=1008`
- 播放网易云音乐歌手 `cloudmusic://163/artist/playlist?id=2116`
- 播放喜马拉雅专辑 `cloudmusic://xmly/playlist?id=258244`

> **搜索播放**

- [x] 音乐搜索播放 `cloudmusic://play/song?kv=关键词`
- [x] 歌手搜索播放 `cloudmusic://play/singer?kv=关键词`
- [x] 歌单搜索播放 `cloudmusic://play/list?kv=关键词`
- [x] 电台搜索播放 `cloudmusic://play/radio?kv=关键词`
- [x] 喜马拉雅搜索播放 `cloudmusic://play/xmly?kv=关键词`
- [ ] FM搜索播放 `cloudmusic://play/fm?kv=关键词`
- [x] （不推荐）第三方音乐搜索播放 `cloudmusic://search/play?kv=关键词`

> **登录后播放**
- [x] 每日推荐 `cloudmusic://163/my/daily`
- [x] 我喜欢的音乐 `cloudmusic://163/my/ilike`

## 关联项目

- https://github.com/shaonianzhentan/cloud_music_mpd
- https://github.com/shaonianzhentan/ha_windows

## 如果这个项目对你有帮助，请我喝杯<del style="font-size: 14px;">咖啡</del>奶茶吧😘
|支付宝|微信|
|---|---|
<img src="https://ha.jiluxinqing.com/img/alipay.png" align="left" height="160" width="160" alt="支付宝" title="支付宝">  |  <img src="https://ha.jiluxinqing.com/img/wechat.png" align="left" height="160" width="160" alt="微信支付" title="微信">

#### 关注我的微信订阅号，了解更多HomeAssistant相关知识
<img src="https://ha.jiluxinqing.com/img/wechat-channel.png" height="160" alt="HomeAssistant家庭助理" title="HomeAssistant家庭助理">

