from enum import Enum

base_topic_name = 'homeassistant'


class EntityTypes(bytes, Enum):
    def __new__(cls, value, entity_type):
        obj = bytes.__new__(cls, [value])
        obj._value_ = value
        obj.entity_type = entity_type
        obj.config_topic = base_topic_name + "/" + entity_type + "/{}/{}/config"
        obj.availability_topic = base_topic_name + "/" + entity_type + "/{}/{}/availability"
        obj.json_attributes_topic = base_topic_name + "/" + entity_type + "/{}/{}/attributes"
        obj.state_topic = base_topic_name + "/" + entity_type + "/{}/{}/state"
        return obj

    SENSOR = (0, 'sensor')
    BINARY_SENSOR = (1, 'binary_sensor')


class SensorTypes(bytes, Enum):
    def __new__(cls, value, device_class, icon, unit_of_measurement):
        obj = bytes.__new__(cls, [value])
        obj._value_ = value
        obj.device_class = device_class
        obj.icon = icon
        obj.unit_of_measurement = unit_of_measurement
        return obj

    TEMPERATURE_F = (0, "temperature", "mdi:thermometer", "°F")
    TEMPERATURE_C = (1, "temperature", "mdi:thermometer", "°C")
    HUMIDITY = (2, "humidity", "mdi:water-percent", "%")
    BATTERY = (3, "battery", "mdi:battery", None)


class ValueTypes(Enum):
    FLOAT = 0
    INT = 1
    BINARY_NUMBER = 2
