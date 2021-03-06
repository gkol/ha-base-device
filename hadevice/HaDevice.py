import json
from datetime import datetime, timedelta
from HaDeviceEnums import EntityTypes, SensorTypes, ValueTypes


class BaseDevice:
    def __init__(self, sensor_id: str, device_id: str, manufacturer: str, model: str, name: str, ha_topic_name: str):
        self.device_id = device_id
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

    def process_ha_messages(self, ha_messages):
        pass

    def payload_online_check(self, payload):
        return True


class DeviceProperty:
    def __init__(self, base_device: BaseDevice, ha_name: str, value_type: ValueTypes, entity_type: EntityTypes,
                 sensor_type: SensorTypes):

        self.value_type = value_type
        self.config_topic = entity_type.config_topic.format(base_device.ha_topic_name, ha_name)

        self.ha_config = {
            "availability_topic": entity_type.availability_topic.format(base_device.ha_topic_name, ha_name),
            "json_attributes_topic": entity_type.json_attributes_topic.format(base_device.ha_topic_name, ha_name),
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

    def generate_messages(self, is_online, state_payload, attributes_payload=None):
        ha_messages = []

        ha_messages += [
            {'topic': self.config_topic, 'payload': json.dumps(self.ha_config)},
            {'topic': self.ha_config['availability_topic'], 'payload': "online" if is_online else "offline"}
        ]

        if not is_online:
            return

        ha_messages.append({'topic': self.ha_config['state_topic'], 'payload': state_payload})

        if attributes_payload:
            ha_messages.append({'topic': self.ha_config['json_attributes_topic'], 'payload': attributes_payload})

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
