# 视频桌面小窗

基于 Electron：启动后显示**始终置顶**的 100×100 视频悬浮窗（不占任务栏），循环播放 `ui/assets` 下视频；**点击视频区域**可打开主页面窗口，二者可同时存在。

## 功能

- **悬浮窗**：100×100 像素、始终置顶、不显示在任务栏；点击任意位置打开主页面
- **主页面**：独立窗口（400×300），简单说明页，带系统标题栏与关闭按钮；关闭后悬浮窗仍显示
- **视频**：从 `ui/assets` 读取，按分辨率去重后循环播放；双缓冲预加载，单视频 seek 重播，无闪烁
- **外观**：圆角、无边框、无滚动条；Windows 下通过 SetWindowRgn 裁剪窗口形状

## 环境与运行

- Node.js 16+
- 视频格式：`.mp4`、`.webm`、`.ogg`、`.mov`

```bash
cd ui
npm install
npm start
```

## 目录结构

```
ui/
├── assets/        # 视频文件
├── main.js        # 主进程：悬浮窗 + 主窗口、IPC open-main
├── preload.js     # 预加载：onVideoPaths、openMain
├── index.html     # 悬浮窗页面
├── main.html      # 主页面内容
├── renderer.js    # 渲染进程：播放逻辑 + 点击打开主窗口
├── package.json
└── README.md
```

## 技术要点

- **主进程**：`pathToFileURL` 生成 file URL，`webSecurity: false` 允许本地视频加载；Windows 下用 koffi 调用 SetWindowRgn 实现圆角无边框
- **播放逻辑**：先扫一遍目录内视频，用 `loadedmetadata` 取分辨率并去重得到播放列表；多段用双 `<video>` 交替预加载与切换，单段用同一元素 seek 到 0 再播
- **首帧防闪**：`.video-scaler` 默认 `opacity: 0`，首个视频 `canplay` 时加 `.ready` 显示
