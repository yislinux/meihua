import streamlit as st
from openai import OpenAI
from lunar_python import Solar
import datetime

# ================= 1. 页面配置 =================
st.set_page_config(
    page_title="AI全息梅花易数 Pro",
    page_icon="☯️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= 2. 样式美化 CSS =================
st.markdown("""
<style>
    /* 全局背景色微调 */
    .stApp { background-color: #faf9f6; }
    
    /* 卦爻容器 */
    .yao-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 6px 0;
        height: 24px;
    }
    /* 阳爻样式 (水墨黑) */
    .yang-yao {
        width: 80%;
        height: 16px;
        background-color: #2c3e50;
        border-radius: 4px;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.2);
    }
    /* 阴爻样式 */
    .yin-yao {
        display: flex;
        width: 80%;
        justify-content: space-between;
    }
    .yin-block {
        width: 44%;
        height: 16px;
        background-color: #2c3e50;
        border-radius: 4px;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.2);
    }
    /* 动爻高亮 (朱砂红) */
    .moving-yao .yang-yao,
    .moving-yao .yin-block {
        background-color: #e74c3c !important;
        box-shadow: 0 0 8px rgba(231, 76, 60, 0.6);
    }
    /* 卦名标题 */
    .gua-title {
        text-align: center;
        font-weight: 900;
        color: #2c3e50;
        margin-bottom: 15px;
        font-size: 1.3em;
        letter-spacing: 2px;
    }
    /* 信息摘要框 */
    .info-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 6px solid #e74c3c;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-top: 15px;
        font-size: 1em;
        line-height: 1.8;
        color: #34495e;
    }
    /* 分割线 */
    hr { border-top: 1px dashed #dcdde1; }
</style>
""", unsafe_allow_html=True)

# ================= 3. 基础数据 (八卦属性) =================
GUA_DATA = {
    1: {"name": "乾", "wx": "金", "binary": [1, 1, 1]},
    2: {"name": "兑", "wx": "金", "binary": [1, 1, 0]},
    3: {"name": "离", "wx": "火", "binary": [1, 0, 1]},
    4: {"name": "震", "wx": "木", "binary": [1, 0, 0]},
    5: {"name": "巽", "wx": "木", "binary": [0, 1, 1]},
    6: {"name": "坎", "wx": "水", "binary": [0, 1, 0]},
    7: {"name": "艮", "wx": "土", "binary": [0, 0, 1]},
    8: {"name": "坤", "wx": "土", "binary": [0, 0, 0]},
}

# ================= 4. 核心工具函数 =================

def get_gua_id_by_binary(bits):
    for gid, data in GUA_DATA.items():
        if data["binary"] == bits:
            return gid
    return 8

def draw_yao_html(is_yang, is_moving=False):
    moving_class = "moving-yao" if is_moving else ""
    if is_yang:
        return f"<div class='yao-container {moving_class}'><div class='yang-yao'></div></div>"
    else:
        return f"<div class='yao-container {moving_class}'><div class='yin-yao'><div class='yin-block'></div><div class='yin-block'></div></div></div>"

def get_api_client():
    """获取阿里云百炼 (DashScope) API配置"""
    api_key = None
    # 阿里云 DashScope 的兼容 OpenAI 接口地址
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    if "DASHSCOPE_API_KEY" in st.secrets:
        api_key = st.secrets["DASHSCOPE_API_KEY"]
    return api_key, base_url

def calculate_bazi(year, month, day, hour, minute):
    try:
        solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
        lunar = solar.getLunar()
        ba_zi_str = f"{lunar.getYearInGanZhi()}年 {lunar.getMonthInGanZhi()}月 {lunar.getDayInGanZhi()}日 {lunar.getTimeInGanZhi()}时"
        solar_str = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
        return ba_zi_str, solar_str
    except Exception as e:
        return f"计算出错: {str(e)}", ""

def get_beijing_time():
    utc_now = datetime.datetime.utcnow()
    return utc_now + datetime.timedelta(hours=8)

def get_time_gua_numbers(date_obj, time_obj):
    solar = Solar.fromYmdHms(date_obj.year, date_obj.month, date_obj.day, time_obj.hour, time_obj.minute, 0)
    lunar = solar.getLunar()
    
    dz_list = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    year_num = dz_list.index(lunar.getYearZhi()) + 1
    month_num = abs(lunar.getMonth())
    day_num = lunar.getDay()
    hour_num = dz_list.index(lunar.getTimeZhi()) + 1
    
    lunar_info = f"农历：{lunar.getYearInGanZhi()}年 {lunar.getMonthInChinese()}月 {lunar.getDayInChinese()} {lunar.getTimeInGanZhi()}时"
    return year_num, month_num, day_num, hour_num, lunar_info

# ================= 5. 侧边栏设置 =================
with st.sidebar:
    st.image("https://img.alicdn.com/tfs/TB1_ZXuNXXXXXatapXXXXXXXXXX-1024-1024.png", width=60) # 示意Icon
    st.title("⚙️ 模型设置")
    
    api_key, base_url = get_api_client()

    # Qwen 模型选择
    model_mapping = {
        "Qwen Plus (推荐, 均衡且强大)": "qwen3.5-plus",
        "Qwen Max (最强推理能力)": "qwen-max",
        "Qwen Turbo (极速响应)": "qwen-turbo"
    }
    model_display = st.selectbox(
        "选择千问模型",
        list(model_mapping.keys()),
        index=0
    )
    model_name = model_mapping[model_display]

    st.markdown("---")
    st.info("💡 **系统说明**：\n结合了数字起卦/时间起卦、八字命理与通义千问大模型的逻辑推理，提供全息的三维断卦体验。")

# ================= 6. 主界面逻辑 =================
st.title("☯️ AI 全息梅花易数 Pro")
st.markdown("<p style='color:#7f8c8d; font-size:1.1em;'>命理(八字) × 地理(方位) × 卦理(梅花) 三才合一排盘引擎</p>", unsafe_allow_html=True)

# 突出核心输入框
question = st.text_input("🔮 您心中所问何事？", placeholder="例如：近期换工作去北京发展是否顺利？请务必清晰描述...", help="心诚则灵，请具体描述所测之事")

# 使用 Tabs 优化界面层级
tab1, tab2 = st.tabs(["🔢 起卦设定 (必填)", "👤 命主信息 (提供可提高准确度)"])

current_bj_time = get_beijing_time()
div_date = current_bj_time.date()
div_time = current_bj_time.time()
num1, num2 = 3, 8

with tab1:
    qigua_method = st.radio("选择起卦法：", ["🔢 数字起卦 (触机灵动)", "🕒 时间起卦 (顺应天时)"], horizontal=True)
    
    if "数字起卦" in qigua_method:
        st.caption("请静心默念问题，凭第一直觉输入两个1-999的数字：")
        col_num1, col_num2 = st.columns(2)
        with col_num1:
            num1 = st.number_input("上卦数 (天)", min_value=1, value=3, step=1)
        with col_num2:
            num2 = st.number_input("下卦数 (地)", min_value=1, value=8, step=1)
    else:
        st.caption("默认取当前起心动念之时起卦（北京时间）：")
        col_d, col_t = st.columns(2)
        with col_d:
            div_date = st.date_input("占卜日期", value=current_bj_time.date())
        with col_t:
            div_time = st.time_input("占卜时间", value=current_bj_time.time(), step=60)

with tab2:
    st.caption("结合出生八字，可判断体用五行对命主的绝对吉凶。")
    col_y, col_m, col_d = st.columns(3)
    with col_y:
        year_list = list(range(1940, 2026))
        sel_year = st.selectbox("出生年 (公历)", year_list, index=year_list.index(1990))
    with col_m:
        sel_month = st.selectbox("出生月", list(range(1, 13)))
    with col_d:
        sel_day = st.selectbox("出生日", list(range(1, 32)))

    col_t, col_p = st.columns([1, 2])
    with col_t:
        t = st.time_input("出生时间", value=None)
    with col_p:
        birth_place = st.text_input(" 出生地点", placeholder="例如：北京市朝阳区")
    
    user_bazi = "未提供完整时间"
    user_solar_str = ""
    is_date_valid = True

    try:
        temp_date = datetime.date(sel_year, sel_month, sel_day)
    except ValueError:
        is_date_valid = False
        st.error("⚠️ 日期错误：不存在该日期。")

    if is_date_valid and t is not None:
        user_bazi, user_solar_str = calculate_bazi(sel_year, sel_month, sel_day, t.hour, t.minute)
        st.success(f"📜 命主八字：**{user_bazi}**")

# --- 按钮区域 ---
st.markdown("<br>", unsafe_allow_html=True)
start_divination = st.button("🚀 开始全息排盘与AI解卦", use_container_width=True, type="primary")

if start_divination:
    if not api_key:
        st.error("请在左侧侧边栏配置 DashScope API Key！")
        st.stop()
    if not question:
        st.warning("请填写您要占卜的事项！")
        st.stop()

    # ================= 排盘逻辑计算 =================
    qigua_info = "" 
    
    if "数字起卦" in qigua_method:
        shang_num = num1 % 8 or 8
        xia_num = num2 % 8 or 8
        dong_yao = (num1 + num2) % 6 or 6
        qigua_info = f"【数字起卦】上数：{num1}，下数：{num2}"
    else:
        y_n, m_n, d_n, h_n, lunar_str = get_time_gua_numbers(div_date, div_time)
        shang_num = (y_n + m_n + d_n) % 8 or 8
        sum_xia = y_n + m_n + d_n + h_n
        xia_num = sum_xia % 8 or 8
        dong_yao = sum_xia % 6 or 6
        qigua_info = f"【时间起卦】{lunar_str} <br>(年{y_n}+月{m_n}+日{d_n}=上卦{shang_num}，加时{h_n}=下卦{xia_num}/动爻{dong_yao})"

    # 本、互、变卦计算
    ben_shang = GUA_DATA[shang_num]
    ben_xia = GUA_DATA[xia_num]
    ben_yao_list = ben_xia["binary"] + ben_shang["binary"]

    bian_yao_list = ben_yao_list.copy()
    idx = dong_yao - 1
    bian_yao_list[idx] = 1 - bian_yao_list[idx]

    bian_xia_id = get_gua_id_by_binary(bian_yao_list[0:3])
    bian_shang_id = get_gua_id_by_binary(bian_yao_list[3:6])
    bian_shang = GUA_DATA[bian_shang_id]
    bian_xia = GUA_DATA[bian_xia_id]

    hu_xia_id = get_gua_id_by_binary(ben_yao_list[1:4])
    hu_shang_id = get_gua_id_by_binary(ben_yao_list[2:5])
    hu_xia = GUA_DATA[hu_xia_id]
    hu_shang = GUA_DATA[hu_shang_id]

    if dong_yao > 3:
        ti_gua, yong_gua, bian_res_gua = ben_xia, ben_shang, bian_shang
    else:
        ti_gua, yong_gua, bian_res_gua = ben_shang, ben_xia, bian_xia

    # ================= 结果展示 =================
    st.markdown("---")
    st.markdown("### 📊 易理排盘结果")

    g1, g2, g3, g4 = st.columns([2, 2, 0.5, 2])
    with g1:
        st.markdown(f"<div class='gua-title'>本卦<br><span style='font-size:0.7em;color:#7f8c8d'>{ben_shang['name']}{ben_xia['name']}</span></div>", unsafe_allow_html=True)
        for i in range(5, -1, -1): st.markdown(draw_yao_html(ben_yao_list[i] == 1, i == idx), unsafe_allow_html=True)
    with g2:
        st.markdown(f"<div class='gua-title'>互卦<br><span style='font-size:0.7em;color:#7f8c8d'>{hu_shang['name']}{hu_xia['name']}</span></div>", unsafe_allow_html=True)
        hu_full = hu_xia["binary"] + hu_shang["binary"]
        for i in range(5, -1, -1): st.markdown(draw_yao_html(hu_full[i] == 1, False), unsafe_allow_html=True)
    with g3:
        st.markdown("<div style='text-align:center;font-size:2.5em;padding-top:40px;color:#bdc3c7;'>➜</div>", unsafe_allow_html=True)
    with g4:
        st.markdown(f"<div class='gua-title'>变卦<br><span style='font-size:0.7em;color:#7f8c8d'>{bian_shang['name']}{bian_xia['name']}</span></div>", unsafe_allow_html=True)
        for i in range(5, -1, -1): st.markdown(draw_yao_html(bian_yao_list[i] == 1, i == idx), unsafe_allow_html=True)

    st.markdown(f"""
    <div class='info-box'>
        <b>📋 起卦机缘：</b>{qigua_info}<br>
        <b>🎯 核心体用：</b>体卦为主（<b>{ti_gua['name']}{ti_gua['wx']}</b>） | 用卦为客（<b>{yong_gua['name']}{yong_gua['wx']}</b>）<br>
        <b>✨ 变化之机：</b>第 <b>{dong_yao}</b> 爻发动，变出 <b>{bian_res_gua['name']}{bian_res_gua['wx']}</b>
    </div>
    """, unsafe_allow_html=True)

    # ================= AI 解读 =================
    bazi_prompt_part = f"""
【命主八字参数】：
- 公历时间：{user_solar_str}
- 八字排盘：{user_bazi}
- 出生地点：{birth_place if birth_place else "未提供"} 
- 校验指令：请判断日主强弱及喜用神。如果“体卦”五行是八字的喜用神，则吉上加吉；若是忌神，则吉处藏凶。
""" if is_date_valid and t is not None else "【命主信息】：用户未提供详细生辰，请仅根据梅花易数卦象法则进行推演。"

    prompt = f"""
# Role: 顶级易学大师与战略决策顾问
你是一位精通《梅花易数》与《子平真诠》的易学宗师。你语言精炼、直断吉凶、拒绝模棱两可，善于结合卦象给出具象化的现代生活指导。

# Context (用户背景)
【用户提问】："{question}"
{bazi_prompt_part}

# Data (卦象数据)
- **本卦 (现状)**：{ben_shang['name']} (上{ben_shang['wx']} 下{ben_xia['wx']})
- **互卦 (过程)**：{hu_shang['name']} (上{hu_shang['wx']} 下{hu_xia['wx']})
- **变卦 (结果)**：{bian_shang['name']} (上{bian_shang['wx']} 下{bian_xia['wx']})
- **核心判定**：体卦：{ti_gua['name']} (属{ti_gua['wx']}) | 用卦：{yong_gua['name']} (属{yong_gua['wx']}) | 动爻：第{dong_yao}爻

# Workflow (推演逻辑，请严格执行)
1. 梅花直断：依据【体用生克】定基调：用生体(大吉)、体克用(小吉/需努力)、用克体(凶/受阻)、体生用(泄气/损耗)、比和(吉/顺遂)。分析动爻带来的变卦生克。
2. 八字修正：若提供了八字，体卦五行是喜用则加分，忌神则减分。
3. 万物类象：根据卦象（如乾为领导、金；坎为水、险）结合问题推导具体人、事、物特征。

# Output Format (严格遵循 Markdown，必须包含以下模块)
## 🎯 断卦结论
*(直接给出吉凶判断，例如：“大吉，得贵人相助，此事必成。”)*

## 📜 深度解析
- **当前局势（本卦）**：*(解读体用关系，当前阻力或助力)*
- **过程隐情（互卦）**：*(解读中间过程、暗中运作的力量)*
- **最终结局（变卦）**：*(最终走向与定论)*

## 🔍 类象与应期
- **应期推断**：*(推断可能发生转折的月份、日期或节气)*
- **关键特征**：*(如涉及人物的长相、性格，或方位的利弊)*

## 💡 锦囊妙计
*(给出 3 条极具操作性的具体行动建议)*
"""

    st.markdown("<br>### 🤖 通义千问 AI 解卦", unsafe_allow_html=True)
    res_box = st.empty()
    full_response = ""

    try:
        # 使用兼容 OpenAI 格式的调用方式
        client = OpenAI(api_key=api_key, base_url=base_url)
        with st.spinner("AI 宗师正在起念观卦，推演天机..."):
            stream = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "你是通义千问驱动的易学宗师。你的回答需要专业、神秘但极其具有实用指导意义。"},
                    {"role": "user", "content": prompt}
                ],
                stream=True,
                temperature=0.7,
                top_p=0.8
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    res_box.info(full_response + " ▌", icon="✨")

            # 最终渲染去掉光标
            res_box.info(full_response, icon="✨")

    except Exception as e:
        st.error(f"API 请求发生错误: {e}")
        st.caption("提示：请检查 DashScope API Key 是否有效，账户是否开通了对应的 Qwen 模型权限。")
