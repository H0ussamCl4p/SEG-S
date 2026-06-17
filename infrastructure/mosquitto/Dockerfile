# Mosquitto with the project's anonymous-listener config baked in.
# Used for the Azure deployment, where mounting an empty Azure Files share over
# /mosquitto/config would otherwise hide the config and break the broker.
FROM eclipse-mosquitto:2.0
COPY config/mosquitto.conf /mosquitto/config/mosquitto.conf
