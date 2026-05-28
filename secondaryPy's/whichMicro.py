
# Source - https://stackoverflow.com/a/39677871
# Posted by slegroux, modified by community. See post 'Timeline' for change history
# Retrieved 2026-05-12, License - CC BY-SA 4.0

import pyaudio

p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

for i in range(0, numdevices):
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
