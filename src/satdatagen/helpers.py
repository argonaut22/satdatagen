
import numpy as np
import os
import requests
import pickle
import json
import numpy as np
from datetime import datetime, timezone
# from datetime import time as tm
from datetime import timedelta, date
import time
from astropy import units as u
from astropy.time import Time
from sgp4.api import Satrec
from sgp4.api import SatrecArray
from astropy.coordinates import TEME, CartesianDifferential, CartesianRepresentation
from astropy.coordinates import SkyCoord, solar_system_ephemeris, get_sun
from astropy import units as u
from astropy.coordinates import ITRS, AltAz, GCRS
from satdatagen.sizes import object_sizes
from satdatagen.M90 import M90_dict
import openmeteo_requests
import time
# from satdatagen.helpers import *
# from satdatagen.TimeRange import *
# from satdatagen.GroundLocation import *
# from satdatagen.Satellite import *
'''
########################################################################
************************************************************************
WEB QUERY methods
************************************************************************
########################################################################
'''

def space_track_login(space_track_credentials):
	'''
	logs user into space-track.org

	@param space_track_credentials: path to credentials.json file containing the user's login info to space-track.org
	@returns: login cookies

	'''
	with open(space_track_credentials) as json_file:
		credentials = json.load(json_file)

	url = "https://www.space-track.org/ajaxauth/login"
	x = requests.post(url, data = credentials)
	if x.status_code == 200:

		return x.cookies
	else:
		print("Login failed with code:",x.status_code)
		return None


def get_cookie(space_track_credentials):
	'''
		@param space_track_credentials: path to credentials.json file containing the user's login info to space-track.org
	    @returns: an existing cookie if there is one, otherwise, get a new one.
	    @returns: None if can't get cookies
    '''

	cookie_path = "./cookie.pkl"
	try:
		auth_cookie = pickle.load(open(cookie_path, "rb"))
	except:
		auth_cookie = None
	if type(auth_cookie) == requests.cookies.RequestsCookieJar:
		auth_cookie.clear_expired_cookies()
	else:
		auth_cookie = None
	# log in if needed
	if auth_cookie == None or len(auth_cookie) == 0:
		auth_cookie = space_track_login(space_track_credentials)
		pickle.dump(auth_cookie, open(cookie_path, "wb"))

	#return none if failed
	if auth_cookie == None:
		return None
		
	return auth_cookie

def get_unique_entries(sat_list, day):
	'''
		finds only the TLE for each object that is closest (but not after) the desired time of observation
		@param sat_list: list of dictionaries, 1 for each TLE returned by space-track.org, sorted in order of NORAD ID
		@param day: datetime.datetime object representing the day/time of observation

		@returns: list of dictionaries, 1 for each RSO observed on day
	'''
	
	idx = 1
	unique_sats = []
	# print(len(sat_list))
	while (idx < len(sat_list)):
		#go through indices of sat_list, find the other TLEs for the same NORAD ID, put them in temp_list
		temp_list = []
		try:
			while(sat_list[idx]['NORAD_CAT_ID'] == sat_list[idx-1]['NORAD_CAT_ID']):

				temp_list.append((idx-1, sat_list[idx-1]['EPOCH']))
				if idx < (len(sat_list) - 1):
					idx+=1
				else:
					break

			temp_list.append((idx-1, sat_list[idx-1]['EPOCH']))

			#go through temp_list to find the TLE that has the epoch closest to desired time, add that to unique_sats list
			closest_ep = 1000000000 #ridiculous number for initial comparison
			closest_idx = idx
			for ix,ep in temp_list:
				epoch = datetime.fromisoformat(ep)
				delta = day - epoch

				if delta.total_seconds() > 0 and delta.total_seconds() <= closest_ep:
					closest_ep = delta.total_seconds()
					closest_idx = ix
			unique_sats.append(sat_list[closest_idx])
			idx+=1
		except:
			# print(f'idx: {idx}, idx-1: {idx-1}')
			pass

	return unique_sats


def get_all_objects(space_track_credentials, day = None): 
	'''
	@param space_track_credentials: path to credentials.json file containing the user's login info to space-track.org
	@param day type: datetime.datetime object representing desired observation day (including time)

	@returns: the data that is received as response of the request to star-tracker as list of python dictionaries for each object
	'''

	auth_cookie = get_cookie(space_track_credentials)
	#query space-track for observation day
	if day is not None:
		#note that if the desired time is early on a day the closest TLE might be from the day before, set threshold to be 8 hours as most TLEs are reported on an 8-hourly basis
		if day.hour < 8:
			qdate = day.date() - timedelta(days=1)
		else:
			qdate = day.date()
		next_qdate = qdate + timedelta(days=1)
		url = f'https://www.space-track.org/basicspacedata/query/class/gp_history/EPOCH/{qdate.isoformat()}--{next_qdate.isoformat()}/orderby/NORAD_CAT_ID%20asc/emptyresult/show'
	#if no day specified then queries for current day
	else:
		url = f'https://www.space-track.org/basicspacedata/query/class/gp/decay_date/null-val/epoch/%3Enow-30/orderby/norad_cat_id/format/json'
	response_data = requests.get(url, allow_redirects=True, cookies=auth_cookie)
	
	if response_data.status_code == 401:
		raise Exception("SpaceTrack login failed.  Please check your credentials, clear the cookie file (cookie.pkl), and try again.")

	all_objects = []
	
	#create list of all objects returned
	for i in response_data.json():
		all_objects.append(dict(i))

	#only return closest TLEs that were recorded BEFORE time of obs.
	unique_objs = get_unique_entries(all_objects, day)

	return unique_objs
	

def get_sat_tle(space_track_credentials, sat_id, day):
	'''
		@param space_track_credentials: path to credentials.json file containing the user's login info to space-track.org
		@param sat_id: NORAD ID of RSO for which you'd like the TLEs
		@param day type: datetime.datetime object representing desired observation day (including time)

		@returns: python dictionary containing the TLE for that satellite which is closest to day
	'''
	auth_cookie = get_cookie(space_track_credentials)
	if day.hour < 8:
		qdate = day.date() - timedelta(days=1)
	else:
		qdate = day.date()
	next_qdate = qdate + timedelta(days=1)
		
	url = f'https://www.space-track.org/basicspacedata/query/class/gp_history/NORAD_CAT_ID/{sat_id}/EPOCH/{qdate.isoformat()}--{next_qdate.isoformat()}/emptyresult/show'
	response_data = requests.get(url, allow_redirects=True, cookies=auth_cookie)
	
	all_objects = []
	
	#create list of all objects returned
	closest_ep = 1000000000
	closest_tle = {}
	tle = {}
	for i in response_data.json():
		tle = dict(i)
		try:
			epoch = datetime.fromisoformat(tle['EPOCH'])
		except KeyError:
			return None
		else:
			delta = day - epoch
			if delta.total_seconds() > 0 and delta.total_seconds() <= closest_ep:
				closest_ep = delta.total_seconds()
				closest_tle = tle

	return tle


def propagate_sats(sats, time_list):
	'''
		propagates each object in sats to its position at the desired observation time(s)

		@param sats: list of dictionaries representing the TLEs returned from space-track after filtering for uniqueness
		@param time_list: list of datetime.datetime objects representing the desired observation time(s)

		@returns: tuple of ndarray numpy arrays.  error codes [e], TEME position coordinates [r], and TEME velocity coordinates [v], with each TLE passed in representing a row in each numpy array

	'''
	sat_arr = []
	for sat in sats:
		sat_arr.append(Satrec.twoline2rv(sat['TLE_LINE1'], sat['TLE_LINE2']))
	prop_sats = SatrecArray(sat_arr)

	times = Time(time_list, scale='utc')
	# print(times.jd1)
	# print(times.jd2)
	time_jd1 = 0
	time_jd2 = 0
	if type(times.jd1) == float:
		time_jd1 = np.array([times.jd1])
		time_jd2 = np.array([times.jd2])
	else:
		time_jd1 = times.jd1
		time_jd2 = times.jd2
	e,r,v = prop_sats.sgp4(time_jd1, time_jd2)
	return e,r,v



def get_alt_az(observ_loc, sat_teme, sat_teme_v, observ_time):
	'''
	returns the altitude and azimuth of the given RSO at the given time as observed from the observation location on ground

	@param observ_loc: astropy EarthLocation object representing the point on the ground we are observing from
	@param sat_teme: numpy array containing the TEME position coordinates of the sat as returned from propagate_sats(...)
	@param sat_teme_v: numpy array containing the TEME velocity coordinates of the sat as returned from propagate_sats(...)
	@param observ_time: datetime.datetime object representing time of observation

	@returns tuple of (altitude, azimuth)
	'''

	itrs_sat = get_sat_itrs(sat_teme, sat_teme_v, observ_time)

	topo_itrs_sat = itrs_sat.cartesian.without_differentials() - observ_loc.get_itrs(np.array(observ_time)).cartesian
	sat_itrs_topo = ITRS(topo_itrs_sat, obstime=observ_time, location=observ_loc)
	altaz = sat_itrs_topo.transform_to(AltAz(obstime=observ_time, location=observ_loc))

	return altaz.alt, altaz.az


def _generate_dataset(space_track_credentials, ground_loc, time_list,  method = 'krag', debug = False, 
					  limit = None, orbit = 'all', elevation_threshold=10., 
					  mixing_coeff = 0.8, output_file = None):
	'''
	generates the dataset as customized by user
	
	@param space_track_credentials: path to a .json file with your space-track.org login information
	@param ground_loc: astropy EarthLocation object
	@param time_list: list of astropy Time objects
	@param [method]: string that determines which AVM method to use to determine satellite brightness.  options are 'krag', 'molczan', 'hejduk'. default is the Krag method
	@param [debug]: internal debug toggle
	@param [limit]: integer that limits the number of satellites represented in the dataset. default is no limit, all satellites that pass over head included
	@param [orbit]: string that filters for objects in a certain orbit.  options are 'LEO', 'MEO', 'GEO', 'all'. default is objects at all orbits
					ALTERNATELY, orbit can be a float that retains objects with a semi-major axis less than the input value (in km)
	@param [elevation_threshold]: float that determines the minimum elevation angle for a satellite to be included in the dataset
	@param [mixing_coeff]: float between 0 and 1 that determines the ratio of diffuse/spectral reflection accounted for ONLY when method=='hejduk'
	@param [output_file]: path to a .json file to output dataset to

	@returns a python dictionary of all the satellites overhead with keys of satellite NORAD ID as given by space-track and values the altitude/azimuth of the satellite at the observation time

	'''

	cloud_start = time.time()
	cloud_cover = get_cloud_cover(ground_loc, time_list[0].datetime, time_list[-1].datetime)
	cloud_time = time.time() - cloud_start
	overhead_sats = {}
	observ_loc = ground_loc

	query_start = time.time()
	all_sats_for_obstime = get_all_objects(space_track_credentials, time_list[0].datetime)
	query_time = time.time() - query_start
	sats_in_dataset = []
	sat_areas = []

	
	#if orbit is a float or int, apply it as a numerical filter
	if isinstance(orbit, (int, float)) and not isinstance(orbit, bool):
		print("Filtering for semi-major axis < ", round(orbit, 0), " km")
		for s in all_sats_for_obstime:
			if float(s['SEMIMAJOR_AXIS']) <= orbit:
				sats_in_dataset.append(s)
				sat_areas.append(get_object_area(s['NORAD_CAT_ID']))
	#otherwise, filter by orbit type
	else:
		if orbit == 'LEO':
			print("Filtering for objects in LEO")
			for s in all_sats_for_obstime:
				if float(s['SEMIMAJOR_AXIS']) < 7178:
					sats_in_dataset.append(s)
					sat_areas.append(get_object_area(s['NORAD_CAT_ID']))
		elif orbit == 'MEO':
			print("Filtering for objects in MEO")
			for s in all_sats_for_obstime:
				if float(s['SEMIMAJOR_AXIS']) >= 7178 and float(s['SEMIMAJOR_AXIS']) < 36378:
					sats_in_dataset.append(s)
					sat_areas.append(get_object_area(s['NORAD_CAT_ID']))
		elif orbit == 'GEO':
			print("Filtering for objects in GEO")
			for s in all_sats_for_obstime:
				if float(s['SEMIMAJOR_AXIS']) >= 36378:
					sats_in_dataset.append(s)
					sat_areas.append(get_object_area(s['NORAD_CAT_ID']))
		else:
			print("No orbit filter applied")
			sats_in_dataset = all_sats_for_obstime
			for s in all_sats_for_obstime:
				sat_areas.append(get_object_area(s['NORAD_CAT_ID']))

	prop_start = time.time()
	e, r, v = propagate_sats(sats_in_dataset, time_list)
	prop_time = time.time() - prop_start

	trans_start = time.time()
	v_x = v[:,:,0] * u.km / u.s
	v_y = v[:,:,1] * u.km / u.s
	v_z = v[:,:,2] * u.km / u.s

	r_x = r[:,:,0] * u.km
	r_y = r[:,:,1] * u.km
	r_z = r[:,:,2] * u.km

	r_cartesian = CartesianRepresentation(x=r_x, y = r_y, z = r_z)
	v_cartesian = CartesianDifferential(d_x = v_x, d_y = v_y, d_z = v_z)
	teme = TEME(r_cartesian.with_differentials(v_cartesian), obstime=time_list)

	obstime = Time(time_list, scale = 'utc')
	itrs_sat = teme.transform_to(ITRS(obstime=time_list))

	topo_itrs_sat = itrs_sat.cartesian.without_differentials() - observ_loc.get_itrs(obstime).cartesian
	sat_itrs_topo = ITRS(topo_itrs_sat, obstime=obstime, location=observ_loc)
	altaz = sat_itrs_topo.transform_to(AltAz(obstime=obstime, location=observ_loc))
	trans_time = time.time() - trans_start
	filter_start = time.time()
	alt_degs = altaz.alt.dms[0]

	over_indices = np.nonzero(alt_degs>elevation_threshold)
	filter_time = time.time() - filter_start
	unique_sats = np.unique(over_indices[0])
	random_sats = unique_sats

	if limit and limit <= len(unique_sats):
		random_sats = np.random.choice(unique_sats, limit, replace = False)
	zip_start = time.time()
	avm_total_time = 0
	prev_s = -1
	for i in range(len(over_indices[0])):
		s = over_indices[0][i]
		t = over_indices[1][i]
		if s not in random_sats:
			continue
		else:
			
			if s != prev_s:
				sat = sats_in_dataset[s]
			# 	sat_area = get_object_area(sat['NORAD_CAT_ID'])
			s_area = sat_areas[s]
			prev_s = s
			avm = None
			cc_idx = (24 * (time_list[t].datetime.date() - time_list[0].datetime.date()).days) + time_list[t].datetime.hour
			# avm_start = time.time()
			if s_area is not None:
				avm_start = time.time()
				avm = str(get_avm(int(sat['NORAD_CAT_ID']), observ_loc, itrs_sat[s,t], s_area, time_list[t], method = method, mixing_coeff = mixing_coeff))
				avm_total_time += (time.time() - avm_start)
			# avm_total_time += time.time() - avm_start
			oh_dict = {'name':sat['OBJECT_NAME'],'time': time_list[t].datetime.isoformat(), 'alt':str(altaz[s,t].alt.dms), 'az':str(altaz[s,t].az.dms), 'TLE_LINE1':sat['TLE_LINE1'], 'TLE_LINE2':sat['TLE_LINE2'], 'AVM' : avm, 'cloud_cover' : str(cloud_cover[cc_idx])}
			if sat['NORAD_CAT_ID'] in overhead_sats:
				overhead_sats[sat['NORAD_CAT_ID']].append(oh_dict)
			else:
				overhead_sats[sat['NORAD_CAT_ID']] = [oh_dict]

	zip_time = time.time() - zip_start
	if debug:
		return cloud_time, query_time, prop_time, trans_time, filter_time, avm_total_time, zip_time
	else:
		if output_file:
			out = open(output_file, 'w')
			json.dump(overhead_sats, out)
			out.close()
		return overhead_sats

def get_sat_itrs(sat_teme, sat_teme_v, observ_time):
	'''
	@param sat_teme: numpy array containing the TEME position coordinates of the sat as returned from propagate_sats(...)
	@param sat_teme_v: numpy array containing the TEME velocity coordinates of the sat as returned from propagate_sats(...)
	@param observ_time: datetime.datetime object representing time of observation or astropy Time object
	'''

	teme_p = CartesianRepresentation(sat_teme*u.km)
	teme_v = CartesianDifferential(sat_teme_v*u.km/u.s)
	teme = TEME(teme_p.with_differentials(teme_v), obstime=observ_time)
	itrs_sat = teme.transform_to(ITRS(obstime=observ_time))

	return itrs_sat



def get_cloud_cover(ground_loc, start_date, end_date):
	'''
	@param ground_loc: astropy EarthLocation object representing ground observatory location
	@param obs_date: datetime object of the day of observation (starting time)
	@param periods: the number of time periods to increase the time by delta minutes
	@param delta: the number of minutes in each time period during the desired time range

	@returns: list of percentages by area for cloud cover, for ALL hours in ALL days in the range
	'''
	openmeteo = openmeteo_requests.Client()
	url = "https://archive-api.open-meteo.com/v1/archive"
	params = {
		"latitude": 42.58,
		"longitude": -71.44,
		"start_date": f'{start_date.date().isoformat()}',
		"end_date": f'{end_date.date().isoformat()}',
		"hourly": ["cloud_cover", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high"],
		"timezone": "auto"
	}
	responses = openmeteo.weather_api(url, params=params)

	# Process first location. Add a for-loop for multiple locations or weather models
	response = responses[0]
	# Process hourly data. The order of variables needs to be the same as requested.
	hourly = response.Hourly()
	hourly_cloud_cover = hourly.Variables(0).ValuesAsNumpy()
	hourly_cloud_cover_low = hourly.Variables(1).ValuesAsNumpy()
	hourly_cloud_cover_mid = hourly.Variables(2).ValuesAsNumpy()
	hourly_cloud_cover_high = hourly.Variables(3).ValuesAsNumpy()

	return hourly_cloud_cover

'''
########################################################################
************************************************************************
AVM methods
************************************************************************
########################################################################
'''
def get_phase_angle(ground_loc, sat_coords, t):
	'''
	calculates the phase angle between the sun, observer, and satellite

	@param ground_loc: astropy EarthLocation object of the observer's location on earth
	@param sat_coords: coordinates of the satellite in ITRS as astropy ITRS object
	@param t: datetime time object

	@returns: phase angle at observed time in radians
	'''
	obs_time = Time(t, scale='utc')
	#the following are all 1x3 numpy arrays
	sat_gcrs = sat_coords.transform_to(GCRS(obstime=obs_time)).cartesian.without_differentials().xyz.value
	ground_gcrs = ground_loc.get_gcrs(obs_time).cartesian.without_differentials().xyz.to(u.km).value
	solar_system_ephemeris.set('builtin')
	sun_gcrs = get_sun(obs_time).cartesian.xyz.to(u.km).value
	
	sun_sat_vec = sun_gcrs - sat_gcrs
	ground_sat_vec = ground_gcrs - sat_gcrs

	sun_sat_mag = np.sqrt(np.sum(np.square(sun_sat_vec)))
	ground_sat_mag = np.sqrt(np.sum(np.square(ground_sat_vec)))

	sun_sat_unit = sun_sat_vec / sun_sat_mag
	ground_sat_unit = ground_sat_vec / ground_sat_mag

	phase_angle = (np.arccos(np.dot(sun_sat_unit, ground_sat_unit)))

	return phase_angle

def get_range(ground_loc, sat_coords, observ_time):
	'''
	calculates the range between the satellite and the observer for the given satellite coordinates

	@param ground_loc: astropy EarthLocation object of the observer's location on earth
	@param sat_coords: coordinates of the satellite in ITRS as astropy ITRS object
	@param observ_time: datetime object of the time of observation

	@returns float of the range between observer and sat
	'''
	o_time = Time(observ_time, scale = 'utc', location = ground_loc)
	sat_topo = sat_coords.cartesian.without_differentials() - ground_loc.get_itrs(o_time).cartesian
	sat_itrs = ITRS(sat_topo, obstime=observ_time, location=ground_loc)

	return np.sqrt(np.sum(np.square(sat_itrs.cartesian.xyz.value)))

def orientation_correction(phase_angle):
	'''
	calculates the orientation correction component of apparent visual magnitude
	uses the phase factor according to the Molczan method which defines the intrinsic brightness at a 90deg phase angle and 1000km range_los

	@param phase_angle: phase angle between sun, observer, and satellite in radians

	@returns: float of correction value
	'''
	pi = np.pi
	return -2.5 * np.log10(((pi - phase_angle) * np.cos(phase_angle) + np.sin(phase_angle)))


def range_correction(range_los):
	'''
	calculates the range_los correction component of apparent visual magnitude
	since intrinsic magnitude is calculated for an object at 1000km range_los, this function is required to adjust its brightness to its actual range_los from the observer

	@param range_los: the range_los in km from the observer to the object

	@returns: float of correction value
	'''

	return 5 * np.log10(range_los) - 15

def get_molczan_avm(intrinsic_mag, range_los, phase_angle):
	'''

	@param intrinsic_mag: the value of the intrinsic magnitude of the object, M_90 as according to Molczan's method of determining AVM (90deg phase angle 1000km away)
	@param sat_diameter: estimated spherical diameter in ???meters???
	@param range_los: range_los from the observer to the RSO
	@param phase_angle: angle between the sun, RSO, and observer

	@returns: the AVM of the RSO
	'''
	# reflectivity = 0.1 #assumption from the IADC simplification
	or_cor = orientation_correction(phase_angle)
	range_cor = range_correction(range_los)

	return intrinsic_mag + or_cor + range_cor


def sphere_spectral_correction(phase_angle):
	'''
	calculates correction for the spectral component of reflection off a spherical objct

	@param phase_angle: @param phase_angle: angle between the sun, RSO, and observer in radians

	@returns: spectral correction value to be used in Hejduk AVM calcs
	'''
	return (1/(4*np.pi))

def sphere_diffuse_correction(phase_angle):
	'''
	calculates correction for the diffuse component of reflection off a spherical objct

	@param phase_angle: @param phase_angle: angle between the sun, RSO, and observer in radians

	@returns: diffuse correction value to be used in Hejduk AVM calcs
	'''
	pi = np.pi
	# p_rad = np.deg2rad(phase)
	term1 = 2.0/(3 * pi**2)
	term2 = ((pi - phase_angle) * np.cos(phase_angle)) + np.sin(phase_angle)
	return term1 * term2


def get_hejduk_avm(eta_val, sat_area, range_los, phase_angle):
	'''
	calculates AVM according to Hejduk's model of specular and diffuse components

	@param beta_val: float in [0,1] that represents the percent diffuse reflection of the object
	@param sat_area: float representing product of object area and albedo/reflectivity
	@param range_los: range_los from the observer to the RSO
	@param phase_angle: angle between the sun, RSO, and observer in radians

	@returns: AVM value
	'''
	eta_correction = (eta_val * sphere_diffuse_correction(phase_angle)) + ((1 - eta_val) * sphere_spectral_correction(phase_angle))
	return -26.74 - 2.5 * np.log10(sat_area*eta_correction) + 5 * np.log10(range_los)


def get_krag_avm(sat_area, range_los, phase_angle):
	'''
	calculates AVM for the satellite based on Krag (1974) formulations
	
	@param sat_area: float representing product of object area and albedo/reflectivity
	@param range_los: range_los from the observer to the RSO
	@param phase_angle: angle between the sun, RSO, and observer in radians

	@returns: AVM value
	'''
	phase_func = sphere_diffuse_correction(phase_angle)
	return -26.78 - 2.5 * np.log10((sat_area * phase_func)/(range_los**2))


def get_object_area(sat_id):
	'''
	gets the cross sectional areas of the objects from the DISCOs database.  If the cross sectional area is unavailable, then we assume a size based on object type

	@param sat_id: string representing the satellite ID assigned to the object

	@returns: the average cross-sectional of the object if available. if unavailable, assume average size based on object type, if object not in database, return None
	'''
	average_sizes = {'Payload': 18.98450165143947, 'Rocket Body': 17.7701706124929, 'Rocket Mission Related Object': 5.396699881790659, 'Payload Mission Related Object': 2.4455370389852473, 'Other Mission Related Object': 1.616687465289769, 'Rocket Fragmentation Debris': 1.1304850945750016, 'Payload Fragmentation Debris': 1.5320116252504274, 'Payload Debris': 13.088677796076936, 'Rocket Debris': 10.856166113561244}
	try:
		return object_sizes[sat_id]['xSectAvg'] * 1E-6
	except:
		try:
			return average_sizes[object_sizes[sat_id]['objectClass']] * 1E-6
		except:
			return None

def get_avm(satno, ground_loc, sat_coords, sat_area, obstime, method = 'krag', mixing_coeff = 0.8):
	'''
	performs calculations to get the brightness (AVM) of the satellite at the desired obstime
	@param sat_area: float representing product of object area and albedo/reflectivity
	@param ground_loc: astropy EarthLocation object of the observer's location on earth
	@param sat_coords: coordinates of the satellite in ITRS as astropy ITRS object

	@returns: AVM of satellite
	'''

	range_los = get_range(ground_loc, sat_coords, obstime)
	phase_angle = get_phase_angle(ground_loc, sat_coords, obstime)


	avm = get_krag_avm(sat_area, range_los, phase_angle)
	if method == 'molczan':
		try:
			m90 = float(M90_dict[satno]['m90'])
		except KeyError:
			m90 = get_krag_avm(sat_area, 1000, np.pi/2)
		avm = get_molczan_avm(m90, range_los, phase_angle)
	elif method == 'hejduk':
		avm = get_hejduk_avm(mixing_coeff, sat_area, range_los, phase_angle)
		# t = time.time() - start
		# print(t)
	return avm


	

# if __name__ == '__main__':
# 	from satdatagen.TimeRange import *
# 	from satdatagen.GroundLocation import *
# 	import time
# 	start_date = datetime(2024, 6, 18, hour = 18, minute = 0)
# # end_date = datetime(2024, 6, 19, hour = 16, minute = 30)
# 	periods = 24
# 	haystack_lon = -71.44 #degrees west
# 	haystack_lat = 42.58 #degrees north

# 	credentials = '/Users/adinagolden/Documents/MIT/Thesis/thesis/code/credentials.json'

# 	tr = TimeRange(start_date = start_date, periods = periods, delta = 30)
# 	gl = GroundLocation(credentials, haystack_lat, haystack_lon, tr)
# 	avg80 = 0
# 	avg100 = 0
# 	avg120 = 0
# 	avg140 = 0
# 	avg200 = 0
# 	avg260 = 0
	# for i in range(10):
	# 	total_80start = time.time()
	# 	times80 = _generate_dataset(credentials, gl.el, tr.times, limit = 80, debug = True)
	# 	total80 = time.time() - total_80start
	# 	avg80 += total80

	# 	total_100start = time.time()
	# 	times100 = _generate_dataset(credentials, gl.el, tr.times, limit = 100, debug = True)
	# 	total100 = time.time() - total_100start
	# 	avg100 += total100

	# 	total_120start = time.time()
	# 	times120 = _generate_dataset(credentials, gl.el, tr.times, limit = 120, debug = True)
	# 	total120 = time.time() - total_120start
	# 	avg120 += total120

	# 	total_140start = time.time()
	# 	times140 = _generate_dataset(credentials, gl.el, tr.times, limit = 140, debug = True)
	# 	total140 = time.time() - total_140start
	# 	avg140 += total140

	# 	total_200start = time.time()
	# 	times200 = _generate_dataset(credentials, gl.el, tr.times, limit = 200, debug = True)
	# 	total200 = time.time() - total_200start
	# 	avg200 += total200

	# 	total_260start = time.time()
	# 	times260 = _generate_dataset(credentials, gl.el, tr.times, limit = 260, debug = True)
	# 	total260 = time.time() - total_260start
	# 	avg260 += total260

	# start500 = time.time()
	# times500 = _generate_dataset(credentials, gl.el, tr.times, limit = 100, debug = True, orbit = 'LEO', method = 'krag', output_file = 'test.json')
	# total500 = time.time() - start500
	# print(f'task size 500: total = {total500}, breakdown = {times500}')
	# print("******")
	# print(times500)

	# start1000 = time.time()
	# times1000 = _generate_dataset(credentials, gl.el, tr.times, limit = 1000, debug = True)
	# total1000 = time.time() - start1000
	# print(f'task size 1000: total = {total1000}, breakdown = {times1000}')


	# print(f'task size 80: total = {avg80/10}, breakdown = {times80}')
	# print(f'task size 100: total = {avg100/10}, breakdown = {times100}')
	# print(f'task size 120: total = {avg120/10}, breakdown = {times120}')
	# print(f'task size 140: total = {avg140/10}, breakdown = {times140}')
	# print(f'task size 200: total = {avg200/10}, breakdown = {times200}')
	# print(f'task size 260: total = {avg260/10}, breakdown = {times260}')
	# out_file = open("example_day.json", 'w')
	# json.dump(all_sats, out_file)
	# out_file.close()

# 	import random
# 	creds = '/Users/adinagolden/Documents/MIT/Thesis/thesis/code/credentials.json'

# 	all_times = []
# 	for i in range(1):
# 		daytime = datetime(2023, random.randint(1,12), random.randint(1,29), hour=18, minute=30)
# 		print(daytime)
# 		# end = datetime(2024, 6, 20, hour=12)
# 		lat = 48.78 #degrees north
# 		lon = 9.18 #degrees west
# 		time_range = TimeRange(start_date = daytime, periods = 24, delta = 30)
# 		haystack = GroundLocation(creds, lat, lon, time_range = time_range)
# 		# x = get_all_objects(creds, daytime)


# 		times = _generate_dataset(creds, haystack.el, time_range.times, debug = True)
# 		all_times.append(times)
# 		print(times)
# 		print('***')

