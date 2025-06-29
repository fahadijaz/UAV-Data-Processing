from rest_framework.views import APIView
from rest_framework.response import Response
from filetransfer import FileTransfer

class InitTransfer(APIView):
    def post(self, request):
        payload = request.data
        results = []

        for path in payload["sd_cards"]:
            ft = FileTransfer(
                input_path=path,
                output_path=payload["output_path"],
                data_overview_file=payload["flight_routes"],
                flight_log=payload["flight_log"]
            )
            ft.get_information()
            ft.reflectance_logic_with_timestamps()
            ft.detect_and_handle_new_routes()
            ft.match()
            results.append({
                "input_path": path,
                "flights": ft.flights_folders
            })

        return Response({"file_transfers": results})
