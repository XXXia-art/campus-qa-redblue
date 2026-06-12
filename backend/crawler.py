"""
东南大学官网数据爬虫
用于抓取校园公开信息，完善 RAG 知识库
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def fetch_page(url: str, retries: int = 2, timeout: int = 15) -> str:
    """抓取页面 HTML，失败返回空字符串"""
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            resp.encoding = resp.apparent_encoding or "utf-8"
            if resp.status_code == 200:
                return resp.text
        except Exception as e:
            print(f"⚠️ 抓取失败 ({attempt+1}/{retries+1}): {url} — {e}")
        time.sleep(1)
    return ""


def extract_text_from_html(html: str, selectors: list = None) -> str:
    """从 HTML 中提取正文文本，去除导航/页脚等噪声"""
    soup = BeautifulSoup(html, "html.parser")
    
    # 去除噪声标签
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    
    # 优先使用指定选择器
    if selectors:
        for sel in selectors:
            elem = soup.select_one(sel)
            if elem:
                return elem.get_text(separator="\n", strip=True)
    
    # 默认尝试常见内容区
    for sel in [".content", "#content", ".main-content", "article", ".detail", ".v_news_content", ".wp_articlecontent"]:
        elem = soup.select_one(sel)
        if elem:
            return elem.get_text(separator="\n", strip=True)
    
    # 兜底：取 body
    body = soup.find("body")
    if body:
        return body.get_text(separator="\n", strip=True)
    return ""


def crawl_seu_overview() -> str:
    """抓取学校概况/简介"""
    urls = [
        ("https://www.seu.edu.cn/xxgk/xxjj.htm", [".content", ".v_news_content", "#content"]),
        ("https://www.seu.edu.cn/xxgk/xxjj.htm", None),
    ]
    texts = []
    for url, sels in urls:
        html = fetch_page(url)
        if html:
            text = extract_text_from_html(html, sels)
            if text and len(text) > 100:
                texts.append(text)
        time.sleep(1)
    return "\n\n".join(texts)


def crawl_seu_departments() -> str:
    """抓取院系设置"""
    url = "https://www.seu.edu.cn/yxsz.htm"
    html = fetch_page(url)
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    
    departments = []
    # 常见院系列表的选择器
    for link in soup.select("a[href*='.seu.edu.cn']"):
        name = link.get_text(strip=True)
        href = link.get("href", "")
        if name and len(name) > 2 and len(name) < 30 and ("学院" in name or "系" in name):
            departments.append(f"- {name}: {urljoin(url, href)}")
    
    if not departments:
        # 兜底：尝试常见列表结构
        for li in soup.select("li"):
            text = li.get_text(strip=True)
            if "学院" in text and len(text) < 40:
                departments.append(f"- {text}")
    
    return "\n".join(departments) if departments else ""


def crawl_seu_library() -> str:
    """抓取图书馆信息"""
    urls = [
        "http://www.lib.seu.edu.cn/",
        "http://www.lib.seu.edu.cn/list.php?fid=3",
    ]
    texts = []
    for url in urls:
        html = fetch_page(url)
        if html:
            text = extract_text_from_html(html)
            if text and len(text) > 100:
                texts.append(text)
        time.sleep(1)
    return "\n\n".join(texts)


def crawl_seu_career() -> str:
    """抓取就业指导中心信息"""
    url = "https://career.seu.edu.cn/"
    html = fetch_page(url)
    if not html:
        return ""
    return extract_text_from_html(html)


def crawl_seu_admission() -> str:
    """抓取招生信息"""
    url = "https://zsb.seu.edu.cn/"
    html = fetch_page(url)
    if not html:
        return ""
    return extract_text_from_html(html)


# ========== 预置关键信息（爬虫失败时的兜底数据） ==========

FALLBACK_DATA = """
【院系设置】

东南大学设有以下主要院系：
- 建筑学院
- 机械工程学院
- 能源与环境学院
- 信息科学与工程学院
- 土木工程学院
- 电子科学与工程学院
- 数学学院
- 计算机科学与工程学院
- 自动化学院
- 物理学院
- 生物科学与医学工程学院
- 材料科学与工程学院
- 人文学院
- 经济管理学院
- 电气工程学院
- 外国语学院
- 体育系
- 化学化工学院
- 交通学院
- 仪器科学与工程学院
- 艺术学院
- 法学院
- 医学院
- 公共卫生学院
- 网络空间安全学院
- 人工智能学院
- 未来技术学院
- 吴健雄学院（荣誉学院）

【招生信息】

东南大学招生咨询电话：025-83792452
本科招生网：https://zsb.seu.edu.cn/
研究生招生网：https://yzb.seu.edu.cn/

招生类型：
1. 普通高考招生
2. 强基计划
3. 高校专项计划
4. 保送生
5. 艺术类招生
6. 高水平运动队
7. 港澳台侨招生
8. 国际学生招生

【就业指导】

东南大学学生就业指导中心：
- 网址：https://career.seu.edu.cn/
- 地址：九龙湖校区大学生活动中心
- 电话：025-52090268

主要服务：
- 校园招聘会组织
- 就业信息发布
- 职业生涯规划指导
- 简历制作与面试辅导
- 就业手续办理

【体育设施】

九龙湖校区：
- 体育馆（含游泳馆、篮球馆、羽毛球馆）
- 室外田径场、足球场
- 网球场、排球场
- 健身房

四牌楼校区：
- 体育馆
- 田径场
- 各类球类场地

【校医院】

九龙湖校区校医院：
- 地址：桃园宿舍区附近
- 电话：025-52090123
- 服务时间：周一至周五 8:00-17:30（急诊24小时）

四牌楼校区校医院：
- 地址：校东宿舍区附近
- 电话：025-83792123

【校车服务】

东南大学校内班车（四牌楼↔九龙湖）：
- 工作日运行
- 需刷校园卡乘坐
- 时刻表可在"东大信息化"App查询

【奖学金与资助】

主要奖学金：
- 国家奖学金：8000元/年
- 国家励志奖学金：5000元/年
- 校长奖学金
- 三星奖学金、华为奖学金等社会捐赠奖学金

资助政策：
- 国家助学金
- 生源地信用助学贷款
- 勤工助学岗位
- 临时困难补助
- 绿色通道（新生入学）

【国际交流】

东南大学国际合作处：
- 网址：https://io.seu.edu.cn/
- 地址：四牌楼校区老图书馆

主要项目：
- 国家公派出国留学
- 校际交换生项目
- 暑期海外研修
- 中外合作办学项目

【校园网络】

SEU-WLAN：校园无线网络
- 覆盖所有校区主要区域
- 使用统一身份认证登录

有线网络：宿舍内可申请开通
- 资费：学生优惠套餐

网络报修：
- "东大信息化"微信公众号 → 网络报修
- 网络信息中心电话：025-83790808

【心理咨询】

东南大学心理健康教育中心：
- 九龙湖校区：大学生活动中心
- 四牌楼校区：行政楼
- 预约电话：025-52090206
- 24小时心理援助热线：400-161-9995
"""


def run_crawler(output_dir: str = "./data") -> dict:
    """
    运行爬虫，抓取东大官网数据
    返回 {文件名: 内容} 的字典
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    print("🕷️ 开始爬取东南大学官网数据...")
    
    # 1. 学校概况
    print("  📄 抓取学校概况...")
    overview = crawl_seu_overview()
    if overview:
        results["crawled_overview.txt"] = f"【学校概况】\n\n{overview[:5000]}"
    
    # 2. 院系设置
    print("  📄 抓取院系设置...")
    depts = crawl_seu_departments()
    if depts:
        results["crawled_departments.txt"] = f"【院系设置】\n\n{depts}"
    
    # 3. 图书馆
    print("  📄 抓取图书馆信息...")
    lib = crawl_seu_library()
    if lib:
        results["crawled_library.txt"] = f"【图书馆】\n\n{lib[:3000]}"
    
    # 4. 就业指导
    print("  📄 抓取就业信息...")
    career = crawl_seu_career()
    if career:
        results["crawled_career.txt"] = f"【就业指导】\n\n{career[:3000]}"
    
    # 5. 招生信息
    print("  📄 抓取招生信息...")
    admission = crawl_seu_admission()
    if admission:
        results["crawled_admission.txt"] = f"【招生信息】\n\n{admission[:3000]}"
    
    # 6. 兜底数据
    results["crawled_fallback.txt"] = FALLBACK_DATA
    
    # 保存文件
    for fname, content in results.items():
        fpath = os.path.join(output_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ 已保存: {fname} ({len(content)} 字符)")
    
    print(f"🎉 爬虫完成，共抓取 {len(results)} 个文件")
    return results


if __name__ == "__main__":
    run_crawler()
