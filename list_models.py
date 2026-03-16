import os
# langchain 라이브러리가 설치할 때 함께 설치된 구글 공식 SDK를 사용합니다.
import google.genai as genai

# agent.py에 넣으셨던 API 키를 그대로 여기에 복사해서 넣어주세요.
api_key = "AIzaSyAMuHYvCcADicZVo00CHdocDsQESgGnAOs" 

client = genai.Client(api_key=api_key)

print("사용 가능한 제미나이(Gemini) 모델 목록:")
print("-" * 40)
for model in client.models.list():
    print(f"- {model.name}")
print("-" * 40)
