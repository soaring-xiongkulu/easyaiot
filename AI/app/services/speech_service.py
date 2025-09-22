# service.py
import os
import time
import uuid
import requests
from pydub import AudioSegment

class SpeechService:
    def __init__(self, appid, appsecret):
        """
        初始化微信语音识别服务

        参数:
            appid (str): 微信公众号或小程序的AppID
            appsecret (str): 微信公众号或小程序的AppSecret
        """
        self.appid = appid
        self.appsecret = appsecret
        self.access_token = None
        self.token_expire_time = 0

    def get_access_token(self):
        """
        获取微信接口调用凭证access_token
        文档: https://developers.weixin.qq.com/doc/offiaccount/Basic_Information/Get_access_token.html
        """
        # 检查token是否还有效(提前5分钟刷新)
        if self.access_token and time.time() < self.token_expire_time - 300:
            return self.access_token

        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.appid}&secret={self.appsecret}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            if 'access_token' in data:
                self.access_token = data['access_token']
                # 默认有效期为7200秒(2小时)
                self.token_expire_time = time.time() + data.get('expires_in', 7200)
                print("✅ Access token obtained successfully")
                return self.access_token
            else:
                error_msg = data.get('errmsg', 'Unknown error')
                raise Exception(f"Failed to get access_token: {error_msg}")
        except Exception as e:
            raise Exception(f"Error getting access_token: {str(e)}")

    def convert_audio_to_mp3(self, input_path, output_path=None, frame_rate=16000, channels=1):
        """
        转换音频文件为微信API要求的格式(MP3, 16kHz, 单声道)
        微信API要求: MP3格式, 16kHz采样率, 单声道:cite[5]

        参数:
            input_path (str): 输入音频文件路径
            output_path (str): 输出MP3文件路径
            frame_rate (int): 目标采样率(默认16000Hz)
            channels (int): 目标声道数(默认1)

        返回:
            str: 转换后的音频文件路径
        """
        try:
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Audio file not found: {input_path}")

            # 读取音频文件
            audio = AudioSegment.from_file(input_path)

            # 设置目标参数
            audio = audio.set_frame_rate(frame_rate).set_channels(channels)

            # 确定输出文件路径
            if output_path is None:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}_converted.mp3"

            # 导出为MP3格式
            audio.export(output_path, format="mp3", bitrate="16k")
            print(f"✅ Audio converted successfully: {output_path}")

            # 检查文件大小(微信API要求最大1M):cite[5]
            file_size = os.path.getsize(output_path) / 1024 / 1024  # MB
            if file_size > 1:
                print(f"⚠️ Warning: File size ({file_size:.2f}MB) exceeds 1MB limit")

            return output_path

        except Exception as e:
            raise Exception(f"Audio conversion failed: {str(e)}")

    def upload_voice_for_recognition(self, audio_file_path, lang="zh_CN"):
        """
        上传语音文件到微信服务器进行识别
        对应API: /cgi-bin/media/voice/addvoicetorecofortext:cite[2]:cite[5]

        参数:
            audio_file_path (str): 音频文件路径
            lang (str): 语言代码, zh_CN(中文)或en_US(英文)

        返回:
            str: 语音唯一标识voice_id
        """
        access_token = self.get_access_token()

        # 生成唯一的voice_id:cite[6]
        voice_id = str(uuid.uuid4())

        # 构建API URL:cite[5]
        upload_url = f"https://api.weixin.qq.com/cgi-bin/media/voice/addvoicetorecofortext"
        params = {
            "access_token": access_token,
            "format": "mp3",
            "voice_id": voice_id,
            "lang": lang
        }

        try:
            with open(audio_file_path, 'rb') as f:
                files = {'media': f}
                response = requests.post(upload_url, params=params, files=files)

            response.raise_for_status()
            result = response.json()

            if result.get('errcode') == 0:
                print(f"✅ Voice uploaded successfully, voice_id: {voice_id}")
                return voice_id
            else:
                error_msg = result.get('errmsg', 'Unknown error')
                raise Exception(f"Upload failed: {error_msg}")

        except Exception as e:
            raise Exception(f"Voice upload error: {str(e)}")

    def query_recognition_result(self, voice_id, lang="zh_CN", max_retries=5, delay=1):
        """
        查询语音识别结果
        对应API: /cgi-bin/media/voice/queryrecoresultfortext:cite[2]:cite[5]

        参数:
            voice_id (str): 语音唯一标识
            lang (str): 语言代码
            max_retries (int): 最大重试次数
            delay (float): 重试延迟(秒)

        返回:
            str: 识别结果文本
        """
        access_token = self.get_access_token()

        query_url = f"https://api.weixin.qq.com/cgi-bin/media/voice/queryrecoresultfortext"
        params = {
            "access_token": access_token,
            "voice_id": voice_id,
            "lang": lang
        }

        # 微信建议上传后稍等再查询:cite[5]:cite[6]
        for attempt in range(max_retries):
            try:
                time.sleep(delay)  # 等待识别完成

                response = requests.post(query_url, params=params)
                response.raise_for_status()
                result = response.json()

                # 检查是否有识别结果
                if 'result' in result:
                    print(f"✅ Recognition successful on attempt {attempt + 1}")
                    return result['result']
                elif result.get('errcode') != 0:
                    error_msg = result.get('errmsg', 'Unknown error')
                    # 如果是临时错误，重试
                    if "busy" in error_msg.lower() or "wait" in error_msg.lower():
                        print(f"⚠️ Server busy, retrying... ({attempt + 1}/{max_retries})")
                        continue
                    else:
                        raise Exception(f"Recognition error: {error_msg}")
                else:
                    print(f"⚠️ No result yet, retrying... ({attempt + 1}/{max_retries})")

            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to get recognition result after {max_retries} attempts: {str(e)}")
                print(f"⚠️ Query failed, retrying... ({attempt + 1}/{max_retries})")

        raise Exception("Max retries exceeded without getting result")

    def recognize_speech(self, audio_file_path, lang="zh_CN"):
        """
        完整的语音识别流程: 转换格式 → 上传 → 查询结果

        参数:
            audio_file_path (str): 音频文件路径
            lang (str): 语言代码

        返回:
            str: 识别结果文本
        """
        try:
            # 1. 转换音频格式为微信API要求的格式
            print("🔄 Converting audio format...")
            converted_audio = self.convert_audio_to_mp3(audio_file_path)

            # 2. 上传语音文件
            print("🔄 Uploading voice file...")
            voice_id = self.upload_voice_for_recognition(converted_audio, lang)

            # 3. 查询识别结果
            print("🔄 Querying recognition result...")
            result = self.query_recognition_result(voice_id, lang)

            return result

        except Exception as e:
            raise Exception(f"Speech recognition failed: {str(e)}")
        finally:
            # 清理临时文件
            if 'converted_audio' in locals() and os.path.exists(converted_audio):
                os.remove(converted_audio)
                print(f"🧹 Temporary file cleaned: {converted_audio}")


def main():
    """
    主函数 - 示例如何使用语音识别服务
    """
    # 配置参数 - 需要替换为你的实际凭证
    APPID = "YOUR_APPID"  # 你的微信公众号/小程序AppID
    APPSECRET = "YOUR_APPSECRET"  # 你的微信公众号/小程序AppSecret
    AUDIO_FILE = "your_audio_file.wav"  # 你的音频文件路径

    # 创建语音识别服务实例
    recognizer = WeChatSpeechRecognitionService(APPID, APPSECRET)

    try:
        print("🎤 Starting speech recognition...")
        print(f"📁 Audio file: {AUDIO_FILE}")

        # 执行语音识别
        text_result = recognizer.recognize_speech(AUDIO_FILE, lang="zh_CN")

        # 输出结果
        print("\n" + "=" * 50)
        print("✅ RECOGNITION RESULT:")
        print("=" * 50)
        print(text_result)
        print("=" * 50)

    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()