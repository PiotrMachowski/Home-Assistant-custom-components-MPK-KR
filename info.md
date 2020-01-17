[![buymeacoffee_badge](https://img.shields.io/badge/Donate-buymeacoffe-ff813f?style=flat)](https://www.buymeacoffee.com/PiotrMachowski)

This sensor use official API provided by MPK Kraków.

## Configuration options

| Key | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `name` | `string` | `False` | `MPK KR` | Name of sensor |
| `stops` | `list` | `True` | - | List of stop configurations |

### Stop configuration

| Key | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `id` | `positive integer` | `True` | - | ID of a stop |
| `platform` | `string` | `True` | - | One of `bus` or `tram` |
| `mode` | `string` | `False` | `departure` | One of `departure` or `arrival` |
| `name` | `string` | `False` | id | Name of a stop |
| `lines` | `list` | `False` | all available | List of monitored lines. |
| `directions` | `list` | `False` | all available | List of monitored directions. |

## Example usage

```
sensor:
  - platform: mpk_kr
      stops:
        - id: 623
          platform: bus
          lines:
            - "274"
        - id: 1173
          platform: tram
          mode: arrival
          directions:
            - "Nowy Bieżanów P+R"
```

## Hints

* Value for `stop_id` can be retrieved from [*TTS Kraków*](https://mpk.jacekk.net/). After choosing a desired stop its ID is a number visibile in URL.

* These sensors provides attributes which can be used in [*HTML card*](https://github.com/PiotrMachowski/Home-Assistant-Lovelace-HTML-card) or [*HTML Template card*](https://github.com/PiotrMachowski/Home-Assistant-Lovelace-HTML-Template-card): `html_timetable`, `html_departures`
  * HTML card:
    ```yaml
    - type: custom:html-card
      title: 'MPK'
      content: |
        <big><center>Timetable</center></big>
        [[ sensor.mpk_kr_623_tram_departure.attributes.html_timetable ]]
        <big><center>Departures</center></big>
        [[ sensor.mpk_kr_1173_bus_arrival.attributes.html_departures ]]
    ```
  * HTML Template card:
    ```yaml
    - type: custom:html-template-card
      title: 'MPK'
      ignore_line_breaks: true
      content: |
        <big><center>Timetable</center></big></br>
        {{ state_attr('sensor.mpk_kr_623_tram_departure','html_timetable') }}
        </br><big><center>Departures</center></big></br>
        {{ state_attr('sensor.mpk_kr_1173_bus_arrival','html_departures') }}
    ```

<a href="https://www.buymeacoffee.com/PiotrMachowski" target="_blank"><img src="https://bmc-cdn.nyc3.digitaloceanspaces.com/BMC-button-images/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>
