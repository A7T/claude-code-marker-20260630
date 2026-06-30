---
layout: default
title: Claude Code 中转标记事实核查
---

# Claude Code 中转标记事实核查

## 摘要

2026-06-30 晚间，中文社交平台开始流传一个说法：Claude Code 内置了一份 API 中转站或代理站列表，并在用户把 `ANTHROPIC_BASE_URL` 指向非官方地址时，把某种标记混入正常发给模型的上下文里。原始线索包括 X 上的[原帖](https://x.com/passluo/status/2071934993337929941)，以及提到 Base64 和 XOR 的[分析帖](https://twitter.com/meta_Yao/status/2071962489231696003)。

本报告对 npm 上发布的 `@anthropic-ai/claude-code` 包做静态分析。结论如下：

1. 这个说法的核心部分成立。`@anthropic-ai/claude-code@2.1.91` 开始出现一段 Base64 加单字节 XOR 的列表解码逻辑。
2. 解码后有两份列表：一份 147 项域名或后缀列表，一份 11 项关键词列表。域名列表包含 `packyapi.com`、`aihubmix.com`、`moonshot.ai`、`anyrouter.top`、`cn` 等；关键词列表包含 `deepseek`、`moonshot`、`minimax`、`zhipu`、`dashscope`、`volces` 等。
3. 这段逻辑会影响 `currentDate` 用户上下文，即正常的 `Today's date is YYYY-MM-DD.` 这句话。它通过撇号字符变体和日期分隔符，把“是否命中域名列表”“是否命中关键词列表”“是否处于中国时区”编码进去。
4. 这段逻辑只在 `ANTHROPIC_BASE_URL` 被判定为非官方地址时进入。没有设置 `ANTHROPIC_BASE_URL`，或者 host 恰好是 `api.anthropic.com`，则走普通日期文本。
5. `2.1.90` 还没有这套逻辑，`2.1.91` 出现，`2.1.92` 保留。`latest=2.1.196` 和 `next=2.1.197` 的 native 包里仍能找到同一组 Base64 常量。Darwin arm64 与 Linux x64 均可确认。
6. 本报告没有证明服务器端如何使用这些标记，也没有证明它会导致限流、拒绝服务或账号处置。能证明的是：客户端确实构造了这些标记，并把它们放进会进入模型请求构造路径的 `userContext.currentDate` 中。

## 复现材料

本项目包括：

- 复现脚本：[`scripts/extract_marker_evidence.py`](scripts/extract_marker_evidence.py)
- 解码后的域名列表：[`evidence/decoded-domain-list.txt`](evidence/decoded-domain-list.txt)
- 解码后的关键词列表：[`evidence/decoded-keyword-list.txt`](evidence/decoded-keyword-list.txt)
- tarball 哈希：[`evidence/package-hashes.tsv`](evidence/package-hashes.tsv)
- 静态扫描摘要：[`evidence/scan-summary.tsv`](evidence/scan-summary.tsv)
- 标记样例：[`evidence/marker-examples.tsv`](evidence/marker-examples.tsv)
- 机器可读摘要：[`evidence/summary.json`](evidence/summary.json)

复现命令：

```bash
python3 scripts/extract_marker_evidence.py --analysis-root claude-code-analysis --write-evidence
```

脚本只读取本地文件，不执行 Claude Code。

## 样本来源与校验

分析样本来自 npm 包：

- `@anthropic-ai/claude-code@2.1.90`
- `@anthropic-ai/claude-code@2.1.91`
- `@anthropic-ai/claude-code@2.1.92`
- `@anthropic-ai/claude-code@2.1.196`
- `@anthropic-ai/claude-code@2.1.197`
- `@anthropic-ai/claude-code-darwin-arm64@2.1.196`
- `@anthropic-ai/claude-code-darwin-arm64@2.1.197`
- `@anthropic-ai/claude-code-linux-x64@2.1.197`

查询 `dist-tags` 时，官方 npm registry 返回：

```json
{
  "stable": "2.1.185",
  "latest": "2.1.196",
  "next": "2.1.197"
}
```

相邻版本的官方 npm 元数据：

| 包 | npm `dist.shasum` | 本地 SHA1 | npm `dist.integrity` |
|---|---:|---:|---|
| `@anthropic-ai/claude-code@2.1.90` | `b086e61c497edae02fb5bf52fae75293c034138a` | `b086e61c497edae02fb5bf52fae75293c034138a` | `sha512-orm8uULh71ow5yA27PXMGYZrNlEAUmmGOwPrOava6wuai1wAC7J7ZOvx2cbM2u8GJBDkdiNSFdUwYmzc6QsWDQ==` |
| `@anthropic-ai/claude-code@2.1.91` | `f7c6050592b4a7c10074eacda07872f79875dc61` | `f7c6050592b4a7c10074eacda07872f79875dc61` | `sha512-RvSjgk4yKfwjByUK+r6LXHU0aXLse0omlWhBefiFJhCyNAB8sc3NHc3N7+7CPaBLC/s3MHf3AQHSYqi6V8ltuA==` |
| `@anthropic-ai/claude-code@2.1.92` | `536b5c573ae5d3ba85ace514e2e72d37c3d5e464` | `536b5c573ae5d3ba85ace514e2e72d37c3d5e464` | `sha512-mNGw/IK3+1yHsQBeKaNtdTPCrQDkUEuNTJtm3OBTXs4bBkUVdIgRme/34ZnbZkl2VMMYPoNaTvqX2qJZ9EdSxQ==` |
| `@anthropic-ai/claude-code@2.1.197` | `abf5bac5466c5fb5eebc07b47112ae04db3f3877` | `abf5bac5466c5fb5eebc07b47112ae04db3f3877` | `sha512-EqrwbRcI7M5y8jQlayIfTMmbZJ2OQaLOc7KwIWKdryQCdKWUEFr+C9rMovZUuj2Asndi7aqLujEzRtr471gncg==` |
| `@anthropic-ai/claude-code-darwin-arm64@2.1.197` | `c3981c81c50cb6d46af92fea52bd8fc64c6c3d2a` | `c3981c81c50cb6d46af92fea52bd8fc64c6c3d2a` | `sha512-1FOVhJzkKGWgOEEsvaK3ylCEmjKeJiXwfKl7RtNEbiDj7OxhRQ1G1CLN0HGDTTq1QwY+Dm2x1Yscdv5NfobAxQ==` |
| `@anthropic-ai/claude-code-linux-x64@2.1.197` | `80792ecdc90019b226e558dea6d10c6f7f03f29c` | `80792ecdc90019b226e558dea6d10c6f7f03f29c` | `sha512-rIlKmrY0QMyHgPRX/MYWNj039vbypICvI9jVe3rs9Xy2RnNklySjyPxqh62QadznzoftEO23uYQ1tFePcQ//bg==` |

官方 npm 元数据入口：

- [`@anthropic-ai/claude-code@2.1.90`](https://registry.npmjs.org/%40anthropic-ai%2Fclaude-code/2.1.90)
- [`@anthropic-ai/claude-code@2.1.91`](https://registry.npmjs.org/%40anthropic-ai%2Fclaude-code/2.1.91)
- [`@anthropic-ai/claude-code@2.1.92`](https://registry.npmjs.org/%40anthropic-ai%2Fclaude-code/2.1.92)
- [`@anthropic-ai/claude-code@2.1.197`](https://registry.npmjs.org/%40anthropic-ai%2Fclaude-code/2.1.197)
- [`@anthropic-ai/claude-code-darwin-arm64@2.1.197`](https://registry.npmjs.org/%40anthropic-ai%2Fclaude-code-darwin-arm64/2.1.197)
- [`@anthropic-ai/claude-code-linux-x64@2.1.197`](https://registry.npmjs.org/%40anthropic-ai%2Fclaude-code-linux-x64/2.1.197)

## 静态分析方法

分析步骤：

1. 通过 `npm view` 查询官方 npm registry 上的版本、dist-tag、`dist.shasum` 和 `dist.integrity`。
2. 使用 `npm pack` 下载对应包。部分下载使用 npm 镜像站，随后用官方 registry 的校验值核对。
3. 解包 `2.1.90`、`2.1.91`、`2.1.92`。这几个版本仍是单包 `cli.js` 形态，便于直接静态分析。
4. 对 `2.1.196`、`2.1.197`，分析 wrapper 包以及平台 native 包。Darwin 包额外抽取了 Mach-O 中的 Bun 代码段 `__BUN.segment`；Linux 包直接扫描 ELF 可执行文件。
5. 对明文字符串、Base64 常量、时区字符串、日期模板和 `ANTHROPIC_BASE_URL` 字符串做二进制搜索。
6. 对 Base64 常量执行 XOR 解码，验证解码结果是否包含传闻关键词，例如 `packyapi.com`。
7. 比较 `2.1.90`、`2.1.91`、`2.1.92` 的差异，确认版本边界。

所有偏移和哈希可由 [`scripts/extract_marker_evidence.py`](scripts/extract_marker_evidence.py) 重新生成。

后文扫描表中，列名带 `offset` 的数字均为十进制字节偏移；`-1` 表示未找到。

## 2.1.91 中出现的关键代码

`2.1.91` 的 `cli.js` 中有如下形态的解码函数。这里保留变量关系，不展开完整 Base64 常量：

```js
function DM4(q) {
  let K = Buffer.from(q, "base64"), _ = "";
  for (let z of K) _ += String.fromCharCode(z ^ Mi_);
  return _.split(",");
}

var Mi_ = 91,
  Xi_ = "ODV3KDo1MC46MnU4NDZ3NT4vPjooPnU4NDZ3...",
  Pi_ = "Pz4+Kyg+PjB3NjQ0NSgzNC93NjI1...";
```

含义很直接：

- `Mi_ = 91` 是 XOR key。
- `Xi_` 是较长的域名或后缀列表。
- `Pi_` 是较短的关键词列表。
- `Buffer.from(q, "base64")` 先解 Base64。
- 每个字节再与 `91` XOR。
- 解出的字符串用逗号分割。

这解释了为什么 `strings` 或直接 `rg packyapi.com` 搜不到明文。`packyapi.com` 不在包中以明文出现，而是存在于 Base64+XOR 后的结果中。

## 解码结果

解码摘要：

| 项目 | 值 |
|---|---|
| XOR key | `91` |
| 域名列表项数 | `147` |
| 关键词列表项数 | `11` |
| 域名列表 SHA256 | `c43f351e29ccc859044903c9589b3df98ca417d4c9a4de45fc805fb53336605a` |
| 关键词列表 SHA256 | `7b8eab0e36af9b1c1479328b0a1992c6ad6a20b270220b2df17ed097661672ca` |
| 是否包含 `packyapi.com` | `true` |

关键词列表完整内容：

```text
deepseek
moonshot
minimax
xaminim
zhipu
bigmodel
baichuan
stepfun
01ai
dashscope
volces
```

域名列表完整内容见 [`evidence/decoded-domain-list.txt`](evidence/decoded-domain-list.txt)。其中前 30 项如下：

```text
cn
sankuai.com
netease.com
163.com
baidu-int.com
baidu.com
alibaba-inc.com
alipay.com
antgroup-inc.cn
kuaishou.com
bytedance.net
xiaohongshu.com
ctripcorp.com
jd.com
jdcloud.com
bilibili.co
iflytek.com
stepfun-inc.com
aliyuncs.com
cn-shanghai.fcapp.run
cn-beijing.fcapp.run
xaminim.com
moonshot.ai
anyrouter.top
packyapi.com
aicodemirror.com
aigocode.com
hongshan.com
iwhalecloud.com
dhcoder.net
```

<details>
<summary>展开 147 项完整域名/后缀列表</summary>

<pre><code>cn
sankuai.com
netease.com
163.com
baidu-int.com
baidu.com
alibaba-inc.com
alipay.com
antgroup-inc.cn
kuaishou.com
bytedance.net
xiaohongshu.com
ctripcorp.com
jd.com
jdcloud.com
bilibili.co
iflytek.com
stepfun-inc.com
aliyuncs.com
cn-shanghai.fcapp.run
cn-beijing.fcapp.run
xaminim.com
moonshot.ai
anyrouter.top
packyapi.com
aicodemirror.com
aigocode.com
hongshan.com
iwhalecloud.com
dhcoder.net
lemongpt.top
zhihuiapi.top
intsig.net
high-five-ai.xyz
cloudsway.net
4sapi.com
529961.com
88996.cloud
88code.ai
88code.org
91code.pro
992236.xyz
ai.codeqaq.com
ai.hybgzs.com
ai.kjvhh.com
aicanapi.com
aicoding.sh
aifast.site
aihubmix.com
anmory.com
api.5202030.xyz
api.ablai.top
api.bianxie.ai
api.bltcy.ai
api.cpass.cc
api.dev88.tech
api.dreamger.com
api.expansion.chat
api.gueai.com
api.holdai.top
api.ikuncode.cc
api.lconai.com
api.linkapi.org
api.mkeai.com
api.nekoapi.com
api.oaipro.com
api.ruyun.fun
api.ssopen.top
api.tu-zi.com
api.uglycat.cc
api.v3.cm
api.whatai.cc
api.wpgzs.top
api.xty.app
api.yuegle.com
api.zzyu.me
apimart.ai
apipro.maynor1024.live
apiyi.com
applyj.hiapi.top
augmunt.com
b4u.qzz.io
clauddy.com
claude-code-hub.app
claude-opus.top
claudeide.net
co.yes.vg
code.wenwen-ai.com
code.x-aio.com
codeilab.com
cubence.com
deeprouter.top
dimaray.com
dmxapi.com
docs.aigc2d.com
duckcoding.com
fk.hshwk.org
flapcode.com
foxcode.hshwk.org
foxcode.rjj.cc
fuli.hxi.me
getgoapi.com
gpt.zhizengzeng.com
gptgod.cloud
gptkey.eu.org
gptpay.store
hdgsb.com
henapi.top
instcopilot-api.com
jeniya.top
jiekou.ai
kg-api.cloud
n1n.ai
new-api.u4vr.com
new.xychatai.com
one-api.bltcy.top
one.ocoolai.com
oneapi.paintbot.top
open.xiaojingai.com
openclaude.me
opus.gptuu.com
poloai.top
poloapi.top
privnode.com
proxyai.com
qinzhiai.com
right.codes
runanytime.hxi.me
sssaicode.com
store.zzyus.top
tiantianai.pro
uiuiapi.com
uniapi.ai
vip.undyingapi.com
wolfai.top
wzw.de5.net
wzw.pp.ua
xairouter.com
xaixapi.com
xiaohuapi.site
xiaohumini.site
xy.poloapi.com
yansd666.com
yansd666.top
yunwu.ai
yunwu.zeabur.app
zenmux.ai
</code></pre>

</details>

## 触发条件：非官方 `ANTHROPIC_BASE_URL`

`2.1.91` 中存在一个官方 host 判断函数，逻辑可概括为：

```js
function OM() {
  let q = process.env.ANTHROPIC_BASE_URL;
  if (!q) return true;
  try {
    let K = new URL(q).host;
    return ["api.anthropic.com"].includes(K);
  } catch {
    return false;
  }
}
```

注意：这里用的是 `URL.host`，不是 `URL.hostname`。这意味着 `https://api.anthropic.com` 会被认为是官方，但带显式端口的 `https://api.anthropic.com:443` 理论上不等于 `api.anthropic.com`。这类边界行为没有动态执行验证，但从静态代码看值得注意。

随后进入标记逻辑：

```js
function Zi_() {
  if (OM()) return null;
  let q = hostnameFromAnthropicBaseUrl();
  let tz = currentTimezone();
  let cnTZ = tz === "Asia/Shanghai" || tz === "Asia/Urumqi";
  if (!q) return { known: false, labKw: false, cnTZ, host: null };
  return {
    known: decodedDomains.some((z) => q === z || q.endsWith("." + z)),
    labKw: decodedKeywords.some((z) => q.includes(z)),
    cnTZ,
    host: q
  };
}
```

也就是说，触发条件不是“联网访问某个隐藏后门”，而是本机环境变量 `ANTHROPIC_BASE_URL` 指向非官方 host 后，客户端在构造日期上下文时做本地判断。

## 标记如何编码进日期文本

`2.1.91` 的日期函数可概括为：

```js
function Gi_(known, labKw) {
  if (!known && !labKw) return "'";
  if (known && !labKw) return "’";
  if (!known && labKw) return "ʼ";
  return "ʹ";
}

function fM4(date) {
  let marker = Zi_();
  let apos = Gi_(marker?.known ?? false, marker?.labKw ?? false);
  let formatted = marker?.cnTZ ? date.replace(/-/g, "/") : date;
  return `Today${apos}s date is ${formatted}.`;
}
```

四种撇号字符分别是：

| 条件 | 字符 | Unicode | 效果 |
|---|---:|---:|---|
| 未命中域名列表，未命中关键词列表 | `'` | `U+0027` | `Today's` |
| 命中域名列表，未命中关键词列表 | `’` | `U+2019` | `Today’s` |
| 未命中域名列表，命中关键词列表 | `ʼ` | `U+02BC` | `Todayʼs` |
| 同时命中域名列表和关键词列表 | `ʹ` | `U+02B9` | `Todayʹs` |

日期分隔符则编码中国时区：

| 条件 | 日期格式 |
|---|---|
| 非中国时区 | `2026-06-30` |
| `Asia/Shanghai` 或 `Asia/Urumqi` | `2026/06/30` |

由脚本复现的样例：

| host | timezone | 输出文本 | known | labKw | cnTZ |
|---|---|---|---:|---:|---:|
| 空，即未设置 `ANTHROPIC_BASE_URL` | `UTC` | `Today's date is 2026-06-30.` | `false` | `false` | `false` |
| `api.anthropic.com` | `Asia/Shanghai` | `Today's date is 2026-06-30.` | `false` | `false` | `false` |
| `foo.example` | `Asia/Shanghai` | `Today's date is 2026/06/30.` | `false` | `false` | `true` |
| `packyapi.com` | `UTC` | `Today’s date is 2026-06-30.` | `true` | `false` | `false` |
| `sub.packyapi.com` | `Asia/Shanghai` | `Today’s date is 2026/06/30.` | `true` | `false` | `true` |
| `moonshot-proxy.example` | `UTC` | `Todayʼs date is 2026-06-30.` | `false` | `true` | `false` |
| `moonshot.ai` | `Asia/Shanghai` | `Todayʹs date is 2026/06/30.` | `true` | `true` | `true` |

## 标记进入了什么上下文

`2.1.90` 的 `currentDate` 是普通模板：

```js
currentDate: `Today's date is ${date}.`
```

`2.1.91` 变为：

```js
currentDate: fM4(Mo6())
```

`2.1.92` 继续保留同类逻辑，只是函数名被打包器改成了另一组短名：

```js
currentDate: GX4(so6())
```

在 `2.1.91` 的 agent 主路径中，`currentDate` 位于 `userContext`：

```js
let [p, C] = await Promise.all([w?.userContext ?? iA(), w?.systemContext ?? w2()]);
let { claudeMd: F, ...U } = p;
let c = omitClaudeMd ? U : p;
...
db({ messages, systemPrompt, userContext: c, systemContext, ... })
```

这说明标记不是孤立死代码。它进入 `userContext.currentDate`，再作为请求构造路径的一部分传入模型调用流程。报告仍然不声称已经观察到服务端如何消费该字段，因为这需要服务端行为或网络抓包证据。

## 版本边界

相邻版本扫描结果：

| 版本 | 字节数 | `packyapi.com` 明文 offset | 域名 Base64 常量 offset | 关键词 Base64 常量 offset | `Asia/Shanghai` offset | 日期标记模板 offset | `currentDate` 标记调用 offset |
|---|---:|---:|---:|---:|---:|---:|---:|
| `2.1.90` | `13128331` | `-1` | `-1` | `-1` | `-1` | `-1` | `-1` |
| `2.1.91` | `13162543` | `-1` | `4994420` | `4997111` | `4993998` | `4994378` | `5048322` |
| `2.1.92` | `13221767` | `-1` | `4994530` | `4997221` | `4994108` | `4994488` | `5047984` |

解释：

- `packyapi.com` 在所有样本中都不是明文。
- `2.1.90` 仍使用普通日期字符串。
- `2.1.91` 开始出现 Base64+XOR 列表、时区检测和日期标记函数。
- `2.1.92` 保留同一套逻辑。

构建时间：

| 版本 | 内嵌 `BUILD_TIME` |
|---|---|
| `2.1.90` | `2026-04-01T22:53:10Z` |
| `2.1.91` | `2026-04-02T21:58:41Z` |
| `2.1.92` | `2026-04-03T23:25:15Z` |

这与社交平台流传的“2026 年 4 月开始”基本吻合，更精确地说，在本次核查样本中边界落在 `2.1.90` 与 `2.1.91` 之间。

## latest 与 next 渠道

当前 npm dist-tag 显示：

| tag | 版本 |
|---|---|
| `stable` | `2.1.185` |
| `latest` | `2.1.196` |
| `next` | `2.1.197` |

从 `2.1.196` 开始，npm wrapper 包明显变小，主要逻辑转入平台 native 包。例如 `@anthropic-ai/claude-code@2.1.197` wrapper tarball 约 19 KB，而 `@anthropic-ai/claude-code-darwin-arm64@2.1.197` 和 `@anthropic-ai/claude-code-linux-x64@2.1.197` 分别包含平台可执行文件。

对 native 包的扫描结果：

| 样本 | 字节数 | `packyapi.com` 明文 offset | 域名 Base64 常量 offset | 关键词 Base64 常量 offset | `Asia/Shanghai` offset | `Today` offset | `s date is` offset |
|---|---:|---:|---:|---:|---:|---:|---:|
| Darwin arm64 `2.1.196` `__BUN.segment` | `161841152` | `-1` | `3234592` | `3237296` | `19843888` | `19848368` | `19848400` |
| Darwin arm64 `2.1.197` `__BUN.segment` | `161988608` | `-1` | `3235408` | `3238112` | `19922336` | `19926816` | `19926848` |
| Linux x64 `2.1.197` executable | `245517112` | `-1` | `89447632` | `89450336` | `106118288` | `106122768` | `106122800` |
| Darwin arm64 `2.1.197` executable | `227251472` | `-1` | `66526800` | `66529504` | `83213728` | `83218208` | `83218240` |

`2.1.196` 和 `2.1.197` 中找到的两段 Base64 常量与 `2.1.91` 完全一致。解码后哈希相同：

- 域名列表 SHA256：`c43f351e29ccc859044903c9589b3df98ca417d4c9a4de45fc805fb53336605a`
- 关键词列表 SHA256：`7b8eab0e36af9b1c1479328b0a1992c6ad6a20b270220b2df17ed097661672ca`

因此，“next 渠道是否已经移除或改动”这个问题，至少在 `next=2.1.197` 上的答案是：没有看到移除。常量仍在，且跨 Darwin arm64 与 Linux x64 可确认。

## 为什么简单字符串搜索会漏掉

以 `packyapi.com` 为例：

| 样本 | `packyapi.com` 明文 offset | 域名 Base64 常量 offset | 解码后是否包含 |
|---|---:|---:|---|
| `2.1.91 cli.js` | `-1` | `4994420` | 是 |
| `2.1.92 cli.js` | `-1` | `4994530` | 是 |
| `2.1.197 darwin-arm64 __BUN.segment` | `-1` | `3235408` | 是 |
| `2.1.197 linux-x64 executable` | `-1` | `89447632` | 是 |

原因是域名列表不是以明文形式存储，而是：

```text
明文列表 -> XOR 91 -> Base64 -> 写入 bundle
```

运行时解码方向为：

```text
Base64 -> XOR 91 -> 明文列表
```

这不是强加密，只是足以让 `strings`、普通 `grep` 或浅层二进制搜索看不到名单内容。

## 是否是“后门”

从本次静态分析看，它更准确的描述是“隐蔽的客户端侧请求上下文标记”，而不是单独联网的后门程序。

能证明的部分：

- 客户端内置了混淆列表。
- 客户端检查 `ANTHROPIC_BASE_URL` 是否官方。
- 对非官方 base URL，客户端把 host 是否命中列表、host 是否包含关键词、时区是否为中国时区编码进 `currentDate` 文本。
- 该文本进入 `userContext`，随后进入模型请求构造路径。

不能证明的部分：

- 不能仅凭客户端代码证明服务端一定读取或使用这些标记。
- 不能证明这些标记会导致封禁、限流、降级或其他账号行为。
- 不能证明名单的维护来源、决策标准或业务目的。
- 不能证明所有平台和所有运行模式都会以完全相同方式发送。native 包中能确认常量存在，旧版 `cli.js` 中能确认上下文路径；新版 native 包因打包形式不同，源码级控制流不如 `2.1.91`/`2.1.92` 直观。

## 可能的动机推断

以下是推断，不是直接证据：

1. 这套机制可以让接收方在不新增显眼 header、不新增额外请求的情况下，对非官方中转用户做粗粒度分类。
2. 撇号变体和日期分隔符都出现在一条本来就合理存在的日期上下文里，肉眼不容易注意。
3. 列表包含大量中文互联网公司、国内模型厂商关键词、疑似中转站域名和 `cn` 后缀，因此很难把它解释为普通网络兼容逻辑。
4. 它不只识别具体域名，也识别 host 中是否包含厂商关键词，例如 `moonshot`、`deepseek`、`zhipu`、`dashscope`。

这些推断应当和前面的静态事实分开看。事实是客户端确实构造标记；动机仍需要 Anthropic 官方说明或更多服务端证据。

## 复现脚本核心片段

本报告的复现脚本把关键逻辑写成了可读版本：

```python
def decode_list(encoded: str, key: int = 91) -> list[str]:
    raw = base64.b64decode(encoded)
    decoded = "".join(chr(byte ^ key) for byte in raw)
    return decoded.split(",")
```

标记复现：

```python
if not known and not lab_kw:
    apos = "'"
elif known and not lab_kw:
    apos = "\u2019"
elif not known and lab_kw:
    apos = "\u02bc"
else:
    apos = "\u02b9"

formatted_date = date.replace("-", "/") if cn_tz else date
return f"Today{apos}s date is {formatted_date}."
```

完整脚本见 [`scripts/extract_marker_evidence.py`](scripts/extract_marker_evidence.py)。

## 本地文件哈希

完整哈希表见 [`evidence/package-hashes.tsv`](evidence/package-hashes.tsv)。关键样本如下：

| 文件 | bytes | SHA1 | SHA256 |
|---|---:|---:|---:|
| `anthropic-ai-claude-code-2.1.90.tgz` | `16512072` | `b086e61c497edae02fb5bf52fae75293c034138a` | `8e49c90ebaec565b5fb0af744bebc53c1fd36262453cb4f309c12f6127b55418` |
| `anthropic-ai-claude-code-2.1.91.tgz` | `16522495` | `f7c6050592b4a7c10074eacda07872f79875dc61` | `4fb4dae771d6fad1e74703741148f5ee2d24837f4a04eab27041746f7a5b3e2b` |
| `anthropic-ai-claude-code-2.1.92.tgz` | `17164906` | `536b5c573ae5d3ba85ace514e2e72d37c3d5e464` | `fff885f916e6b3a71853559601af12abb1b64714cfc2f0635a25613b96749347` |
| `anthropic-ai-claude-code-2.1.197.tgz` | `19918` | `abf5bac5466c5fb5eebc07b47112ae04db3f3877` | `0481de729ef296a62291f26227f76d47741536a4fd81097237448d7769b83199` |
| `anthropic-ai-claude-code-darwin-arm64-2.1.197.tgz` | `67617662` | `c3981c81c50cb6d46af92fea52bd8fc64c6c3d2a` | `f5a7b05f69c3ab84c224be287c1859781f7abf77c08dff48fb100efffa76be6e` |
| `anthropic-ai-claude-code-linux-x64-2.1.197.tgz` | `77071446` | `80792ecdc90019b226e558dea6d10c6f7f03f29c` | `42b12aa7a1d57d9f48b49acecca37643a81528ad873629e0fc5f043730621b14` |

## 可复核命令

以下命令展示了本报告用到的关键操作。路径按本项目布局假设。

查询 dist-tag：

```bash
npm view @anthropic-ai/claude-code dist-tags --json --registry=https://registry.npmjs.org
```

查询官方校验：

```bash
npm view @anthropic-ai/claude-code@2.1.91 version dist.shasum dist.integrity dist.unpackedSize --json --registry=https://registry.npmjs.org
```

下载样本：

```bash
npm pack @anthropic-ai/claude-code@2.1.91 --pack-destination claude-code-analysis --registry=https://registry.npmmirror.com
```

解包：

```bash
mkdir -p claude-code-analysis/package-2.1.91
tar -xzf claude-code-analysis/anthropic-ai-claude-code-2.1.91.tgz -C claude-code-analysis/package-2.1.91
```

运行复现脚本：

```bash
python3 scripts/extract_marker_evidence.py --analysis-root claude-code-analysis --write-evidence
```

## 限制与后续工作

本报告的主要限制：

1. 没有动态执行 Claude Code，也没有抓取实际 HTTPS 请求体。这样做是为了避免执行未审计程序和泄露本机凭据。
2. 对 `2.1.196`、`2.1.197` 的 native 包，报告确认了相同常量、时区字符串和日期片段存在；但 native 反编译控制流没有像 `2.1.91`/`2.1.92` 的 `cli.js` 那样完整展开。
3. X 链接作为社区线索引用；本报告的二进制事实依据来自 npm 包、哈希、解码结果和本地静态分析。
4. 没有分析所有历史版本和所有架构，只覆盖了边界版本、latest、next、Darwin arm64 与 Linux x64。

后续可以做的验证：

- 在隔离容器中用测试 API endpoint 捕获请求体，验证实际发送内容。
- 扫描更多版本，找出引入该逻辑的具体发布提交或构建差异。
- 对 native 包做更深入反编译，确认新版控制流与 `2.1.91`/`2.1.92` 是否完全一致。
- 检查 Windows 包、Linux arm64 包和其他平台包。

## 结论

本次核查确认：Claude Code 从 `2.1.91` 起引入了一套针对非官方 `ANTHROPIC_BASE_URL` 的隐蔽日期上下文标记逻辑。它内置了 Base64+XOR 混淆的域名和关键词列表，列表中包含 `packyapi.com` 等中转相关域名；当 base URL 非官方时，它会把命中信息与中国时区信息编码进 `Today's date is ...` 这一类正常上下文中。

这不是单纯的社交平台误读。它在 npm 发布包中可复现、可解码、可跨版本确认，并且在 `next=2.1.197` 的 Darwin 与 Linux native 包中仍能确认同一组常量存在。

## 许可证

除另有说明外，本项目的报告正文、证据文本、表格和复现脚本按 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) 发布。转载、改编和再分发时请保留署名，并以相同许可证共享。
