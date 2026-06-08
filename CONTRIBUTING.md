# Contributing

感谢你改进 `review-benchmark-harness`。

## 开发环境

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## 提交内容建议

- 保持 Python 3.9+ 兼容
- 运行时优先使用标准库
- 新增功能时同步补测试
- 保持输入输出格式向后兼容
- 如果调整评分逻辑，请在 PR 描述中说明对 benchmark 历史结果的影响

## 目录约定

- `src/review_benchmark_harness/`: 核心实现
- `tests/`: 单元测试与 CLI 测试
- `examples/`: 可直接运行的样例基准集

## 发布前检查

```bash
python -m unittest discover -s tests -v
review-benchmark-harness score --suite examples/sample-suite --predictions examples/sample-suite/predictions/good --system-name release-check
```
