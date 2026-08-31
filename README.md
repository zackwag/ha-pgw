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
| Total Usage | CCF | Cumulative gas consumption across all billed months |
| Current Month Usage | CCF | Current billing period usage |
| Previous Month Usage | CCF | Previous billing period usage |
| Current Bill | $ | Current month bill amount |
| Balance Due | $ | Outstanding balance |
| Gas Rate | $/CCF | Effective rate for current period |

## Energy Dashboard

Because PGW publishes usage only once per monthly bill, this integration does not
rely on a live sensor for the energy dashboard. Instead it imports your full
billing history into Home Assistant's long-term statistics, so the dashboard
shows one bar per billing month for your entire account history and stays current
as new bills post.

Two statistics are published:

| Statistic | Unit | Description |
|-----------|------|-------------|
| `pgw:gas_consumption` (**PGW Gas Consumption**) | CCF | Actual monthly consumption history |
| `pgw:gas_cost` (**PGW Gas Cost**) | your HA currency | The same history priced at your *current* rate — an estimate for comparing spend across months, not what you were billed |

To configure the dashboard:

1. Go to **Settings → Dashboards → Energy**
2. Under **Gas consumption**, click **Add gas source**
3. Select **PGW Gas Consumption**
4. For cost tracking, choose either:
   - **Use an entity with current price** → `sensor.pgw_gas_meter_gas_rate` (accurate going forward), or
   - **Use an entity tracking the total costs** → **PGW Gas Cost** (full history, estimated at your current rate)

The history is (re)imported on every poll, so newly posted bills appear within
6 hours with no further action.

## Data Updates

The integration polls PGW every 6 hours. PGW updates billing data monthly, so more frequent polling is unnecessary.

## Requirements

- Home Assistant 2024.1+
- A PGW customer portal account at [myaccount.pgworks.com](https://myaccount.pgworks.com)
