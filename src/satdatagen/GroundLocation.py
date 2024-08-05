from astropy.coordinates import EarthLocation
from astropy import units as u
import openmeteo_requests
from datetime import datetime
from satdatagen.TimeRange import TimeRange
import satdatagen.helpers as hel

		
class GroundLocation:
	'''
	this class acts as a wrapper for the astropy EarthLocation class, and is also how the user creates their dataset using the create_dataset class method.

	users create a GroundLocation instance with the latitude/longitude of a location on earth, a TimeRange object that determines the period of observation, and the path to their space-track.org login credentials
	'''
	def __init__(self, space_track_credentials, lat, lon, time_range):
		self.lon = lon
		self.lat = lat
		self.el = EarthLocation(lat = lat*u.deg, lon = lon*u.deg)
		self.time_range = time_range
		self.credentials = space_track_credentials

	def set_latlon(self, lat, lon):
		self.lat = lat
		self.lon = lon

	def get_latlon(self):
		return lat,lon

	def EarthLocation(self):
		return self.el

	def set_time_range(self, time_range):
		self.time_range = time_range

	def get_time_range(self):
		return self.time_range

	def generate_dataset(self, method = 'krag', limit = None, orbit = 'all', mixing_coeff = 0.8, output_file = None):
		'''
		returns a python dictionary of all the satellites overhead with keys of satellite NORAD ID as given by space-track and values the altitude/azimuth of the satellite at the observation time

		@param [method]: string that determines which AVM method to use to determine satellite brightness.  options are 'krag', 'molczan', 'hejduk'. default is the Krag method
		@param [limit]: integer that limits the number of satellites represented in the dataset. default is no limit, all satellites that pass over head included
		@param [orbit]: string that filters for objects in a certain orbit.  options are 'LEO', 'MEO', 'GEO', 'all'. default is objects at all orbits
		@param [mixing_coeff]: float between 0 and 1 that determines the ratio of diffuse/spectral reflection accounted for ONLY when method=='hejduk'
		@param [output_file]: path to a .json file to output dataset to

		'''
		return hel._generate_dataset(self.credentials, self.el, self.time_range.times, method = method, limit = limit, orbit = orbit, mixing_coeff = mixing_coeff, output_file = output_file)

	def __str__(self):
		return f'Latitude: {self.lat}, Longitude: {self.lon}, Time range: {self.time_range}'




# if __name__ == '__main__':
# 	lat = 48.78 #degrees north
# 	lon = 9.18 #degrees west

# 	temp = datetime(2024, 6, 10, hour=23, minute=30)
# 	temp2 = datetime(2024, 6, 12)
# 	td = temp2.date() - temp.date()
# 	print((td.days))
# 	time_range = TimeRange(temp, periods = 25, delta = 500)
# 	credentials = '/Users/adinagolden/Documents/MIT/Thesis/thesis/code/credentials.json'
# 	haystack = GroundLocation(credentials, lat, lon, time_range = time_range)
# 	print(haystack.find_all_overhead_sats())

# 	# print(clouds)