# Philadelphia Gas Works (PGW) for Home Assistant

Custom component for [Home Assistant](https://www.home-assistant.io/) that monitors your [Philadelphia Gas Works](https://www.pgworks.com/) gas account. Provides usage, billing, and rate sensors compatible with the HA energy dashboard.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/zackwag/ha-pgw` as an **Integration**
4. Search for "Philadelphia Gas Works" and install
5. Restart Home Assistant

### Manual

Copy `custom_components/pgw` to your Home Assistant `config/custom_components/` directory and restart.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "Philadelphia Gas Works"
3. Enter your PGW portal email and password

## Sensors

| Sensor | Unit | Description |
|--------|------|-------------|
| Total Usage | CCF | Cumulative gas consumption (TOTAL_INCREASING) |
| Current Month Usage | CCF | Current billing period usage |
| Previous Month Usage | CCF | Previous billing period usage |
| Current Bill | $ | Current month bill amount |
| Balance Due | $ | Outstanding balance |
| Gas Rate | $/CCF | Effective rate for current period |

## Energy Dashboard

This integration is designed for the Home Assistant energy dashboard:

1. Go to **Settings → Dashboards → Energy**
2. Under **Gas consumption**, click **Add gas source**
3. Select `sensor.pgw_total_usage` (reports in CCF, which the dashboard accepts directly)
4. For cost tracking, select **Use an entity with current price** and choose `sensor.pgw_gas_rate`

## Data Updates

The integration polls PGW every 6 hours. PGW updates billing data monthly, so more frequent polling is unnecessary.

## Requirements

- Home Assistant 2024.1+
- A PGW customer portal account at [myaccount.pgworks.com](https://myaccount.pgworks.com)
