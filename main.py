from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from pypinyin import lazy_pinyin
import requests
import re
from bs4 import BeautifulSoup


@register("fetch_weather", "YourName", "获取城市天气和穿衣建议", "1.0.0")
class WeatherPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    def hanzi_to_pinyin(self, text):
        # 返回拼音字符串，比如“北京”->"beijing"
        return "".join(lazy_pinyin(text))

    def is_chinese(self, text):
        return bool(re.fullmatch(r"[\u4e00-\u9fff]+", text))

    @filter.command("天气")
    async def fetch_weather(self, event: AstrMessageEvent, cityname: str):
        # 检测输入是否有效
        if not self.is_chinese(cityname):
            yield event.plain_result("请输入有效的中文城市名喵～")
            return
        # 拼接拼音网址
        city_pinyin = self.hanzi_to_pinyin(cityname)
        url = f"https://www.tianqi.com/{city_pinyin}/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = "utf-8"
        except Exception as e:
            logger.error(f"请求失败：{e}")
            yield event.plain_result("请求天气服务失败，请稍后再试。")
            return

        if response.status_code != 200:
            logger.error(f"请求tianqi.com失败，状态码：{response.status_code}")
            yield event.plain_result("没有查询到天气喵~")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        try:
            # 天气和温度
            weather_dd = soup.find("dd", class_="weather")
            weather_info = weather_dd.find("span").text.strip()

            # 风向
            wind_info = "暂无风向信息"
            shidu_dd = soup.find("dd", class_="shidu")
            if shidu_dd:
                b_tags = shidu_dd.find_all("b")
                for b in b_tags:
                    if "风向" in b.text:
                        wind_info = b.text.strip()
                        break

            # 空气质量、PM值、日出日落
            kongqi_dd = soup.find("dd", class_="kongqi")
            air_quality = (
                kongqi_dd.find("h5").text.strip() if kongqi_dd else "暂无空气质量"
            )
            pm_value = kongqi_dd.find("h6").text.strip() if kongqi_dd else "暂无PM值"
            sun_times = (
                kongqi_dd.find("span").get_text(separator=" / ").strip()
                if kongqi_dd
                else "暂无日出日落时间"
            )

            # 构造输出内容
            reply = (
                f"📍 {cityname} 的天气情况如下：\n\n"
                f"🌤 天气：{weather_info}\n"
                f"💨 风向：{wind_info}\n"
                f"🍃 空气质量：{air_quality}（{pm_value}）\n"
                f"🌅 日出 / 日落：{sun_times}"
            )

            yield event.plain_result(reply)

        except Exception as e:
            logger.error(f"解析页面出错：{e}")
            yield event.plain_result("解析天气数据失败喵~可能是页面结构变了。")

    async def terminate(self):
        """插件被卸载/停用时调用"""
        logger.info("天气插件已卸载")
