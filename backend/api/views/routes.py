from rest_framework.views import APIView
from rest_framework.response import Response
import sqlite3

DB_PATH = "database/drone_data.db"

class ProjectInfo(APIView):
    def get(self, request):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT * FROM flight_routes")
        routes = cur.fetchall()

        cur.execute("SELECT * FROM flight_log")
        logs = cur.fetchall()

        projects = {}
        for r in routes:
            r_dict = dict(r)
            base = r_dict["BasePath"]
            projects.setdefault(base, {
                "output_path": base,
                "flight_routes": [],
                "flight_log": []
            })
            projects[base]["flight_routes"].append(r_dict)

        for l in logs:
            l_dict = dict(l)
            out_path = l_dict["output_path"]
            if out_path in projects:
                projects[out_path]["flight_log"].append(l_dict)

        conn.close()
        return Response(projects)
