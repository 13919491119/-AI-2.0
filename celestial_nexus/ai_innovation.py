"""
ai_innovation.py
AI创新方法融合模块
- 支持大模型（GPT/NVIDIA NeMo）、因果推断、图神经网络（GNN）、强化学习（RL）等创新AI方法的统一接口与集成
"""
from gpt_api import GPTAPI
from nvidia_nemo_api import NvidiaNemoAPI

class AIInnovationHub:
    def __init__(self, gpt_key=None, nemo_key=None, deepseek_key=None):
        import os
        # 优先参数，其次环境变量，最后降级为None
        gpt_key = gpt_key or os.getenv('OPENAI_API_KEY')
        nemo_key = nemo_key or os.getenv('NVIDIA_NEMO_API_KEY')
        deepseek_key = deepseek_key or os.getenv('DEEPSEEK_API_KEY')
        self.gpt = GPTAPI(api_key=gpt_key) if gpt_key else None
        self.nemo = NvidiaNemoAPI(api_key=nemo_key) if nemo_key else None
        try:
            from deepseek_api import DeepseekAPI
            self.deepseek = DeepseekAPI(api_key=deepseek_key) if deepseek_key else None
        except Exception:
            self.deepseek = None
        # 预留因果推断、GNN、RL等接口
        self.causal = None
        self.gnn = None
        self.rl = None
    def gpt_infer(self, messages, **kwargs):
        # 优先使用DeepseekAPI进行推理
        if self.deepseek:
            try:
                resp = self.deepseek.chat(messages, **kwargs)
                return resp['choices'][0]['message']['content']
            except Exception as e:
                return f'[Deepseek调用失败: {e}]'
        # 兼容老逻辑（无Deepseek时才用GPT）
        if not self.gpt:
            return '[GPT未配置]'
        try:
            resp = self.gpt.chat(messages, **kwargs)
            return resp['choices'][0]['message']['content']
        except Exception as e:
            return f'[GPT调用失败: {e}]'
    def nemo_infer(self, messages, **kwargs):
        if not self.nemo:
            return '[NVIDIA NeMo未配置]'
        try:
            resp = self.nemo.chat(messages, **kwargs)
            return resp['choices'][0]['message']['content']
        except Exception as e:
            return f'[NeMo调用失败: {e}]'
    def causal_infer(self, data):
        # 预留因果推断方法
        return '[因果推断功能待扩展]'
    def gnn_infer(self, graph_data):
        # 预留图神经网络方法
        return '[GNN功能待扩展]'
    def rl_infer(self, env_state):
        # 预留强化学习方法
        return '[RL功能待扩展]'
