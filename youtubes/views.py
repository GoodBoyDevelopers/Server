from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from models.models import *
from .serializers import *
from .youtubes import *
class YoutubeCreateAPIView(CreateAPIView):
    queryset = Youtube
    serializer_class = YoutubeSerializer

    def create(self, request, *args, **kwargs):
        link = request.data["link"]
        if link:
            # 유튜브 script 추출
            video_id = link.split("v=")[1]
            print(video_id)
            script = script_extraction(video_id)
            if script == "":
                return JsonResponse({"message" : "Scripts Extraction Failed"}, status=400)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        print(serializer.data["id"])
        youtube = Youtube.objects.get(id=serializer.data["id"])
        Script(script=script, youtube=youtube).save()
        

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)