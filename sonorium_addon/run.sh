#!/usr/bin/with-contenv bash
# shellcheck shell=bash
# ==============================================================================
# Sonorium Addon Startup Script
# ==============================================================================

# Source bashio library
source /usr/lib/bashio/bashio.sh

bashio::log.info "Starting Sonorium addon..."

# Log environment for debugging
bashio::log.debug "Environment variables:"
bashio::log.debug "  SUPERVISOR_TOKEN present: $([ -n "${SUPERVISOR_TOKEN:-}" ] && echo 'yes' || echo 'no')"

# Export addon configuration as environment variables
export SONORIUM__STREAM_URL="$(bashio::config 'sonorium__stream_url')"
export SONORIUM__PATH_AUDIO="$(bashio::config 'sonorium__path_audio')"
export SONORIUM__MAX_CHANNELS="$(bashio::config 'sonorium__max_channels')"

bashio::log.info "Configuration:"
bashio::log.info "  Stream URL: ${SONORIUM__STREAM_URL}"
bashio::log.info "  Audio Path: ${SONORIUM__PATH_AUDIO}"
bashio::log.info "  Max Channels: ${SONORIUM__MAX_CHANNELS}"

# Create audio directory if it doesn't exist
if [ ! -d "${SONORIUM__PATH_AUDIO}" ]; then
    bashio::log.warning "Audio path does not exist, creating: ${SONORIUM__PATH_AUDIO}"
    mkdir -p "${SONORIUM__PATH_AUDIO}"
fi

# ==============================================================================
# Install Lovelace Card and Custom Integration
# ==============================================================================
HA_CONFIG="/config"
CARD_SOURCE="/app/sonorium/web/static/lovelace/sonorium-card.js"
INTEGRATION_SOURCE="/app/sonorium/ha_integration"

# Install Lovelace card to www folder
if [ -f "${CARD_SOURCE}" ]; then
    WWW_DIR="${HA_CONFIG}/www/community/sonorium"
    mkdir -p "${WWW_DIR}"

    # Only copy if different or doesn't exist
    if [ ! -f "${WWW_DIR}/sonorium-card.js" ] || ! cmp -s "${CARD_SOURCE}" "${WWW_DIR}/sonorium-card.js"; then
        cp "${CARD_SOURCE}" "${WWW_DIR}/sonorium-card.js"
        bashio::log.info "Lovelace card installed to ${WWW_DIR}/sonorium-card.js"
        bashio::log.notice "Add this resource in HA: /local/community/sonorium/sonorium-card.js (JavaScript Module)"
    else
        bashio::log.debug "Lovelace card already up to date"
    fi
else
    bashio::log.warning "Lovelace card source not found at ${CARD_SOURCE}"
fi

# Install custom integration
if [ -d "${INTEGRATION_SOURCE}" ]; then
    INTEGRATION_DIR="${HA_CONFIG}/custom_components/sonorium"

    # Check if we need to update
    if [ ! -d "${INTEGRATION_DIR}" ]; then
        mkdir -p "${INTEGRATION_DIR}"
        cp -r "${INTEGRATION_SOURCE}"/* "${INTEGRATION_DIR}/"
        bashio::log.info "Custom integration installed to ${INTEGRATION_DIR}"
        bashio::log.notice "Restart Home Assistant, then add Sonorium integration in Settings > Devices & Services"
    else
        # Check version and update if needed
        SOURCE_VERSION=$(grep -o '"version": "[^"]*"' "${INTEGRATION_SOURCE}/manifest.json" | cut -d'"' -f4)
        INSTALLED_VERSION=$(grep -o '"version": "[^"]*"' "${INTEGRATION_DIR}/manifest.json" 2>/dev/null | cut -d'"' -f4)

        if [ "${SOURCE_VERSION}" != "${INSTALLED_VERSION}" ]; then
            cp -r "${INTEGRATION_SOURCE}"/* "${INTEGRATION_DIR}/"
            bashio::log.info "Custom integration updated to version ${SOURCE_VERSION}"
            bashio::log.notice "Restart Home Assistant to apply integration update"
        else
            bashio::log.debug "Custom integration already up to date (v${INSTALLED_VERSION})"
        fi
    fi
else
    bashio::log.debug "Custom integration source not found at ${INTEGRATION_SOURCE}"
fi

# Check if sonorium command exists
if ! command -v sonorium &> /dev/null; then
    bashio::log.error "sonorium command not found!"
    bashio::log.error "Attempting to run via Python module..."
    exec python3 -m sonorium.entrypoint
fi

bashio::log.info "Launching Sonorium..."

# Run sonorium
exec sonorium
