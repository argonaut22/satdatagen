import satdatagen as sdg
from datetime import datetime, timedelta
import os
print(sdg.__file__)

def satdatagen_wrapper(
    sdg_credentials_path,
    start_datetime, 
    delta = None, 
    end_datetime = None,
    obsv_lat = 0, 
    obsv_lon = 0, 
    orbit="LEO",
    method="krag", 
    elevation_min=10.,
    limit=None,
    savejson = False,
    savetxt = True,
    target_directory = ""
):
    """
    Generate a satellite dataset, save as a .json, and save specific fields to a .txt file.
    Note: an account with space-track.org is required, and the credentials must be accessible (see satdatagen docs for details)

    Args:
        sdg_credentials_path (str): Path to the space-track.org credentials file (see satdatagen docs for details).
        start_datetime (datetime):  The start datetime for the time range to be queried.
        delta (int, opt):           The interval for sampling in minutes. 
                                    If not provided (or if None), a single point at the start_datetime is queried.
        end_datetime (datetime, opt.): The end datetime for the time range to be queried. 
                                    By default, a 24 hr period is assumed. Not used if delta is not provided or is None.
        obsv_lat (float, opt.):     Latitude of the observation point (in degrees north). default is 0
        obsv_lon (float, opt.):     Longitude of the observation point (in degrees). default is 0
        orbit (str OR float, opt):  Orbit type (default: "LEO"; accepts: 'LEO', 'MEO', 'GEO', or 'all').
                                    If a float is provided, is is applied as the maximum semi-major axis in km.
        method (str, optional):     The method to use for avm calculation (options are 'krag', 'molczan', 'hejduk'; default: None).
                                    method = None will skip the AVM calculation and only return the satellite information, which is A LOT faster
        elevation_min (float, opt.):The minimum elevation threshold for a satellite to be considered visible (default: 10.).
        limit (int, optional):      Limit for the number of satellites in set
        savejson (Bool, opt.):      flag if json with full satdatagen dataset will be saved (default is False)
        savejson (Bool, opt.):      flag if txt with name-TLE lines will be saved (default is true)
        target_directory(str):      abs. or rel. filepath to directory where files will be saved
                                    directory must exist (this won't create it and will throw an error)

    Generates:
        a .json file with raw satdatagen output (all objects, all sightings)
        a .txt file of NAME-TLE1-TLE2 lines for the observed objects. Only the TLE lines for the latest sighting are recorded

    Returns:
        str: Path to the generated .txt file with specific fields.
    """
    # Calculate periods and time range
    if end_datetime is None:    #if no end time is specified, assumes a full day
        duration_mins = 24 * 60 #one day in minutes
    else:                       #ow. compute the duration in minutes via datetime
        duration_mins = abs((end_datetime - start_datetime).total_seconds()/ 60)

    if delta is None:           #if no delta is specified, assume a single sample at the start time
        periods = 1
        delta = duration_mins
    else:
        periods = int(duration_mins / delta) + 1  


    #create sdg objects
    tr = sdg.TimeRange(start_date=start_datetime, periods=periods, delta=delta)

    # Create ground location object
    gl = sdg.GroundLocation(sdg_credentials_path, obsv_lat, obsv_lon, tr)

    # Format output file name
    date_id_str = start_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"sdg_TLE_N_{date_id_str}_{method}_{orbit}_D{int(delta)}min"
    filename = filename.replace(" ", "_").replace(".", "p") #make filename more palatable

    #if saving json, set the filename
    if savejson:
        json_filepath = os.path.join(target_directory,filename+".json")
    else:
        json_filepath = None

    
    # Generate dataset and write the .json file (if requested)
    # this is the slowest part bc data pull
    ds = gl.generate_dataset(method=method, limit=limit, orbit=orbit, 
                             elevation_threshold=elevation_min, output_file=json_filepath)

    #correct the filename to include # of objects observed (formatted to be 6 digits always)
    N_objs = len(ds.keys())
    filename2 = filename.replace("sdg_TLE_N", f"sdg_TLE_N{N_objs:06}")

    #update json filename with number if we saved one
    if savejson: os.rename(json_filepath, os.path.join(target_directory, filename2+".json"))

    #if saving txt, set the filename and write to it
    if savetxt:
        txt_filepath = os.path.join(target_directory,filename2+".txt")
    
        with open(txt_filepath, "w") as txt_file:
            for key, value in ds.items():
                # Get the latest sighting's data
                last_sighting = value[-1]
                name = last_sighting.get("name", "Unknown Name")
                tle_line1 = last_sighting.get("TLE_LINE1", "Unknown Line1")
                tle_line2 = last_sighting.get("TLE_LINE2", "Unknown Line2")

                # Write the fields to the file
                txt_file.write(f"{name}\n{tle_line1}\n{tle_line2}\n")

        return txt_filepath

    return 1