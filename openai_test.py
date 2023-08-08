# import openai
# from dotenv import load_dotenv
# import os

# load_dotenv()

# openai.api_key = os.getenv("OPENAI_API_KEY")
# model = "gpt-3.5-turbo"

# # role의 종류 : system, assistant, user
# # system : 역할 부여하기
# # assitant : 이전에 응답했던 결과 저장해서 대화의 흐름 유지
# # user : 도우미에게 직접 전달하는 내용
# messages = [
#     {"role": "system", "content": "You are a helpful assistant."},
#     {"role": "user", "content": "Who won the world series in 2020?"},
#     {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
#     {"role": "user", "content": "Where was it played?"}
# ]

# response = openai.ChatCompletion.create(
#     model = model,
#     messages = messages
# )

# answer = response['choices'][0]['message']['content']
# print(answer)