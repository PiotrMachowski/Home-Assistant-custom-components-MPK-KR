[![HACS Custom][hacs_shield]][hacs]
[![GitHub Latest Release][releases_shield]][latest_release]
[![GitHub All Releases][downloads_total_shield]][releases]
[![Buy me a coffee][buy_me_a_coffee_shield]][buy_me_a_coffee]
[![PayPal.Me][paypal_me_shield]][paypal_me]


[hacs_shield]: https://img.shields.io/static/v1.svg?label=HACS&message=Custom&style=popout&color=orange&labelColor=41bdf5&logo=HomeAssistantCommunityStore&logoColor=white
[hacs]: https://hacs.xyz/docs/faq/custom_repositories

[latest_release]: https://github.com/PiotrMachowski/Home-Assistant-custom-components-MPK-KR/releases/latest
[releases_shield]: https://img.shields.io/github/release/PiotrMachowski/Home-Assistant-custom-components-MPK-KR.svg?style=popout

[releases]: https://github.com/PiotrMachowski/Home-Assistant-custom-components-MPK-KR/releases
[downloads_total_shield]: https://img.shields.io/github/downloads/PiotrMachowski/Home-Assistant-custom-components-MPK-KR/total

[buy_me_a_coffee_shield]: https://img.shields.io/static/v1.svg?label=%20&message=Buy%20me%20a%20coffee&color=6f4e37&logo=buy%20me%20a%20coffee&logoColor=white
[buy_me_a_coffee]: https://www.buymeacoffee.com/PiotrMachowski

[paypal_me_shield]: https://img.shields.io/static/v1.svg?label=%20&message=PayPal.Me&logo=paypal
[paypal_me]: https://paypal.me/PiMachowski

# MPK Kraków sensor

This sensor uses official API provided by MPK Kraków.

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

## Installation

### Using [HACS](https://hacs.xyz/) (recommended)

This integration can be added to HACS as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories):
* URL: `https://github.com/PiotrMachowski/Home-Assistant-custom-components-MPK-KR`
* Category: `Integration`

After adding a custom repository you can use HACS to install this integration using user interface.

### Manual

To install this integration manually you have to download [*mpk_kr.zip*](https://github.com/PiotrMachowski/Home-Assistant-custom-components-MPK-KR/releases/latest/download/mpk_kr.zip) and extract its contents to `config/custom_components/mpk_kr` directory:
```bash
mkdir -p custom_components/mpk_kr
cd custom_components/mpk_kr
wget https://github.com/PiotrMachowski/Home-Assistant-custom-components-MPK-KR/releases/latest/download/mpk_kr.zip
unzip mpk_kr.zip
rm mpk_kr.zip
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
<a href="https://paypal.me/PiMachowski" target="_blank"><img src="https://www.paypalobjects.com/webstatic/mktg/logo/pp_cc_mark_37x23.jpg" border="0" alt="PayPal Logo" style="height: auto !important;width: auto !important;"></a>
