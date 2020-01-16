import requests

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, ENTITY_ID_FORMAT
from homeassistant.const import CONF_ID, CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity import async_generate_entity_id

DEFAULT_NAME = 'MPK KR'

CONF_STOPS = 'stops'
CONF_PLATFORM = 'platform'
CONF_LINES = 'lines'
CONF_MODE = 'mode'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_STOPS): vol.All(cv.ensure_list, [
        vol.Schema({
            vol.Required(CONF_ID): cv.positive_int,
            vol.Required(CONF_PLATFORM): cv.string,
            vol.Optional(CONF_NAME): cv.string,
            vol.Optional(CONF_MODE, default="departure"): cv.string,
            vol.Optional(CONF_LINES, default=[]): cv.ensure_list
        })])
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    name = config.get(CONF_NAME)
    stops = config.get(CONF_STOPS)
    dev = []
    for stop in stops:
        stop_id = str(stop.get(CONF_ID))
        platform = stop.get(CONF_PLATFORM)
        lines = stop.get(CONF_LINES)
        mode = stop.get(CONF_MODE)
        if mode not in ["departure", "arrival"]:
            raise Exception("Invalid mode: {}".format(mode))
        if platform not in ["tram", "bus"]:
            raise Exception("Invalid platform: {}".format(platform))
        real_stop_name = MpkKrSensor.get_stop_name(stop_id, platform)
        if real_stop_name is None:
            raise Exception("Invalid stop id: {}".format(stop_id))
        stop_name = stop.get(CONF_NAME) or stop_id
        uid = '{}_{}_{}'.format(name, stop_name, mode)
        entity_id = async_generate_entity_id(ENTITY_ID_FORMAT, uid, hass=hass)
        dev.append(MpkKrSensor(entity_id, name, stop_id, platform, mode, stop_name, real_stop_name, lines))
    add_entities(dev, True)


class MpkKrSensor(Entity):
    def __init__(self, entity_id, name, stop_id, platform, mode, stop_name, real_stop_name, watched_lines):
        self.entity_id = entity_id
        self._name = name
        self._stop_id = stop_id
        self._platform = platform
        self._mode = mode
        self._watched_lines = watched_lines
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
    def device_state_attributes(self):
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
        data = MpkKrSensor.get_data(self._stop_id, self._platform, self._mode)
        if data is None:
            return
        departures = data["actual"]
        parsed_departures = []
        for departure in departures:
            line = departure["patternText"]
            if len(self._watched_lines) > 0 and line not in self._watched_lines:
                continue
            status = departure["status"]
            planned_time = departure["plannedTime"]
            actual_time = departure["actualTime"] if status == "PREDICTED" else planned_time
            direction = departure["direction"]
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
    def get_stop_name(stop_id, platform):
        data = MpkKrSensor.get_data(stop_id, platform)
        if data is None:
            return None
        return data["stopName"]

    @staticmethod
    def get_data(stop_id, platform, mode="departure"):
        base_url_tram = 'http://www.ttss.krakow.pl/internetservice/services/passageInfo/stopPassages/stop?stop={}&mode={}&language=pl'
        base_url_bus = 'http://ttss.mpk.krakow.pl/internetservice/services/passageInfo/stopPassages/stop?stop={}&mode={}'
        base_url = base_url_tram if platform == "tram" else base_url_bus
        address = base_url.format(stop_id, mode)
        response = requests.get(address)
        if response.status_code == 200 and response.content.__len__() > 0:
            return response.json()
        return None
