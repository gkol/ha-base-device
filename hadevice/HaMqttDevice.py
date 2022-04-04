from HaDevice import BaseDevice, DeviceProperty
from datetime import datetime
from HaDeviceEnums import EntityTypes, SensorTypes, ValueTypes


class BaseMQTTDevice(BaseDevice):
    def __init__(self, sensor_id: str, device_id: str, input_topic: str, manufacturer: str, model: str,
                 name: str, ha_topic_name: str):
        super().__init__(
            sensor_id,
            device_id,
            manufacturer,
            model,
            name,
            ha_topic_name
        )
        self.input_topic = input_topic

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


class MqttDeviceProperty(DeviceProperty):
    def __init__(self, base_device: BaseDevice, ha_name: str, topic_property_name: str, value_type: ValueTypes,
                 entity_type: EntityTypes, sensor_type: SensorTypes):
        super().__init__(
            base_device,
            ha_name,
            value_type,
            entity_type,
            sensor_type
        )

        self.topic_property_name = topic_property_name

    def matches_rtl433_topic(self, input_topic):
        return True if self.topic_property_name in input_topic else False
