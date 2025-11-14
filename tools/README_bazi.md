# 八字计算库（tools/bazi_lib）说明

功能简介
- 提供 `BaziCalculator` 类，用于计算年/月/日/时四柱（干支）。
- 提供命令行工具 `tools/bazi_cli.py`，支持 JSON 或 Markdown 输出格式。

精度说明
- 若环境中安装了 `sxtwl`（推荐），库将使用 `sxtwl.fromSolar` 进行专业排盘，结果精确。
- 若未安装 `sxtwl`，库会退回到简化算法：年柱可准确计算，月柱/日柱在缺少天文历数据时无法准确给出并会返回 `null`，时柱给出带问号的近似时干（如 `?午`）。

安装建议
- 推荐安装：

```bash
pip install sxtwl
```

（在某些系统上 `sxtwl` 需要编译本地 C 组件或从二进制包安装，视系统而定。）

使用示例

JSON 输出：

```bash
python3 tools/bazi_cli.py --year 1976 --month 11 --day 13 --hour 11 --format json
```

Markdown 输出：

```bash
python3 tools/bazi_cli.py --year 1976 --month 11 --day 13 --hour 11 --format md
```

集成提示
- 在需要“专业”级别排盘（包括准确的月、日干支、节气等）时，请确保安装 `sxtwl`，否则请在上层服务中提示用户准确性限制。
