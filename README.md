# OSS Thanks

![OSS Thanks hero](assets/oss-thanks-hero.png)

AI 编程工具越来越常去 GitHub 找项目、看代码、下载开源 skill。OSS Thanks 做一件很小的事：

**当 AI 参考或下载了一个 GitHub 开源项目，就按你的选择给它点一个 star。**

它不写感谢信，不打扰作者，也不生成一堆致谢文案。就是把“AI 用过开源项目”这件事，变成一个简单、可见的 star。

## 两种方式

第一次使用时，OSS Thanks 会直接问你想怎么运行，并记住选择。

| 方式 | 适合谁 | 会发生什么 |
| --- | --- | --- |
| 自动点 star | 想尽量省心的人 | AI 看到 GitHub 项目后，自动帮你点 star |
| 结束前确认 | 想自己看一眼的人 | 先记录下来，任务结束时让你决定哪些要 star |

之后不用每次再说一遍。想改时，再运行一次设置就行。

![OSS Thanks flow](assets/oss-thanks-flow.png)

## 怎么用

### 1. 添加到 Codex

```bash
codex plugin marketplace add qnianjinri-del/oss-thanks
```

然后在 Codex 的插件列表里安装 **OSS Thanks**，新开一个 thread。

### 2. 第一次它会直接问你

安装后，第一次有任务需要用到 OSS Thanks 时，Codex 会直接问：

```text
OSS Thanks 要怎么运行？
1) 自动点 star
2) 先问我
```

选过一次后，会保存在当前项目的 `.oss-thanks/config.json`。

如果你想手动改选择，也可以运行：

```bash
python3 scripts/oss_thanks.py setup
```

### 3. 让 AI 正常工作

之后你照常让 Codex 或 Claude Code 写代码、找参考项目、下载 skill。OSS Thanks 会从命令、链接和 hook 事件里识别 GitHub 仓库。

如果你选的是自动点 star，它会直接尝试点星。

如果你选的是结束前确认，可以查看当前列表：

```bash
python3 scripts/oss_thanks.py review
```

确认全部点星：

```bash
python3 scripts/oss_thanks.py review --star --yes
```

## GitHub 登录

自动点 star 需要能代表你的 GitHub 账号发起 star 操作。最简单的方式是安装并登录 GitHub CLI：

```bash
gh auth login
```

如果没有 `gh`，也可以设置 `GH_TOKEN` 或 `GITHUB_TOKEN`。

## 它会识别什么

这些都会被记录：

```text
https://github.com/openai/skills
git clone https://github.com/pallets/flask.git
git@github.com:psf/requests.git
gh repo clone pytest-dev/pytest
```

重复出现的项目只会保留一份记录。已经 star、忽略过的项目不会反复处理。

## 给 Claude Code 或其它工具用

核心功能是一个普通命令行脚本：

```bash
python3 scripts/oss_thanks.py record --text "git clone https://github.com/openai/skills.git"
```

所以不只 Codex 能用。任何 AI 编程工具只要能在任务过程中调用这个脚本，都可以接入。

## 抖音介绍图

项目里放了一张竖版介绍图，可以直接拿去发短视频封面或动态：

![OSS Thanks Douyin poster](assets/douyin-oss-thanks.png)

## 文件位置

- `plugins/oss-thanks`：Codex 插件包
- `.agents/plugins/marketplace.json`：Codex marketplace 入口
- `scripts/oss_thanks.py`：核心脚本
- `assets/`：README 图片和介绍图

## 说明

GitHub star 是用户账号的公开行为。OSS Thanks 会在第一次使用时让你选择运行方式，并把选择保存下来。自动点 star 适合明确愿意这样做的用户；如果你希望每次都看一眼，可以选择结束前确认。
