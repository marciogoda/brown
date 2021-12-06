import logging
import asyncio
import struct
import os

from uuid import UUID
from time import sleep
from io import BytesIO
from datetime import datetime
from picamera import PiCamera
from pyhap import tlv
from pyhap.camera import Camera
from pyhap.accessory import Accessory
from pyhap.util import to_base64_str, byte_bool

SETUP_TYPES = {
    'SESSION_ID': b'\x01',
    'STATUS': b'\x02',
    'ADDRESS': b'\x03',
    'VIDEO_SRTP_PARAM': b'\x04',
    'AUDIO_SRTP_PARAM': b'\x05',
    'VIDEO_SSRC': b'\x06',
    'AUDIO_SSRC': b'\x07'
}


SETUP_STATUS = {
    'SUCCESS': b'\x00',
    'BUSY': b'\x01',
    'ERROR': b'\x02'
}


SETUP_IPV = {
    'IPV4': b'\x00',
    'IPV6': b'\x01'
}


SETUP_ADDR_INFO = {
    'ADDRESS_VER': b'\x01',
    'ADDRESS': b'\x02',
    'VIDEO_RTP_PORT': b'\x03',
    'AUDIO_RTP_PORT': b'\x04'
}


SETUP_SRTP_PARAM = {
    'CRYPTO': b'\x01',
    'MASTER_KEY': b'\x02',
    'MASTER_SALT': b'\x03'
}


STREAMING_STATUS = {
    'AVAILABLE': b'\x00',
    'STREAMING': b'\x01',
    'BUSY': b'\x02'
}


RTP_CONFIG_TYPES = {
    'CRYPTO': b'\x02'
}


SRTP_CRYPTO_SUITES = {
    'AES_CM_128_HMAC_SHA1_80': b'\x00',
    'AES_CM_256_HMAC_SHA1_80': b'\x01',
    'NONE': b'\x02'
}


VIDEO_TYPES = {
    'CODEC': b'\x01',
    'CODEC_PARAM': b'\x02',
    'ATTRIBUTES': b'\x03',
    'RTP_PARAM': b'\x04'
}


VIDEO_CODEC_TYPES = {
    'H264': b'\x00'
}


VIDEO_CODEC_PARAM_TYPES = {
    'PROFILE_ID': b'\x01',
    'LEVEL': b'\x02',
    'PACKETIZATION_MODE': b'\x03',
    'CVO_ENABLED': b'\x04',
    'CVO_ID': b'\x05'
}


VIDEO_CODEC_PARAM_CVO_TYPES = {
    'UNSUPPORTED': b'\x01',
    'SUPPORTED': b'\x02'
}


VIDEO_CODEC_PARAM_PROFILE_ID_TYPES = {
    'BASELINE': b'\x00',
    'MAIN': b'\x01',
    'HIGH': b'\x02'
}


VIDEO_CODEC_PARAM_LEVEL_TYPES = {
    'TYPE3_1': b'\x00',
    'TYPE3_2': b'\x01',
    'TYPE4_0': b'\x02'
}


VIDEO_CODEC_PARAM_PACKETIZATION_MODE_TYPES = {
    'NON_INTERLEAVED': b'\x00'
}


VIDEO_ATTRIBUTES_TYPES = {
    'IMAGE_WIDTH': b'\x01',
    'IMAGE_HEIGHT': b'\x02',
    'FRAME_RATE': b'\x03'
}


SUPPORTED_VIDEO_CONFIG_TAG = b'\x01'


SELECTED_STREAM_CONFIGURATION_TYPES = {
    'SESSION': b'\x01',
    'VIDEO': b'\x02',
    'AUDIO': b'\x03'
}


RTP_PARAM_TYPES = {
    'PAYLOAD_TYPE': b'\x01',
    'SYNCHRONIZATION_SOURCE': b'\x02',
    'MAX_BIT_RATE': b'\x03',
    'RTCP_SEND_INTERVAL': b'\x04',
    'MAX_MTU': b'\x05',
    'COMFORT_NOISE_PAYLOAD_TYPE': b'\x06'
}


AUDIO_TYPES = {
    'CODEC': b'\x01',
    'CODEC_PARAM': b'\x02',
    'RTP_PARAM': b'\x03',
    'COMFORT_NOISE': b'\x04'
}


AUDIO_CODEC_TYPES = {
    'PCMU': b'\x00',
    'PCMA': b'\x01',
    'AACELD': b'\x02',
    'OPUS': b'\x03'
}


AUDIO_CODEC_PARAM_TYPES = {
    'CHANNEL': b'\x01',
    'BIT_RATE': b'\x02',
    'SAMPLE_RATE': b'\x03',
    'PACKET_TIME': b'\x04'
}


AUDIO_CODEC_PARAM_BIT_RATE_TYPES = {
    'VARIABLE': b'\x00',
    'CONSTANT': b'\x01'
}


AUDIO_CODEC_PARAM_SAMPLE_RATE_TYPES = {
    'KHZ_8': b'\x00',
    'KHZ_16': b'\x01',
    'KHZ_24': b'\x02'
}


SUPPORTED_AUDIO_CODECS_TAG = b'\x01'
SUPPORTED_COMFORT_NOISE_TAG = b'\x02'
SUPPORTED_AUDIO_CONFIG_TAG = b'\x02'
SET_CONFIG_REQUEST_TAG = b'\x02'
SESSION_ID = b'\x01'


NO_SRTP = b'\x01\x01\x02\x02\x00\x03\x00'
'''Configuration value for no SRTP.'''

VIDEO_CODEC_PARAM_PROFILE_VALUES = {
    b'\x00' : 'BASELINE',
    b'\x01' : 'MAIN',
    b'\x02' : 'HIGH' 
}

VIDEO_CODEC_PARAM_LEVEL_VALUES = {
        b'\x00': '3.1',
        b'\x01': '3.2',
        b'\x02': '4.0'
}

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

logger = logging.getLogger(__name__)


class BrownCamera(Camera):
    def __init__(self, options, *args, **kwargs):
        super().__init__(options, *args, **kwargs)

    def get_snapshot(self, image_size):  # pylint: disable=unused-argument, no-self-use
        """Return a jpeg of a snapshot from the camera.

        Overwrite to implement getting snapshots from your camera.

        :param image_size: ``dict`` describing the requested image size. Contains the
            keys "image-width" and "image-height"
        """
        with open(os.path.join('./', 'snapshot.jpg'), 'rb') as fp:
            return fp.read()

    def get_snapshot(self, image_size):
        with BytesIO() as stream:
            with PiCamera() as cam:
                cam.resolution = (image_size['image-width'], image_size['image-height'])
                cam.start_preview()
                sleep(1)
                cam.capture(stream, format='jpeg')
                stream.seek(0)
                return stream.read()
        return 
    
    async def start_stream(self, session_info, stream_config):
  
        logger.info(
            '[%s] Starting stream with the following parameters: %s',
            session_info['id'],
            stream_config
        )

        cmd = self.start_stream_cmd.format(**stream_config).split()
        logger.info('Executing start stream command: "%s"', ' '.join(cmd))
        try:
            process = await asyncio.create_subprocess_exec(*cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.PIPE,
                    limit=1024)

        except Exception as e:  # pylint: disable=broad-except
            logger.error('Failed to start streaming process because of error: %s', e)
            return False

        session_info['process'] = process

        logger.info(
            '[%s] Started stream process - PID %d',
            session_info['id'],
            process.pid
        )

        return True
    
    async def _start_stream(self, objs, reconfigure):  # pylint: disable=unused-argument
        """Start or reconfigure video streaming for the given session.

        Schedules ``self.start_stream`` or ``self.reconfigure``.

        No support for reconfigure currently.

        :param objs: TLV-decoded SelectedRTPStreamConfiguration
        :type objs: ``dict``

        :param reconfigure: Whether the stream should be reconfigured instead of
            started.
        :type reconfigure: bool
        """
        video_tlv = objs.get(SELECTED_STREAM_CONFIGURATION_TYPES['VIDEO'])
        audio_tlv = objs.get(SELECTED_STREAM_CONFIGURATION_TYPES['AUDIO'])

        opts = {}

        if video_tlv:
            video_objs = tlv.decode(video_tlv)

            video_codec_params = video_objs.get(VIDEO_TYPES['CODEC_PARAM'])
            if video_codec_params:
                video_codec_param_objs = tlv.decode(video_codec_params)
                opts['v_profile_id'] = \
                    VIDEO_CODEC_PARAM_PROFILE_VALUES[video_codec_param_objs[VIDEO_CODEC_PARAM_TYPES['PROFILE_ID']]]
                opts['v_level'] = \
                    VIDEO_CODEC_PARAM_LEVEL_VALUES[video_codec_param_objs[VIDEO_CODEC_PARAM_TYPES['LEVEL']]]

            video_attrs = video_objs.get(VIDEO_TYPES['ATTRIBUTES'])
            if video_attrs:
                video_attr_objs = tlv.decode(video_attrs)
                opts['width'] = struct.unpack('<H',
                            video_attr_objs[VIDEO_ATTRIBUTES_TYPES['IMAGE_WIDTH']])[0]
                opts['height'] = struct.unpack('<H',
                            video_attr_objs[VIDEO_ATTRIBUTES_TYPES['IMAGE_HEIGHT']])[0]
                opts['fps'] = struct.unpack('<B',
                                video_attr_objs[VIDEO_ATTRIBUTES_TYPES['FRAME_RATE']])[0]

            video_rtp_param = video_objs.get(VIDEO_TYPES['RTP_PARAM'])
            if video_rtp_param:
                video_rtp_param_objs = tlv.decode(video_rtp_param)
                if RTP_PARAM_TYPES['SYNCHRONIZATION_SOURCE'] in video_rtp_param_objs:
                    opts['v_ssrc'] = struct.unpack('<I',
                        video_rtp_param_objs.get(
                            RTP_PARAM_TYPES['SYNCHRONIZATION_SOURCE']))[0]
                if RTP_PARAM_TYPES['PAYLOAD_TYPE'] in video_rtp_param_objs:
                    opts['v_payload_type'] = \
                        video_rtp_param_objs.get(RTP_PARAM_TYPES['PAYLOAD_TYPE'])
                if RTP_PARAM_TYPES['MAX_BIT_RATE'] in video_rtp_param_objs:
                    opts['v_max_bitrate'] = struct.unpack('<H',
                        video_rtp_param_objs.get(RTP_PARAM_TYPES['MAX_BIT_RATE']))[0]
                if RTP_PARAM_TYPES['RTCP_SEND_INTERVAL'] in video_rtp_param_objs:
                    opts['v_rtcp_interval'] = struct.unpack('<f',
                        video_rtp_param_objs.get(RTP_PARAM_TYPES['RTCP_SEND_INTERVAL']))[0]
                if RTP_PARAM_TYPES['MAX_MTU'] in video_rtp_param_objs:
                    opts['v_max_mtu'] = video_rtp_param_objs.get(RTP_PARAM_TYPES['MAX_MTU'])

        if audio_tlv:
            audio_objs = tlv.decode(audio_tlv)

            opts['a_codec'] = audio_objs[AUDIO_TYPES['CODEC']]
            audio_codec_param_objs = tlv.decode(
                                        audio_objs[AUDIO_TYPES['CODEC_PARAM']])
            audio_rtp_param_objs = tlv.decode(
                                        audio_objs[AUDIO_TYPES['RTP_PARAM']])
            opts['a_comfort_noise'] = audio_objs[AUDIO_TYPES['COMFORT_NOISE']]

            opts['a_channel'] = \
                audio_codec_param_objs[AUDIO_CODEC_PARAM_TYPES['CHANNEL']][0]
            opts['a_bitrate'] = struct.unpack('?',
                audio_codec_param_objs[AUDIO_CODEC_PARAM_TYPES['BIT_RATE']])[0]
            opts['a_sample_rate'] = 8 * (
                1 + audio_codec_param_objs[AUDIO_CODEC_PARAM_TYPES['SAMPLE_RATE']][0])
            opts['a_packet_time'] = struct.unpack('<B',
                audio_codec_param_objs[AUDIO_CODEC_PARAM_TYPES['PACKET_TIME']])[0]

            opts['a_ssrc'] = struct.unpack('<I',
                audio_rtp_param_objs[RTP_PARAM_TYPES['SYNCHRONIZATION_SOURCE']])[0]
            opts['a_payload_type'] = audio_rtp_param_objs[RTP_PARAM_TYPES['PAYLOAD_TYPE']]
            opts['a_max_bitrate'] = struct.unpack('<H',
                audio_rtp_param_objs[RTP_PARAM_TYPES['MAX_BIT_RATE']])[0]
            opts['a_rtcp_interval'] = struct.unpack('<f',
                audio_rtp_param_objs[RTP_PARAM_TYPES['RTCP_SEND_INTERVAL']])[0]
            opts['a_comfort_payload_type'] = \
                audio_rtp_param_objs[RTP_PARAM_TYPES['COMFORT_NOISE_PAYLOAD_TYPE']]

        session_objs = tlv.decode(objs[SELECTED_STREAM_CONFIGURATION_TYPES['SESSION']])
        session_id = UUID(bytes=session_objs[SETUP_TYPES['SESSION_ID']])
        session_info = self.sessions[session_id]
        stream_idx = session_info['stream_idx']

        opts.update(session_info)
        success = await self.reconfigure_stream(session_info, opts) if reconfigure \
            else await self.start_stream(session_info, opts)

        if success:
            self._streaming_status[stream_idx] = STREAMING_STATUS['STREAMING']
        else:
            logger.error(
                '[%s] Failed to start/reconfigure stream, deleting session.',
                session_id
            )
            del self.sessions[session_id]
            self._streaming_status[stream_idx] = STREAMING_STATUS['AVAILABLE']

    def set_endpoints(self, value, stream_idx=None):
        """Configure streaming endpoints.

        Called when iOS sets the SetupEndpoints ``Characteristic``. The endpoint
        information for the camera should be set as the current value of SetupEndpoints.

        :param value: The base64-encoded stream session details in TLV format.
        :param value: ``str``
        """
        if stream_idx is None:
            stream_idx = 0

        objs = tlv.decode(value, from_base64=True)
        session_id = UUID(bytes=objs[SETUP_TYPES['SESSION_ID']])

        # Extract address info
        address_tlv = objs[SETUP_TYPES['ADDRESS']]
        address_info_objs = tlv.decode(address_tlv)
        is_ipv6 = struct.unpack('?',
            address_info_objs[SETUP_ADDR_INFO['ADDRESS_VER']])[0]
        address = address_info_objs[SETUP_ADDR_INFO['ADDRESS']].decode('utf8')
        target_video_port = struct.unpack(
            '<H', address_info_objs[SETUP_ADDR_INFO['VIDEO_RTP_PORT']])[0]
        target_audio_port = struct.unpack(
            '<H', address_info_objs[SETUP_ADDR_INFO['AUDIO_RTP_PORT']])[0]

        # Video SRTP Params
        video_srtp_tlv = objs[SETUP_TYPES['VIDEO_SRTP_PARAM']]
        video_info_objs = tlv.decode(video_srtp_tlv)
        video_crypto_suite = video_info_objs[SETUP_SRTP_PARAM['CRYPTO']][0]
        video_master_key = video_info_objs[SETUP_SRTP_PARAM['MASTER_KEY']]
        video_master_salt = video_info_objs[SETUP_SRTP_PARAM['MASTER_SALT']]

        # Audio SRTP Params
        audio_srtp_tlv = objs[SETUP_TYPES['AUDIO_SRTP_PARAM']]
        audio_info_objs = tlv.decode(audio_srtp_tlv)
        audio_crypto_suite = audio_info_objs[SETUP_SRTP_PARAM['CRYPTO']][0]
        audio_master_key = audio_info_objs[SETUP_SRTP_PARAM['MASTER_KEY']]
        audio_master_salt = audio_info_objs[SETUP_SRTP_PARAM['MASTER_SALT']]

        logger.info(
            'Received endpoint configuration:'
            '\nsession_id: %s\naddress: %s\nis_ipv6: %s'
            '\ntarget_video_port: %s\ntarget_audio_port: %s'
            '\nvideo_crypto_suite: %s\nvideo_srtp: %s'
            '\naudio_crypto_suite: %s\naudio_srtp: %s',
            session_id, address, is_ipv6, target_video_port, target_audio_port,
            video_crypto_suite,
            to_base64_str(video_master_key + video_master_salt),
            audio_crypto_suite,
            to_base64_str(audio_master_key + audio_master_salt)
        )

        # Configure the SetupEndpoints response

        if self.has_srtp:
            video_srtp_tlv = tlv.encode(
                SETUP_SRTP_PARAM['CRYPTO'], SRTP_CRYPTO_SUITES['AES_CM_128_HMAC_SHA1_80'],
                SETUP_SRTP_PARAM['MASTER_KEY'], video_master_key,
                SETUP_SRTP_PARAM['MASTER_SALT'], video_master_salt)

            audio_srtp_tlv = tlv.encode(
                SETUP_SRTP_PARAM['CRYPTO'], SRTP_CRYPTO_SUITES['AES_CM_128_HMAC_SHA1_80'],
                SETUP_SRTP_PARAM['MASTER_KEY'], audio_master_key,
                SETUP_SRTP_PARAM['MASTER_SALT'], audio_master_salt)
        else:
            video_srtp_tlv = NO_SRTP
            audio_srtp_tlv = NO_SRTP

        video_ssrc = int.from_bytes(os.urandom(3), byteorder="big")
        audio_ssrc = int.from_bytes(os.urandom(3), byteorder="big")

        res_address_tlv = tlv.encode(
            SETUP_ADDR_INFO['ADDRESS_VER'], self.stream_address_isv6,
            SETUP_ADDR_INFO['ADDRESS'], self.stream_address.encode('utf-8'),
            SETUP_ADDR_INFO['VIDEO_RTP_PORT'], struct.pack('<H', target_video_port),
            SETUP_ADDR_INFO['AUDIO_RTP_PORT'], struct.pack('<H', target_audio_port))

        response_tlv = tlv.encode(
            SETUP_TYPES['SESSION_ID'], session_id.bytes,
            SETUP_TYPES['STATUS'], SETUP_STATUS['SUCCESS'],
            SETUP_TYPES['ADDRESS'], res_address_tlv,
            SETUP_TYPES['VIDEO_SRTP_PARAM'], video_srtp_tlv,
            SETUP_TYPES['AUDIO_SRTP_PARAM'], audio_srtp_tlv,
            SETUP_TYPES['VIDEO_SSRC'], struct.pack('<I', video_ssrc),
            SETUP_TYPES['AUDIO_SSRC'], struct.pack('<I', audio_ssrc),
            to_base64=True)

        self.sessions[session_id] = {
            'id': session_id,
            'stream_idx': stream_idx,
            'address': address,
            'v_port': target_video_port,
            'v_srtp_key': to_base64_str(video_master_key + video_master_salt),
            'v_ssrc': video_ssrc,
            'a_port': target_audio_port,
            'a_srtp_key': to_base64_str(audio_master_key + audio_master_salt),
            'a_ssrc': audio_ssrc
        }

        self._management[stream_idx].get_characteristic('SetupEndpoints').set_value(response_tlv)

    async def stop(self):
        """Stop all streaming sessions."""
        await asyncio.gather(*(
        self.stop_stream(session_info) for session_info in self.sessions.values()), return_exceptions=True)
    
    async def stop_stream(self, session_info):  # pylint: disable=no-self-use

        session_id = session_info['id']
        # self._cam.stop_recording()
        ffmpeg_process = session_info.get('process')
        if ffmpeg_process:
            logger.info('[%s] Stopping stream.', session_id)
            try:
                ffmpeg_process.terminate()
                _, stderr = await asyncio.wait_for(
                    ffmpeg_process.communicate(), timeout=2.0)
                logger.debug('Stream command stderr: %s', stderr)
            except asyncio.TimeoutError:
                logger.error(
                    'Timeout while waiting for the stream process '
                    'to terminate. Trying with kill.'
                )
                ffmpeg_process.kill()
                await ffmpeg_process.wait()
            logger.debug('Stream process stopped.')
        else:
            logger.warning('No process for session ID %s', session_id)
        
    # @Accessory.run_at_interval(60)
    # async def save_snapshot(self):
    #     # date_stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    #     self._cam.resolution = (1640, 1232)
    #     self._cam.start_preview()
    #     sleep(5)
    #     self._cam.capture(f"/home/pi/brown/images/1.jpg")
    #     self._cam.stop_preview()

    # def start_record(self, file_name):
    #     self._cam.start_recording(file_name)
    #     return
    
    # def stop_record(self):
    #     self._cam.stop_recording()
    #     return