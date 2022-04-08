from src.duneapi.api import DuneAPI
from src.duneapi.dashboard import DuneDashboard

dune = DuneAPI.new_from_environment()
dashboard = DuneDashboard.from_file(
    api=dune, filename="./example/dashboard/_config.json"
)
dashboard.update()
print("Updated", dashboard)
