import signal


from pyhap import camera, util
from pyhap.accessory import Bridge
from pyhap.accessory_driver import AccessoryDriver
from accessories.moisture_sensor import MoistureSensor
from accessories.picamera import BrownCamera
from accessories.watering_switch import WateringSwitch

# FFMPEG_CMD = (
#     'raspivid -o - -t 0 -w {width} -h {height} | '
#     'ffmpeg -i pipe: '
#     # '-map 0:0 -threads 0-vcodec libx264 -an -pix_fmt yuv420p -r {fps} -f rawvideo -tune zerolatency ' 
#     # '-vf scale={width}:{height} -b:v {v_max_bitrate}k -bufsize {v_max_bitrate}k  '
#     # '-payload_type 99 -ssrc {v_ssrc} '
#     '-f rtp -srtp_out_suite AES_CM_128_HMAC_SHA1_80 '
#     '-srtp_out_params {v_srtp_key} "rtp://{address}:{v_port}?rtcpport={v_port}&'
#     'localrtcpport={v_port}&pkt_size=1378"'
# )

FFMPEG_CMD = (
    #'raspivid -o - -t 0 -n -w {width} -h {height} | '
    'ffmpeg '
    #'-i pipe: -an -sn -dn '
    '-re -f v4l2 -i /dev/video0 '
    '-video_size {width}x{height} '
    '-an -sn -dn '
    '-vcodec h264_omx '
    '-s {width}x{height} '
    '-profile:v high -level:v 4.0 '
    '-pix_fmt yuv420p -color_range mpeg '
    '-f rawvideo -tune zerolatency '
    '-vf scale={width}:{height} '
    '-r {fps} ' 
    '-vb {v_max_bitrate}k -bufsize {v_max_bitrate}k '
    '-f rtp '
    #'-payload_type {v_payload_type} '
    '-ssrc {v_ssrc} '
    '-srtp_out_suite AES_CM_128_HMAC_SHA1_80 '
    '-srtp_out_params {v_srtp_key} '
    'srtp://{address}:{v_port}?rtcpport={v_port}&pkt_size=1378 '
    '-re -f mp3 -i music.mp3 -vn -sn -dn ' 
    '-acodec libopus -ab {a_max_bitrate}k -ac {a_channel} -ar {a_sample_rate}000 '
    '-f rtp '
    #'-payload_type {a_payload_type} '
    '-ssrc {a_ssrc} '
    '-srtp_out_suite AES_CM_128_HMAC_SHA1_80 '
    '-srtp_out_params {a_srtp_key} '
    'srtp://{address}:{a_port}?rtcpport={a_port}&pkt_size=188'
)

options = {
    "video": {
        "codec": {
            "profiles": [
                camera.VIDEO_CODEC_PARAM_PROFILE_ID_TYPES["BASELINE"],
                camera.VIDEO_CODEC_PARAM_PROFILE_ID_TYPES["MAIN"],
                camera.VIDEO_CODEC_PARAM_PROFILE_ID_TYPES["HIGH"]
            ],
            "levels": [
                camera.VIDEO_CODEC_PARAM_LEVEL_TYPES['TYPE3_1'],
                camera.VIDEO_CODEC_PARAM_LEVEL_TYPES['TYPE3_2'],
                camera.VIDEO_CODEC_PARAM_LEVEL_TYPES['TYPE4_0'],
            ],
        },
        "resolutions": [
            # Width, Height, framerate
            [320, 180, 30],
            [320, 240, 15], # Apple Watch requires this configuration
            [320, 240, 30],
            [480, 270, 30],
            [480, 360, 30],
            [640, 360, 30],
            [640, 480, 30],
            [1280, 720, 30],
            [1280, 960, 30],
            [1920, 1080, 30],
            [1600, 1200, 30]
        ],
    },
    "audio": {
        "codecs": [
            {
                'type': 'OPUS',
                'samplerate': 24,
            },
            # {
            #     'type': 'AAC-eld',
            #     'samplerate': 16
            # }
        ],
    },
    "srtp": True,
    "start_stream_cmd": FFMPEG_CMD,
    # hard code the address if auto-detection does not work as desired: e.g. "192.168.1.226"
    "address": util.get_local_address(), 
}

def get_bridge(driver):
    bridge = Bridge(driver, 'Brown')
    moisture_sensor = MoistureSensor(driver,'Moisture Sensor')
    acc = BrownCamera(options, driver, "Camera")
    water = WateringSwitch(21, 60, False, 0, driver, "Water")
    bridge.add_accessory(moisture_sensor)
    bridge.add_accessory(acc)
    bridge.add_accessory(water)

    return bridge

driver = AccessoryDriver(port=51826, persist_file='/home/pi/brown/brown.state')
driver.add_accessory(accessory=get_bridge(driver))
signal.signal(signal.SIGTERM, driver.signal_handler)
driver.start()