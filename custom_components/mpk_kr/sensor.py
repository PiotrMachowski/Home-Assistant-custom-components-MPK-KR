import logging

import requests

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, ENTITY_ID_FORMAT
from homeassistant.const import CONF_ID, CONF_NAME, CONF_VERIFY_SSL
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity import async_generate_entity_id

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'MPK KR'

CONF_STOPS = 'stops'
CONF_PLATFORM = 'platform'
CONF_LINES = 'lines'
CONF_MODE = 'mode'
CONF_DIRECTIONS = 'directions'
CONF_CA_BUNDLE = 'ca_bundle'

REQUEST_TIMEOUT = 10

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_VERIFY_SSL, default=True): cv.boolean,
    vol.Optional(CONF_CA_BUNDLE): cv.isfile,
    vol.Required(CONF_STOPS): vol.All(cv.ensure_list, [
        vol.Schema({
            vol.Required(CONF_ID): cv.positive_int,
            vol.Required(CONF_PLATFORM): cv.string,
            vol.Optional(CONF_NAME): cv.string,
            vol.Optional(CONF_MODE, default="departure"): cv.string,
            vol.Optional(CONF_LINES, default=[]): cv.ensure_list,
            vol.Optional(CONF_DIRECTIONS, default=[]): cv.ensure_list
        })])
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    name = config.get(CONF_NAME)
    stops = config.get(CONF_STOPS)
    verify = config.get(CONF_CA_BUNDLE) or config.get(CONF_VERIFY_SSL)
    dev = []
    for stop in stops:
        stop_id = str(stop.get(CONF_ID))
        platform = stop.get(CONF_PLATFORM)
        lines = stop.get(CONF_LINES)
        directions = stop.get(CONF_DIRECTIONS)
        mode = stop.get(CONF_MODE)
        if mode not in ["departure", "arrival"]:
            _LOGGER.error("Invalid mode '%s' for stop %s, skipping this stop", mode, stop_id)
            continue
        if platform not in ["tram", "bus"]:
            _LOGGER.error("Invalid platform '%s' for stop %s, skipping this stop", platform, stop_id)
            continue
        real_stop_name = MpkKrSensor.get_stop_name(stop_id, platform, verify)
        if real_stop_name is None:
            _LOGGER.warning("No data returned for stop %s (%s), skipping this stop", stop_id, platform)
            continue
        stop_name = stop.get(CONF_NAME) or stop_id
        uid = '{}_{}_{}_{}'.format(name, stop_name, platform, mode)
        entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, uid, hass=hass)
        dev.append(MpkKrSensor(entity_id, name, stop_id, platform, mode, stop_name, real_stop_name, lines, directions,
                               verify))
    if not dev:
        _LOGGER.error("No sensors were created, check stop ids and TTSS availability")
        return
    add_entities(dev, True)


class MpkKrSensor(Entity):
    def __init__(self, entity_id, name, stop_id, platform, mode, stop_name, real_stop_name, watched_lines,
                 watched_directions, verify=True):
        self.entity_id = entity_id
        self._name = name
        self._stop_id = stop_id
        self._platform = platform
        self._mode = mode
        self._verify = verify
        self._watched_lines = watched_lines
        self._watched_directions = watched_directions
        self._stop_name = stop_name
        self._real_stop_name = real_stop_name
        self._departures = []
        self._departures_number = 0
        self._departures_by_line = dict()

    @property
    def name(self):
        return '{} - {} {}'.format(self._name, self._stop_name, self._mode)

    @property
    def icon(self):
        return "mdi:bus-clock"

    @property
    def state(self):
        if self._departures_number is not None and self._departures_number > 0:
            dep = self._departures[0]
            return MpkKrSensor.departure_to_str(dep)
        return None

    @property
    def unit_of_measurement(self):
        return None

    @property
    def extra_state_attributes(self):
        attr = dict()
        attr['stop_name'] = self._real_stop_name
        if self._departures is not None:
            attr['list'] = self._departures
            attr['html_timetable'] = self.get_html_timetable()
            attr['html_departures'] = self.get_html_departures()
            if self._departures_number > 0:
                dep = self._departures[0]
                attr['line'] = dep["line"]
                attr['direction'] = dep["direction"]
                attr['departure'] = dep["departure"]
                attr['time_to_departure'] = dep["time_to_departure"]
                attr['original_departure'] = dep["original_departure"]
                attr['status'] = dep["status"]
        return attr

    def update(self):
        data = MpkKrSensor.get_data(self._stop_id, self._platform, self._mode, self._verify)
        if data is None:
            return
        departures = data.get("actual") or []
        parsed_departures = []
        for departure in departures:
            line = departure["patternText"]
            direction = departure["direction"]
            if len(self._watched_lines) > 0 and line not in self._watched_lines \
                    or len(self._watched_directions) > 0 and direction not in self._watched_directions:
                continue
            status = departure["status"]
            planned_time = departure["plannedTime"]
            actual_time = departure["actualTime"] if status == "PREDICTED" else planned_time
            time_to_departure = departure["actualRelativeTime"] // 60
            parsed_departures.append(
                {
                    "line": line,
                    "direction": direction,
                    "departure": actual_time,
                    "original_departure": planned_time,
                    "time_to_departure": int(time_to_departure),
                    "status": status
                })
        self._departures = parsed_departures
        self._departures_number = len(parsed_departures)
        self._departures_by_line = MpkKrSensor.group_by_line(self._departures)

    def get_html_timetable(self):
        html = '<table width="100%" border=1 style="border: 1px black solid; border-collapse: collapse;">\n'
        lines = list(self._departures_by_line.keys())
        lines.sort()
        for line in lines:
            directions = list(self._departures_by_line[line].keys())
            directions.sort()
            for direction in directions:
                if len(direction) == 0:
                    continue
                html = html + '<tr><td style="text-align: center; padding: 4px"><big>{}, kier. {}</big></td>'.format(
                    line, direction)
                departures = ', '.join(map(lambda x: x["departure"], self._departures_by_line[line][direction]))
                html = html + '<td style="text-align: right; padding: 4px">{}</td></tr>\n'.format(departures)
        if len(lines) == 0:
            html = html + '<tr><td style="text-align: center; padding: 4px">Brak połączeń</td>'
        html = html + '</table>'
        return html

    def get_html_departures(self):
        html = '<table width="100%" border=1 style="border: 1px black solid; border-collapse: collapse;">\n'
        for departure in self._departures:
            html = html + '<tr><td style="text-align: center; padding: 4px">{}</td></tr>\n'.format(
                MpkKrSensor.departure_to_str(departure))
        html = html + '</table>'
        return html

    @staticmethod
    def departure_to_str(dep):
        return '{}, kier. {}: {} ({}m)'.format(dep["line"], dep["direction"], dep["departure"],
                                               dep["time_to_departure"])

    @staticmethod
    def group_by_line(departures):
        departures_by_line = dict()
        for departure in departures:
            line = departure["line"]
            direction = departure["direction"]
            if line not in departures_by_line:
                departures_by_line[line] = dict()
            if direction not in departures_by_line[line]:
                departures_by_line[line][direction] = []
            departures_by_line[line][direction].append(departure)
        return departures_by_line

    @staticmethod
    def get_stop_name(stop_id, platform, verify=True):
        data = MpkKrSensor.get_data(stop_id, platform, verify=verify)
        if data is None:
            return None
        return data.get("stopName")

    @staticmethod
    def get_data(stop_id, platform, mode="departure", verify=True):
        base_url_tram = 'https://www.ttss.krakow.pl/internetservice/services/passageInfo/stopPassages/stop?stop={}&mode={}&language=pl'
        base_url_bus = 'https://ttss.mpk.krakow.pl/internetservice/services/passageInfo/stopPassages/stop?stop={}&mode={}'
        base_url = base_url_tram if platform == "tram" else base_url_bus
        address = base_url.format(stop_id, mode)
        try:
            response = requests.get(address, timeout=REQUEST_TIMEOUT, verify=verify)
        except requests.exceptions.SSLError as err:
            _LOGGER.warning("SSL error for stop %s: %s. TTSS servers send an incomplete certificate chain; "
                            "see README for the 'ca_bundle' option", stop_id, err)
            return None
        except requests.exceptions.RequestException as err:
            _LOGGER.warning("Connection error for stop %s: %s", stop_id, err)
            return None
        if response.status_code != 200 or len(response.content) == 0:
            _LOGGER.warning("Unexpected response for stop %s: HTTP %s, %s bytes",
                            stop_id, response.status_code, len(response.content))
            return None
        try:
            return response.json()
        except ValueError as err:
            _LOGGER.warning("Invalid JSON for stop %s: %s", stop_id, err)
            return None
