import openmeteo_requests
import pandas as pd

def get_cloud_cover_list(location_tuple_list, start_date, end_date=None,
						 output_csv=False):
	'''
		Fetches cloud cover data for a list of locations over a specified date range via the Open Meteo API.
	
	@param location_tuple_list: list of tuples containing ( datetime object of the observation time)
	@param start_date: datetime object for the start DAY of the observation period (time is ignored since the API returns hourly data for the full day)
	@param end_date: datetime object of the end of the observation period (optional). defaults to None, which means only the start day is sampled.
	@param output_csv: boolean flag to save the output as a CSV file (default is False); if true, a csv file will be saved with a generated name; if a STRING is provided, it will be used as the filename.

	@returns: Dataframe with columns for ID, lat, long, and percentages by area for cloud cover, for ALL hours in ALL days in the range, on the hour
	'''

	# default end date to start date if not provided
	if end_date is None:
		end_date = start_date

	# get list of lats and longs for api call
	n_locations = len(location_tuple_list)
	latitudes = [loc[0] for loc in location_tuple_list]
	longitudes = [loc[1] for loc in location_tuple_list]

	# openmeteo setup and call
	openmeteo = openmeteo_requests.Client()
	url = "https://archive-api.open-meteo.com/v1/archive"
	params = {
			"latitude": latitudes,
			"longitude": longitudes,
			"start_date": f'{start_date.date().isoformat()}',
			"end_date": f'{end_date.date().isoformat()}',
			"hourly": ["cloud_cover"],
			"timezone": "auto"
		}

	responses = openmeteo.weather_api(url, params=params)

	# generate hourly times for column headers
	hourly = responses[0].Hourly()
	hourly_times = range(hourly.Time(), hourly.TimeEnd(), hourly.Interval())
	time_headers = pd.to_datetime(hourly_times, unit='s') # Convert unix timestamps to datetime

	#initialize DataFrame with headers
	init_columns = ["ID", "lat", "long"]
	headers = init_columns + list(time_headers)
	df = pd.DataFrame(index=range(n_locations), columns=headers)

	# get cloud cover for each location and store in DataFrame
	for ir, response in enumerate(responses):
		cloud_cover = response.Hourly().Variables(0).ValuesAsNumpy()
		df.loc[ir, "ID"] = ir
		df.loc[ir, "lat"] = latitudes[ir]
		df.loc[ir, "long"] = longitudes[ir]
		df.loc[ir, time_headers] = cloud_cover

	# generate output CSV file if requested
	if output_csv:
		if isinstance(output_csv, str):
			output_file = output_csv
		else:
			output_file = f"cloud_cover_N{n_locations}_{start_date.date().isoformat()}_{end_date.date().isoformat()}.csv"

		df.to_csv(output_file, index=False)
		print(f"Cloud cover data saved to {output_file}")

	return df

#example usage: 
# from datetime import datetime
# #test data
# location_tuple_list = [(52.5200, 13.4050), (48.8566, 2.3522), (51.5074, -0.1278)]  # Example locations: Berlin, Paris, London
# start_date = datetime(2023, 1, 1)  # Example start date
# end_date = datetime(2023, 1, 2)

# # Call the function with test data
# df = get_cloud_cover_list(location_tuple_list, start_date, end_date, output_csv=True)

