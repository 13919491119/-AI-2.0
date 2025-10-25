"""
训练入口（smoke test）
用法示例：
  python3 experiments/train.py --min-samples 200 --mlflow --run-name smoke-test
"""
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("train")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--min-samples",
        type=int,
        default=200,
        help=(
            "最小样本数，若不足则调用 fetch_online"
        ),
    )
    parser.add_argument(
        "--mlflow",
        action="store_true",
        help=("是否尝试记录到 mlflow 本地"),
    )
    run_name_default = f"smoke-{int(datetime.now().timestamp())}"
    parser.add_argument(
        "--run-name",
        type=str,
        default=run_name_default,
    )
    args = parser.parse_args()

    # 延迟导入以避免不必要依赖在未安装时导致脚本直接失败
    # 当直接从 experiments/ 目录运行脚本时，Python 的模块搜索路径可能不包含仓库根目录。
    # 在这里把仓库根路径插入 sys.path 前端，确保能导入顶层模块（如 ssq_data、ssq_ai_model）。
    try:
        repo_root = Path(__file__).resolve().parents[1]
        repo_root_str = str(repo_root)
        if repo_root_str not in sys.path:
            sys.path.insert(0, repo_root_str)
    except Exception:
        # 若路径处理失败，也不阻塞后续逻辑，导入错误将在下面的导入 try/except 中被捕获并报告
        pass
    try:
        from ssq_data import SSQDataManager
        from ssq_ai_model import SSQAIModel
    except Exception as e:
        logger.error(f"导入模块失败: {e}")
        raise

    dm = SSQDataManager()
    # 确保有一定量数据
    if len(dm.history) < args.min_samples:
        msg = (
            f"历史数据({len(dm.history)}) 小于需要的样本数 ({args.min_samples})，"
            "调用 fetch_online 以补齐（模拟数据）"
        )
        logger.info(msg)
        dm.fetch_online()
        logger.info(f"补采后历史数据条数: {len(dm.history)}")

    model = SSQAIModel(dm)

    if args.mlflow:
        try:
            import mlflow  # pyright: ignore[reportMissingImports]
            mlflow.set_experiment("xuanji-smoke")
            with mlflow.start_run(run_name=args.run_name):
                mlflow.log_param("min_samples", args.min_samples)
                res = model.train()
                mlflow.log_text(res, "train_result.txt")
                logger.info(res)
        except Exception as e:
            logger.warning(f"mlflow 记录失败或 mlflow 未安装：{e}")
            res = model.train()
            logger.info(res)
    else:
        res = model.train()
        logger.info(res)

    # 保存模型状态文件（若有）
    try:
        state_file = 'ssq_ai_model_state.json'
        import json
        state = {
            'trained_at': datetime.now().isoformat(),
            'train_count': model.cumulative_train_count,
        }
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        logger.info(f"训练状态已写入 {state_file}")
    except Exception as e:
        logger.warning(f"写入训练状态失败: {e}")


if __name__ == '__main__':
    main()
