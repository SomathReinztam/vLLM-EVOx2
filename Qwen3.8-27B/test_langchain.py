"""
pip install langchain-openai


"""

from langchain_openai import ChatOpenAI

BASE_URL=f"http://10.8.0.82:8002/v1"
MODEL = "qwen3-27b" 

llm = ChatOpenAI(
    model=MODEL,
    base_url=BASE_URL,
    api_key="EMPTY",
    temperature=0.2,
    max_tokens=4096,
)



if __name__ == "__main__":
    # print(BASE_URL)
    prompt = "¿Cuánto es 17*23? Piensa paso a paso."
    ai_message = llm.invoke(prompt)
    ai_message.pretty_print()


"""
se ejecuta:
python3 Qwen3.8-27B/test_langchain.py


"""