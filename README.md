# claude-code-marker-20260630

这是 Claude Code “中转标记”事实核查报告的源码仓库。主报告在 [`index.md`](index.md)，静态分析脚本在 [`scripts/extract_marker_evidence.py`](scripts/extract_marker_evidence.py)，已生成的证据输出在 [`evidence/`](evidence/)。

本仓库不提交 Claude Code 的 npm tarball、解包后的 `cli.js`、native 可执行文件或抽取出的 Bun 段。这些文件体积较大，也不适合作为第三方项目重新分发。复现时请把样本下载到仓库内的 [`claude-code-analysis/`](claude-code-analysis/) 目录；该目录只保留 `.gitkeep` 和 `.gitignore` 作为占位。

## 结论概览

复现脚本会验证这些事实：

- `@anthropic-ai/claude-code@2.1.90` 还没有日期标记逻辑。
- `@anthropic-ai/claude-code@2.1.91` 开始出现 Base64 + XOR 列表与 `currentDate` 标记逻辑。
- `@anthropic-ai/claude-code@2.1.92` 保留同类逻辑。
- `@anthropic-ai/claude-code@2.1.197` 的 Darwin arm64 与 Linux x64 native 包中仍能找到同一组 Base64 常量。
- 解码后的域名列表包含 `packyapi.com`，关键词列表包含 `deepseek`、`moonshot`、`minimax`、`zhipu`、`dashscope`、`volces` 等。

## 环境要求

需要：

- `git`
- `node` / `npm`
- `python3`
- `tar`

可选：

- macOS 上的 `otool` 和 `dd`：用于从 Darwin native 可执行文件中抽取 `__BUN.segment`。
- `shasum`：用于手动核对 tarball 哈希。

本项目只做静态分析，不执行 Claude Code。

## 克隆仓库

```bash
git clone https://github.com/A7T/claude-code-marker-20260630.git
cd claude-code-marker-20260630
```

如果只想看报告，不需要下载样本。若要复现分析，继续执行后续步骤。

## 下载 npm 样本

创建分析目录：

```bash
mkdir -p claude-code-analysis
```

下载边界版本、latest/next wrapper 包和 native 包：

```bash
npm pack @anthropic-ai/claude-code@2.1.90 --pack-destination claude-code-analysis --registry=https://registry.npmjs.org
npm pack @anthropic-ai/claude-code@2.1.91 --pack-destination claude-code-analysis --registry=https://registry.npmjs.org
npm pack @anthropic-ai/claude-code@2.1.92 --pack-destination claude-code-analysis --registry=https://registry.npmjs.org
npm pack @anthropic-ai/claude-code@2.1.196 --pack-destination claude-code-analysis --registry=https://registry.npmjs.org
npm pack @anthropic-ai/claude-code@2.1.197 --pack-destination claude-code-analysis --registry=https://registry.npmjs.org
npm pack @anthropic-ai/claude-code-darwin-arm64@2.1.196 --pack-destination claude-code-analysis --registry=https://registry.npmjs.org
npm pack @anthropic-ai/claude-code-darwin-arm64@2.1.197 --pack-destination claude-code-analysis --registry=https://registry.npmjs.org
npm pack @anthropic-ai/claude-code-linux-x64@2.1.197 --pack-destination claude-code-analysis --registry=https://registry.npmjs.org
```

网络较慢时，可以把 `--registry` 换成镜像站；但建议随后用官方 npm registry 的 `dist.shasum` / `dist.integrity` 做核对。主报告中已经列出本次使用样本的 SHA1、SHA256 和 npm integrity。

## 解包样本

解包 wrapper / `cli.js` 包：

```bash
mkdir -p claude-code-analysis/package-2.1.90
mkdir -p claude-code-analysis/package-2.1.91
mkdir -p claude-code-analysis/package-2.1.92
mkdir -p claude-code-analysis/package-2.1.196
mkdir -p claude-code-analysis/package-2.1.197

tar -xzf claude-code-analysis/anthropic-ai-claude-code-2.1.90.tgz -C claude-code-analysis/package-2.1.90
tar -xzf claude-code-analysis/anthropic-ai-claude-code-2.1.91.tgz -C claude-code-analysis/package-2.1.91
tar -xzf claude-code-analysis/anthropic-ai-claude-code-2.1.92.tgz -C claude-code-analysis/package-2.1.92
tar -xzf claude-code-analysis/anthropic-ai-claude-code-2.1.196.tgz -C claude-code-analysis/package-2.1.196
tar -xzf claude-code-analysis/anthropic-ai-claude-code-2.1.197.tgz -C claude-code-analysis/package-2.1.197
```

解包 native 包：

```bash
mkdir -p claude-code-analysis/native-darwin-arm64-2.1.196
mkdir -p claude-code-analysis/native-darwin-arm64-2.1.197
mkdir -p claude-code-analysis/native-linux-x64-2.1.197

tar -xzf claude-code-analysis/anthropic-ai-claude-code-darwin-arm64-2.1.196.tgz -C claude-code-analysis/native-darwin-arm64-2.1.196
tar -xzf claude-code-analysis/anthropic-ai-claude-code-darwin-arm64-2.1.197.tgz -C claude-code-analysis/native-darwin-arm64-2.1.197
tar -xzf claude-code-analysis/anthropic-ai-claude-code-linux-x64-2.1.197.tgz -C claude-code-analysis/native-linux-x64-2.1.197
```

目录结构应大致如下：

```text
claude-code-analysis/
  anthropic-ai-claude-code-2.1.91.tgz
  package-2.1.91/
    package/
      cli.js
  native-darwin-arm64-2.1.197/
    package/
      claude
  native-linux-x64-2.1.197/
    package/
      claude
```

## 可选：抽取 Darwin `__BUN.segment`

报告中的一部分表格使用了 Darwin Mach-O 的 `__BUN.segment`。如果你在 macOS 上，可以用 `otool` 查出 `__BUN` 段的 file offset 和 file size，再用 `dd` 抽取。

查看 `__BUN` 段信息：

```bash
otool -l claude-code-analysis/native-darwin-arm64-2.1.197/package/claude | grep -A8 -B2 "__BUN"
```

你会看到类似字段：

```text
segname __BUN
...
fileoff <offset>
filesize <size>
```

抽取时把 `<offset>` 和 `<size>` 换成实际数字：

```bash
dd if=claude-code-analysis/native-darwin-arm64-2.1.197/package/claude \
  of=claude-code-analysis/native-darwin-arm64-2.1.197/__BUN.segment \
  bs=1 skip=<offset> count=<size>
```

对 `2.1.196` 同理：

```bash
otool -l claude-code-analysis/native-darwin-arm64-2.1.196/package/claude | grep -A8 -B2 "__BUN"
dd if=claude-code-analysis/native-darwin-arm64-2.1.196/package/claude \
  of=claude-code-analysis/native-darwin-arm64-2.1.196/__BUN.segment \
  bs=1 skip=<offset> count=<size>
```

如果不抽取 `__BUN.segment`，复现脚本仍会直接扫描 native executable；只是 `summary.json` 中与 `__BUN.segment` 对应的条目会显示 `exists: false`。

## 执行分析脚本

```bash
python3 scripts/extract_marker_evidence.py --analysis-root claude-code-analysis --write-evidence
```

脚本会：

- 解码内置的 Base64 + XOR 常量。
- 生成 `evidence/decoded-domain-list.txt`。
- 生成 `evidence/decoded-keyword-list.txt`。
- 计算 `claude-code-analysis/*.tgz` 的 SHA1 / SHA256。
- 扫描 `2.1.90`、`2.1.91`、`2.1.92` 的 `cli.js`。
- 扫描 `2.1.197` 的 Darwin / Linux native executable。
- 如果存在 `__BUN.segment`，也扫描对应 Bun 段。
- 生成 `evidence/summary.json` 和 `evidence/scan-summary.tsv`。

## 如何解读输出

关键文件：

- [`evidence/summary.json`](evidence/summary.json)：机器可读摘要，包含 XOR key、列表哈希、各样本 offset。
- [`evidence/scan-summary.tsv`](evidence/scan-summary.tsv)：适合人读的扫描表。
- [`evidence/decoded-domain-list.txt`](evidence/decoded-domain-list.txt)：解码出的 147 项域名或后缀。
- [`evidence/decoded-keyword-list.txt`](evidence/decoded-keyword-list.txt)：解码出的 11 项关键词。
- [`evidence/marker-examples.tsv`](evidence/marker-examples.tsv)：不同 host / 时区会得到的日期标记样例。
- [`evidence/package-hashes.tsv`](evidence/package-hashes.tsv)：本地 tarball 哈希。

几个判断点：

- `literal_packyapi_offset = -1` 说明 `packyapi.com` 没有以明文形式出现。
- `domain_b64_offset` 和 `keyword_b64_offset` 为非负数，说明找到了混淆后的 Base64 常量。
- `contains_packyapi = true` 说明解码后列表包含 `packyapi.com`。
- `2.1.90` 中 Base64 常量和 marker current date offset 都是 `-1`，说明该版本还没有这套标记逻辑。
- `2.1.91` 和 `2.1.92` 中相关 offset 为非负数，说明边界落在 `2.1.90` 与 `2.1.91` 之间。
- native 包中 `domain_b64_offset` / `keyword_b64_offset` 为非负数，说明 latest/next 的 native 分发包仍包含同一组常量。

## 只验证解码逻辑

如果你不想下载 Claude Code 包，只想确认 Base64 + XOR 解码结果，也可以直接运行：

```bash
python3 scripts/extract_marker_evidence.py
```

这会输出类似：

```text
xor_key=91
domains=147 contains_packyapi=True
keywords=11 first=['deepseek', 'moonshot', 'minimax', 'xaminim', 'zhipu']
```

但没有样本文件时，脚本无法复现各版本 offset 和 tarball 哈希。

## 许可证

除另有说明外，本项目的报告正文、证据文本、表格和复现脚本按 CC BY-SA 4.0 发布，见 [`LICENSE`](LICENSE)。
