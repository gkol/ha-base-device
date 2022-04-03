from abc import ABC
from enum import Enum
import json
from datetime import datetime, timedelta

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


class BaseDevice(ABC):
    def __init__(self, sensor_id: str, device_id: str, input_topic: str, manufacturer: str, model: str,
                 name: str, ha_topic_name: str):
        self.device_id = device_id
        self.input_topic = input_topic
        self.manufacturer = manufacturer
        self.model = model
        self.name = name
        self.ha_topic_name = '{}_{}'.format(ha_topic_name, sensor_id)
        self.offline_timedelta = timedelta(minutes=2, seconds=30)
        self.last_message_time = None
        self.device_properties = []

    def check_offline(self):
        if not self.last_message_time or datetime.now() - self.last_message_time > self.offline_timedelta:
            for device_property in self.device_properties:
                ha_messages = device_property.generate_messages(False, None)
                if ha_messages:
                    self.process_ha_messages(ha_messages)

    def is_my_message(self, message):
        return self.input_topic.split('#')[0] in message.topic

    def on_message(self, message):
        if not self.is_my_message(message):
            return

        self.process_message(message)

    def process_message(self, message):
        ha_messages = []
        for device_property in self.device_properties:
            if not device_property.matches_rtl433_topic(message.topic):
                continue

            state = device_property.calculate_state(message)

            if self.payload_online_check(state):
                ha_messages = device_property.generate_messages(True, state)
            else:
                ha_messages = device_property.generate_messages(False, None)

        if ha_messages:
            self.process_ha_messages(ha_messages)

        self.last_message_time = datetime.now()

    def process_ha_messages(self, ha_messages):
        pass

    def payload_online_check(self, payload):
        return True


class DeviceProperty:
    def __init__(self, base_device: BaseDevice, ha_name: str, topic_property_name: str, value_type: ValueTypes,
                 entity_type: EntityTypes, sensor_type: SensorTypes):

        self.topic_property_name = topic_property_name
        self.value_type = value_type
        self.config_topic = entity_type.config_topic.format(base_device.ha_topic_name, ha_name)

        self.ha_config = {
            "availability_topic": entity_type.availability_topic.format(base_device.ha_topic_name, ha_name),
            # "json_attributes_topic": json_attributes_topic.format(base_device.ha_topic_name, self.name),
            "state_topic": entity_type.state_topic.format(base_device.ha_topic_name, ha_name),
            "unique_id": "{}_{}".format(base_device.ha_topic_name, ha_name),
            "name": ha_name,
            "qos": 1,
            "icon": sensor_type.icon,
            "device_class": sensor_type.device_class,
            "device": {
                "identifiers": [
                    base_device.device_id
                ],
                "manufacturer": base_device.manufacturer,
                "model": base_device.model,
                "name": base_device.name
            }
        }

        if sensor_type.unit_of_measurement:
            self.ha_config['unit_of_measurement'] = sensor_type.unit_of_measurement

    def matches_rtl433_topic(self, input_topic):
        return True if self.topic_property_name in input_topic else False

    def generate_messages(self, is_online, payload):
        ha_messages = []

        ha_messages += [
            {'topic': self.config_topic, 'payload': json.dumps(self.ha_config)},
            {'topic': self.ha_config['availability_topic'], 'payload': "online" if is_online else "offline"}
        ]

        if is_online:
            ha_messages.append({'topic': self.ha_config['state_topic'], 'payload': payload})

        return ha_messages

    def calculate_state(self, message):
        payload = message.payload.decode("utf-8")

        if self.value_type == ValueTypes.FLOAT:
            return float(payload)
        if self.value_type == ValueTypes.INT:
            return int(payload)
        elif self.value_type == ValueTypes.BINARY_NUMBER:
            return "on" if int(payload) == 1 else "off"

        return None
