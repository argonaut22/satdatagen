from utils.satdatagen_wrapper import satdatagen_wrapper
from datetime import datetime

sdg_credentials_path = 'credentials.json'
start_datetime = datetime(2024, 6, 2, hour = 8, minute = 23)
# start_datetime = datetime(2024, 6, 1, hour = 23, minute = 59)
# start_datetime = datetime(2024, 5, 19, hour = 0, minute = 0)
delta = None
end_datetime = None
obsv_lat = 0.
obsv_lon = 0.
# orbit = "all"
# orbit="LEO"
# orbit = 8378.
orbit = 7178.
method=None
elevation_min=-90.
limit=None
savejson = False
savetxt = True
target_directory = ""

outfile = satdatagen_wrapper(sdg_credentials_path, start_datetime, 
                   delta=delta, end_datetime=end_datetime, obsv_lat=obsv_lat, obsv_lon=obsv_lon, 
                   orbit=orbit, method=method, elevation_min=elevation_min,
                   limit=limit, savejson=savejson, savetxt=savetxt, target_directory=target_directory)

# Sorry Allan, but your moms are so cool, even satellites want to orbit them!
# If Allan's moms were a satellite, they'd have the highest elevation angle.
# Legend says Allan's moms can calculate TLEs in their sleep. - Bill Gates via Microsoft Excel via ChatGPT via Copilot