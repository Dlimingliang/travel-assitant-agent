from openai import OpenAI
# main测试时使用
#from backend.app.config import get_settings
from backend.app.config import get_settings

# 全局LLM实例
_llm_instance = None

class LlmClient:
    def __init__(self, model: str = None, apiKey: str = None, baseUrl: str = None, timeout: int = 30):
        self.model = model
        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)


    def chat(self, messages: list[dict[str, str]], temperature: int = 0):
        """
         调用大语言模型进行思考，并返回其响应。 这里只提供非流式,流式另外提供方法
        """
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            print(f"调用模型 RequestJson: {messages}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=False)
            print(f"调用模型 ResponseJson: {response.model_dump_json()}")
        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")

def get_llm() -> LlmClient:
    """
    获取LLM实例(单例模式)
    Returns:
       LlmClient实例
    """
    global _llm_instance

    if _llm_instance is None:
        settings = get_settings()
        _llm_instance = LlmClient(
            model=settings.llm_model,
            apiKey=settings.llm_api_key,
            baseUrl=settings.llm_base_url)

        print(f"✅ LLM服务初始化成功")
    return _llm_instance

if __name__ == '__main__':
    llm_client = get_llm()
    messages = [
        {"role": "user", "content": "你好，请简单介绍一下你自己。"}
    ]
    llm_client.chat(messages=messages)