# eeProperty Home Assistant Integration

Home Assistant custom integration for eeProperty washing machine system.

## Features

- Monitor washing machine status
- View remaining time and cycle information
- Automatic discovery of all machines on your account
- Easy configuration through Home Assistant UI

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/eeproperty` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "eeProperty"
4. Enter your credentials:
   - API URL (default: https://api.eeproperty.com)
   - Username
   - Password
5. Click Submit

## Entities

The integration creates sensor entities for each washing machine:

- **Sensor**: Shows the current status (idle, running, completed, error)
- **Attributes**:
  - `remaining_time`: Time remaining in current cycle
  - `cycle`: Current wash cycle name

## API Customization

You'll need to update the API endpoints in `api.py` to match the actual eeProperty API:

- Authentication endpoint
- Machine list endpoint
- Machine status endpoint
- Control endpoints (start/stop)

## Development

This integration is a template. You need to:

1. Update API endpoints to match actual eeProperty API
2. Adjust data models based on actual API responses
3. Add additional entity types (switches, buttons) as needed
4. Update authentication flow if different
5. Test with real API credentials

## Support

For issues and feature requests, please use the GitHub issue tracker.

## License

MIT License
