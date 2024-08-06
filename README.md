# satdatagen
a Python package for generating datasets to be used in satellite tasking schedulers

## Installation
`satdatagen` is in the Python Package Index, and can be installed using pip. The command:

`python3 -m install satdatagen`

or

`pip3 install satdatagen`

will install the `satdatagen` library in addition to all necessary dependencies.

*Note: in some cases the library `openmeteo-requests` does not get automatically installed. Users will need to run `pip3 install openmeteo-requests` only once to solve this*

## User Requirements
This package relies on data collected from space-track.org, one of the main resource for satellite ephemeral data. Users of satdatagen must have an existing space-track.org login. Add a file called `credentials.json` to your working directory, with login information formatted as a JSON object:

```
{
  identity : 'username@email.com',
  password : 'yourPassword12345'
}
```

The satdatagen code will query the space-track.org servers for satellite data using the user's login information.  Note that each user is subject to space-track's query limit - up to 30 queries per minute and up to 300 queries per hour.  

## Usage

The `satdatagen` library is easy to use.  A dataset can be generated with minimal lines of code. Dataset generation revolves around the creation of 2 objects: a `TimeRange` object and a `GroundLocation` object.

### `TimeRange`
`satdatagen.TimeRange(start_date, periods, delta = 0, end_date = None)`
#### Parameters:
**start_date**: a `datetime` object or `str` in ISO-T format (`YYYY-MM-DDTHH:mm:ss`). Represents the start date/time for the dataset scheduling

**periods**: an `int`. Represents the number of time steps in the time range for the duration of scheduling

**[delta]**: optional parameter. `int`. Represents the time between each time step in the time range

**[end_date]**: optional parameter. a `datetime` object or `str` in ISO-T format (`YYYY-MM-DDTHH:mm:ss`). Represents the final date/time in the time range.



Users must provide *either* a `delta` value or `end_date` value to control the length of the time range.
