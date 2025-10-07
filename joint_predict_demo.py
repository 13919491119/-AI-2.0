import sys
sys.stdout.reconfigure(encoding='utf-8')
from xuanji_ai_main import run_xuanji_ai_utf8

if __name__ == "__main__":
    print("\n=== ChatGPT 智能分析 ===")
    run_xuanji_ai_utf8('chatgpt分析: 双色球 2025114期')
    print("\n=== 玄机AI2.0+Deepseek 六爻智能解读 ===")
    from ssq_data import SSQDataManager
    from ssq_ai_model import SSQAIModel
    data_manager = SSQDataManager()
    reds, blue = SSQAIModel(data_manager).predict()
    run_xuanji_ai_utf8(f'六爻分析: 双色球 2025114期 红球{reds} 蓝球{blue}')
