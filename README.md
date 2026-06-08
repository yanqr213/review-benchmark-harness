# review-benchmark-harness

`review-benchmark-harness` 是一个离线、零运行时依赖优先的 Python CLI，用于维护和执行 AI code review / 自动代码审查系统的基准评测。

它不调用任何 LLM API，也不负责生成审查意见；它只消费已经存在的 patch/diff、期望 finding、以及候选审查器的 JSON/Markdown 输出，然后计算：

- 命中率、误报、漏报
- Precision / Recall / F1
- 严重级别匹配
- 文件路径模糊匹配
- 行号定位误差
- 规则覆盖率
- baseline 对比与 leaderboard
- JSON / Markdown / CSV / JUnit 报告
- CI gate

适用对象：

- AI review agent 开发者
- 静态分析 / 自动审查工具作者
- 需要离线 benchmark harness 的评测工程团队

## 特性

- Python 3.9+，标准库优先，零运行时依赖
- 可安装 CLI：`review-benchmark-harness`
- 支持子命令：`score`、`init-suite`、`normalize-output`、`compare`、`check`
- 支持统一 diff 解析与修改行提取
- 支持 JSON / Markdown 审查输出归一化
- 支持 severity 映射与模糊文件/行匹配
- `--output`、`--markdown-output`、`--csv-output`、`--junit-output` 自动创建父目录
- `--check warning|error` 可用于 CI 软告警或硬失败

## 安装

```bash
python -m pip install .
```

安装后可直接使用：

```bash
review-benchmark-harness --help
```

也可以在源码目录下运行：

```bash
python -m review_benchmark_harness --help
```

## 快速开始

### 1. 初始化一个基准集

```bash
review-benchmark-harness init-suite work/demo-suite
```

这会生成：

- `manifest.json`
- `cases/`
- `patches/`
- `predictions/`
- `reports/`

并附带一个可运行样例。

### 2. 对现有 AI review 输出打分

```bash
review-benchmark-harness score ^
  --suite examples/sample-suite ^
  --predictions examples/sample-suite/predictions/good ^
  --system-name good-bot ^
  --output outputs/good/score.json ^
  --markdown-output outputs/good/score.md ^
  --csv-output outputs/good/cases.csv ^
  --junit-output outputs/good/junit.xml
```

### 3. 比较多个系统

```bash
review-benchmark-harness compare ^
  outputs/good/score.json ^
  outputs/noisy/score.json ^
  --output outputs/compare/leaderboard.json ^
  --markdown-output outputs/compare/leaderboard.md ^
  --csv-output outputs/compare/leaderboard.csv
```

### 4. 在 CI 中设置 gate

```bash
review-benchmark-harness check outputs/good/score.json --min-f1 0.80 --min-recall 0.75 --check error
```

## 输入格式

### 基准集目录结构

```text
suite/
  manifest.json
  cases/
    CASE-001.json
  patches/
    CASE-001.diff
  predictions/
    CASE-001.json
    CASE-001.md
  reports/
```

### `manifest.json`

```json
{
  "name": "sample-suite",
  "version": 1,
  "cases": ["CASE-001", "CASE-002"]
}
```

### case schema

```json
{
  "case_id": "CASE-001",
  "title": "Broad exception swallow",
  "patch": "patches/CASE-001.diff",
  "expected_findings": [
    {
      "file": "src/service.py",
      "line": 12,
      "severity": "warning",
      "rule_id": "python.swallowed-exception",
      "title": "Broad exception hides failure state",
      "message": "The new code catches Exception and only logs it."
    }
  ],
  "metadata": {
    "language": "python"
  }
}
```

### 审查器输出格式

支持两类输入：

1. JSON

接受以下常见形态：

- 顶层为 finding 数组
- 顶层对象包含 `findings` / `issues` / `results` / `comments`
- 单条对象包含 `file`、`line`、`severity`、`rule_id`、`title`、`message`

2. Markdown

从列表项中提取 finding，例如：

```markdown
- [warning] src/service.py line 12: broad exception hides failure state (rule: python.swallowed-exception)
- [error] api/user.ts L44: unsanitized redirect target (rule: web.open-redirect)
```

## 评估 AI review agent 的建议流程

1. 固定 benchmark suite，不把 patch 之外的仓库上下文混进分数里。
2. 对每个 case 保存机器可读的期望 finding。
3. 把 agent 输出先用 `normalize-output` 归一化，再进入 `score`。
4. 同时看整体 F1 和 case 级明细，不只看单一总分。
5. 把 `compare` 结果作为 leaderboard，把 `check` 作为 CI gate。
6. 把误报和漏报样本回灌到 suite，迭代 benchmark。

## CLI 说明

### `score`

```bash
review-benchmark-harness score --suite SUITE_DIR --predictions PREDICTIONS_DIR_OR_FILE [options]
```

常用参数：

- `--system-name`
- `--input-format auto|json|markdown`
- `--output`
- `--markdown-output`
- `--csv-output`
- `--junit-output`
- `--min-precision`
- `--min-recall`
- `--min-f1`
- `--min-rule-coverage`
- `--max-fp`
- `--max-fn`
- `--check warning|error`

### `init-suite`

```bash
review-benchmark-harness init-suite TARGET_DIR [--force] [--no-sample]
```

### `normalize-output`

```bash
review-benchmark-harness normalize-output INPUT_PATH --output normalized.json [--format auto|json|markdown]
```

### `compare`

```bash
review-benchmark-harness compare report-a.json report-b.json [report-c.json ...]
```

### `check`

```bash
review-benchmark-harness check score.json --min-f1 0.80 --check error
```

## 输出说明

### JSON score report

包含：

- 总体 metrics
- case 级指标
- matched / unmatched 明细
- threshold check 结果

### Markdown report

适合 PR 评论、wiki、日报。

### CSV report

适合导入表格和二次分析。

### JUnit report

适合接入 CI 测试报告面板。

## 示例

仓库内自带一个可直接运行的样例基准集：

- `examples/sample-suite`
- `examples/sample-suite/predictions/good`
- `examples/sample-suite/predictions/noisy`

建议运行：

```bash
review-benchmark-harness score --suite examples/sample-suite --predictions examples/sample-suite/predictions/good --system-name good-bot
review-benchmark-harness score --suite examples/sample-suite --predictions examples/sample-suite/predictions/noisy --system-name noisy-bot
```

## CI 集成

仓库内提供 GitHub Actions workflow，会执行：

- 多 Python 版本安装
- 单元测试
- CLI smoke test
- 样例 suite 打分

你也可以在任意 CI 中直接运行：

```bash
python -m pip install .
python -m unittest discover -s tests -v
review-benchmark-harness score --suite examples/sample-suite --predictions examples/sample-suite/predictions/good --output work/ci/score.json
review-benchmark-harness check work/ci/score.json --min-f1 0.80 --min-recall 0.80 --check error
```

## 隐私与安全

- 完全离线，不调用网络 API
- 不上传 patch、代码或审查结果
- 适合在内网或受控环境中使用
- 报告中可能包含源码路径与规则标识，归档时请按团队安全策略处理

## 限制

- 当前只支持统一 diff
- Markdown 解析面向常见 review 列表格式，不是完整 Markdown AST
- 模糊匹配是启发式算法，不等同于人工语义判断
- 评分关注 finding 对齐，不评估建议文案质量或修复可行性

## English

`review-benchmark-harness` is an offline Python CLI for benchmarking AI code review systems and automated review tools. It consumes existing patches, expected findings, and candidate review outputs in JSON or Markdown, then computes precision, recall, F1, severity alignment, file/line localization quality, rule coverage, baseline deltas, and leaderboard-style reports. It does not call any LLM API.

Core commands:

- `score`
- `init-suite`
- `normalize-output`
- `compare`
- `check`

Typical flow:

```bash
python -m pip install .
review-benchmark-harness score --suite examples/sample-suite --predictions examples/sample-suite/predictions/good --system-name good-bot --output outputs/good/score.json
review-benchmark-harness check outputs/good/score.json --min-f1 0.80 --check error
```

See `examples/sample-suite` for a runnable benchmark layout and `tests/` for expected behaviors.
