from src.duneapi.dashboard import DuneDashboard

dashboard = DuneDashboard.from_file("./example/dashboard/my_dashboard.json")
dashboard.update()
print("Updated", dashboard)
