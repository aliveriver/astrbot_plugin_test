from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from pypinyin import lazy_pinyin
import requests
from bs4 import BeautifulSoup


@register(
    "astrbot_plugin_fetch_weather",
    "aliveriver",
    "一个简单的爬取 www.tianqi.com 来获取天气的插件",
    "1.0.0",
)
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    def hanzi_to_pinyin(self, text):
        # 返回拼音并连接成字符串
        return "".join(lazy_pinyin(text))

    @filter.command("天气")
    async def helloworld(self, event: AstrMessageEvent, cityname: str):
        message_chain = event.get_messages()  # 用户所发的消息的消息链
        logger.info(message_chain)

        """这是一个 爬取www.tianqi.com获得当天天气 指令"""
        url = f"https://www.tianqi.com/{self.hanzi_to_pinyin(cityname)}/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        response = requests.get(url, headers=headers)
        response.encoding = "utf-8"

        if response.status_code != 200:
            logger.error("请求tianqi.com失败，状态码：", {response.status_code})
            yield event.plain_result(f"没有查询到喵！")  # 发送一条纯文本消息
            return

        soup = BeautifulSoup(response.text, "html.parser")

        # 获取天气状态（晴、多云等）和温度范围
        weather_dd = soup.find("dd", class_="weather")
        weather_info = (
            weather_dd.find("span").text.strip() if weather_dd else "暂无天气信息"
        )

        # 获取风向信息
        shidu_dd = soup.find("dd", class_="shidu")
        wind_info = None
        if shidu_dd:
            b_tags = shidu_dd.find_all("b")
            for b in b_tags:
                if "风向" in b.text:
                    wind_info = b.text.strip()

        # 获取空气质量、PM值、日出日落
        kongqi_dd = soup.find("dd", class_="kongqi")
        air_quality = kongqi_dd.find("h5").text.strip() if kongqi_dd else "暂无空气质量"
        pm_value = kongqi_dd.find("h6").text.strip() if kongqi_dd else "暂无PM值"
        sun_times = (
            kongqi_dd.find("span").text.strip().replace("<br>", " / ")
            if kongqi_dd
            else "暂无日出日落"
        )

        # 构造回复内容
        message = (
            f"今天的 {cityname} 天气为：{weather_info}，"
            f"风向：{wind_info}，"
            f"空气质量：{air_quality}，{pm_value}，"
            f"日出日落时间：{sun_times}"
        )

        yield event.plain_result(message)  # 发送一条纯文本消息

    async def terminate(self):
        """可选择实现 terminate 函数，当插件被卸载/停用时会调用。"""
