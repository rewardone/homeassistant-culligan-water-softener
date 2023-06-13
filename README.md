# homeassistant-culligan-water-softener
Home Assistant specific integration for Culligan Water Softeners

# Culligan Water Softener Integration for Home Assistant

`Culligan Water Softener` is a _custom component_ for [Home Assistant](https://www.home-assistant.io/). The integration allows you to pull data for you Culligan supported water softener from the Culligan IoT and Ayla Networks servers.

It will create a number of sensors (refreshed every 5 seconds):
- Connection Status - whether the softener is connected to Ayla Networks
- Date/time - date and time set on water softener
- Last regeneration - the day of last regeneration
- Days of Salt Remaining - the day on which the end of salt is predicted
- Salt level - salt level load in percentage
- Today water usage - water used today
- Water current flow - current flow of water
- Water usage daily average - computed average by softener of daily usage
- Available water - water available to use before next regeneration

The units displayed are set in the application settings.

## Installation
Copy the `custom_components/culligan_water_softener` folder into the config folder.

## Configuration
To add a Culligan water softener to Home assistant, go to Settings and click "+ ADD INTEGRATION" button. From list select "Culligan Water Softener" and click it, in displayed window you must enter:
- Username - Culligan application username
- Password - Culligan application password

## License
[MIT](https://choosealicense.com/licenses/mit/)