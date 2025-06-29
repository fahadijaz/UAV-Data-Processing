# backend/api/urls.py
from django.urls import path
from api.views import sdcard, filetransfer, routes, pilots, drones

urlpatterns = [
    path("sd-cards/", sdcard.SDCardDetector.as_view()),
    path("projects/", routes.ProjectInfo.as_view()),
    path("file-transfer/init/", filetransfer.InitTransfer.as_view()),
    path("file-transfer/move/", filetransfer.MoveFlight.as_view()),
    path("file-transfer/trash/", filetransfer.TrashFlight.as_view()),
    path("file-transfer/dupe/", filetransfer.DuplicateFlight.as_view()),
    path("file-transfer/skyline/", filetransfer.SkylineFlight.as_view()),
    path("file-transfer/confirm/", filetransfer.ConfirmAndMove.as_view()),
    path("pilots/", pilots.PilotList.as_view()),
    path("drones/", drones.DroneList.as_view()),
]

