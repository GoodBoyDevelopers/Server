from django.shortcuts import render
from youtube_transcript_api import YouTubeTranscriptApi
import openai
from dotenv import load_dotenv
import os

# Create your views here.

def get_keywords(summary):
    pass

def script_summary(scripts) :
    load_dotenv()

    openai.api_key = os.getenv("OPENAI_API_KEY")
    model = "gpt-3.5-turbo"

    messages = [
        {"role": "system", "content": "너는 요약해주는 역할이야."}
    ]
    for script in scripts :
        messages.append({"role": "user", "content": f"{script}"})
    messages.append({"role": "user", "content": "위의 글을 3줄 요약해주고, 핵심내용을 토대로 키워드 3개를 줄래?"})
    for m in messages :
        print(m)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0,
        max_tokens=20000
    )
    # response = openai.ChatCompletion.create(
    #     model = model,
    #     messages = messages
    # )

    summary = response['choices'][0]['message']['content']
    return summary

def script_extraction(video_id) :
    srt = YouTubeTranscriptApi.get_transcript("iCvmsMzlF7o", languages=['ko'])
    scripts = []
    temp = ""
    for s in srt :
        cleaned_s = s["text"].replace("''", "")
        temp += cleaned_s
        if len(temp) > 1000 :
            scripts.append(temp)
            temp = ""
    return (scripts)

# def youtube_view(request) :
    # video_id = request.data["video_id"]
video_id = "rrkrvAUbU9Y"
scripts = script_extraction(video_id)
summary = script_summary(scripts)
print(summary)