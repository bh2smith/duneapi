from src.duneapi.dashboard import DuneDashboard

dashboard = DuneDashboard("./example/dashboard/my_dashboard.json")
dashboard.update()
print("Updated", dashboard)
