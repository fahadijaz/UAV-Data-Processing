from rest_framework.views import APIView
from rest_framework.response import Response
import platform, os, string, ctypes

class SDCardDetector(APIView):
    def get(self, request):
        dcim_folder = "DCIM"
        sd_cards = []

        system = platform.system()

        if system == "Windows":
            def is_removable_drive(letter):
                DRIVE_REMOVABLE = 2
                return ctypes.windll.kernel32.GetDriveTypeW(f"{letter}:/") == DRIVE_REMOVABLE

            for letter in string.ascii_uppercase:
                path = f"{letter}:/"
                if is_removable_drive(letter) and os.path.isdir(os.path.join(path, dcim_folder)):
                    sd_cards.append(os.path.join(path, dcim_folder))

        elif system in ("Linux", "Darwin"):
            for mount in ["/media", "/Volumes", "/mnt"]:
                if os.path.exists(mount):
                    for device in os.listdir(mount):
                        full = os.path.join(mount, device, dcim_folder)
                        if os.path.isdir(full):
                            sd_cards.append(full)

        return Response({"sd_cards": sd_cards})
