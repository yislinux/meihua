import streamlit as st
from openai import OpenAI
from lunar_python import Solar
import datetime

# ================= 1. 页面配置 =================
st.set_page_config(
    page_title="AI梅花易数排盘 Pro",
    page_icon="☯️",
    layout="wide"
)

# ================= 2. 样式美化 CSS =================
st.markdown("""
<style>
    /* 卦爻容器 */
    .yao-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 4px 0;
        height: 26px;
    }
    /* 阳爻样式 */
    .yang-yao {
        width: 100%;
        height: 18px;
        background-color: #333;
        border-radius: 3px;
    }
    /* 阴爻样式 */
    .yin-yao {
        display: flex;
        width: 100%;
        justify-content: space-between;
    }
    .yin-block {
        width: 45%;
        height: 18px;
        background-color: #777;
        border-radius: 3px;
    }
    /* 动爻高亮 (红色) */
    .moving-yao .yang-yao,
    .moving-yao .yin-block {
        background-color: #C0392B !important;
        box-shadow: 0 0 5px rgba(192, 57, 43, 0.5);
    }
    /* 卦名标题 */
    .gua-title {
        text-align: center;
        font-weight: bold;
        color: #444;
        margin-bottom: 8px;
        font-size: 1.1em;
    }
    /* 信息摘要框 */
    .info-box {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #ff4b4b;
        margin-top: 10px;
        font-size: 0.95em;
        line-height: 1.6;
    }
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
    """根据二进制列表查找卦ID"""
    for gid, data in GUA_DATA.items():
        if data["binary"] == bits:
            return gid
    return 8

def draw_yao_html(is_yang, is_moving=False):
    """绘制单根爻的HTML"""
    moving_class = "moving-yao" if is_moving else ""
    if is_yang:
        return f"""<div class='yao-container {moving_class}'><div class='yang-yao'></div></div>"""
    else:
        return f"""<div class='yao-container {moving_class}'><div class='yin-yao'><div class='yin-block'></div><div class='yin-block'></div></div></div>"""

def get_api_client():
    """获取API配置"""
    api_key = None
    base_url = "https://api.deepseek.com"
    if "DEEPSEEK_API_KEY" in st.secrets:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
        if "DEEPSEEK_BASE_URL" in st.secrets:
            base_url = st.secrets["DEEPSEEK_BASE_URL"]
    return api_key, base_url

def calculate_bazi(year, month, day, hour, minute):
    """根据公历计算八字，并返回格式化字符串"""
    try:
        # 建立阳历对象
        solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
        # 转阴历
        lunar = solar.getLunar()
        
        # 获取干支
        gan_zhi_year = lunar.getYearInGanZhi()
        gan_zhi_month = lunar.getMonthInGanZhi()
        gan_zhi_day = lunar.getDayInGanZhi()
        gan_zhi_time = lunar.getTimeInGanZhi()
        
        ba_zi_str = f"{gan_zhi_year}年 {gan_zhi_month}月 {gan_zhi_day}日 {gan_zhi_time}时"
        
        # 格式化公历显示为纯数字: YYYY-MM-DD HH:mm
        solar_str = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
        
        return ba_zi_str, solar_str
    except Exception as e:
        return f"计算出错: {str(e)}", ""

def get_beijing_time():
    """获取当前北京时间 (UTC+8)"""
    # 获取 UTC 时间
    utc_now = datetime.datetime.utcnow()
    # 加 8 小时
    beijing_now = utc_now + datetime.timedelta(hours=8)
    return beijing_now

def get_time_gua_numbers(date_obj, time_obj):
    """
    根据公历时间返回梅花易数时间起卦所需的数值：
    年数(地支)、月数(农历)、日数(农历)、时数(地支)
    """
    solar = Solar.fromYmdHms(date_obj.year, date_obj.month, date_obj.day, time_obj.hour, time_obj.minute, 0)
    lunar = solar.getLunar()
    
    # 1. 年数 (子1, 丑2... 亥12)
    dz_list = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    year_dz = lunar.getYearZhi()
    year_num = dz_list.index(year_dz) + 1
    
    # 2. 月数 (农历月份，闰月取绝对值)
    month_num = abs(lunar.getMonth())
    
    # 3. 日数 (农历日期)
    day_num = lunar.getDay()
    
    # 4. 时数 (子1, 丑2... 亥12)
    time_dz = lunar.getTimeZhi()
    hour_num = dz_list.index(time_dz) + 1
    
    # 返回四者和阴历详细信息（用于展示）
    lunar_info = f"农历：{lunar.getYearInGanZhi()}年 {lunar.getMonthInChinese()}月 {lunar.getDayInChinese()} {lunar.getTimeInGanZhi()}时"
    
    return year_num, month_num, day_num, hour_num, lunar_info

# ================= 5. 侧边栏设置 =================
with st.sidebar:
    st.title("🔮 设置")
    
    api_key, base_url = get_api_client()

    if not api_key:
        st.warning("请配置 API Key")
        api_key = st.text_input("DeepSeek API Key", type="password")
        base_url = st.text_input("API Base URL", value="https://api.deepseek.com")

    # 模型选择
    model_mapping = {
        "DeepSeek-R1 (推理模型)": "deepseek-R1",
        "DeepSeek-V3 (通用模型)": "deepseek-chat"
    }
    model_display = st.selectbox(
        "选择模型",
        list(model_mapping.keys()),
        index=0,
        help="推荐使用 reasoner 模型以获得更强的逻辑推理能力"
    )
    model_name = model_mapping[model_display]

    st.markdown("---")
    st.info("💡 **说明**：\n本系统结合了数字起卦（触机）、八字命理（时间）与地理方位（空间），提供三维一体的AI解读。")

# ================= 6. 主界面逻辑 =================
st.title("☯️ AI 全息梅花易数")
st.caption("命理(八字) + 地理(方位) + 卦理(梅花) 三才合一排盘")

# --- 第一部分：起卦方式选择 ---
st.subheader("1. 起卦设定")

qigua_method = st.radio(
    "选择起卦法：",
    ["🔢 数字起卦 (触机灵动)", "🕒 时间起卦 (顺应天时)"],
    horizontal=True
)

# 初始化变量
num1, num2 = 3, 8 
# 获取当前北京时间
current_bj_time = get_beijing_time()
div_date = current_bj_time.date()
div_time = current_bj_time.time()

# 根据选择显示不同的输入框
if "数字起卦" in qigua_method:
    col_num1, col_num2 = st.columns(2)
    with col_num1:
        num1 = st.number_input("上卦数 (天)", min_value=1, value=3, step=1, help="心中想到的第一个数字")
    with col_num2:
        num2 = st.number_input("下卦数 (地)", min_value=1, value=8, step=1, help="心中想到的第二个数字")
else:
    col_d, col_t = st.columns(2)
    with col_d:
        # 默认值使用当前北京时间
        div_date = st.date_input("占卜日期", value=current_bj_time.date())
    with col_t:
        # step=60 去掉秒的显示，保持界面整洁
        div_time = st.time_input("占卜时间", value=current_bj_time.time(), step=60, help="默认为当前北京时间")

question = st.text_input("🔮 占卜事项", placeholder="例如：近期换工作去北京发展是否顺利？")

# --- 第二部分：命主信息 ---
st.subheader("2. 命主信息 (八字与空间)")
with st.expander("点击展开/折叠 个人详细信息设置", expanded=True):
    # 使用 3列布局选择 年、月、日
    col_y, col_m, col_d = st.columns([1, 1, 1])
    
    with col_y:
        # 年份：从 1940 到 2025，默认选 1990
        year_list = list(range(1940, 2026))
        sel_year = st.selectbox("出生年", year_list, index=year_list.index(1990))
        
    with col_m:
        # 月份：1-12
        sel_month = st.selectbox("出生月", list(range(1, 13)))
        
    with col_d:
        # 日期：1-31
        sel_day = st.selectbox("出生日", list(range(1, 32)))

    # 时间与地点
    col_t, col_p = st.columns([1, 2])
    with col_t:
        t = st.time_input("出生时间", value=None, help="请选择出生时间（24小时制）")
    with col_p:
        birth_place = st.text_input(" 出生地点", placeholder="例如：北京市朝阳区", help="用于结合地理五行分析")
    
    # 实时计算八字预览
    user_bazi = "等待填写时间..."
    user_solar_str = ""
    is_date_valid = True

    # 简单的日期有效性检查
    try:
        temp_date = datetime.date(sel_year, sel_month, sel_day)
    except ValueError:
        is_date_valid = False
        st.error(f"日期错误：{sel_year}年{sel_month}月 没有 {sel_day}日")

    if is_date_valid and t is not None:
        user_bazi, user_solar_str = calculate_bazi(sel_year, sel_month, sel_day, t.hour, t.minute)
        st.success(f" 八字排盘：**{user_bazi}**")
        st.caption(f"公历时间：{user_solar_str}")
    elif t is None:
        st.info("请补充出生时间以生成八字")

# --- 按钮区域 ---
start_divination = st.button("🚀 开始全息排盘与解卦", use_container_width=True)

if start_divination:
    if not api_key:
        st.error("请先配置 API Key！")
        st.stop()
    if not question:
        st.warning("请填写占卜事项。")
        st.stop()

    # ================= 排盘逻辑计算 =================
    qigua_info = "" 
    
    if "数字起卦" in qigua_method:
        # 数字起卦算法
        shang_num = num1 % 8 or 8
        xia_num = num2 % 8 or 8
        total_sum = num1 + num2
        dong_yao = total_sum % 6 or 6
        qigua_info = f"【数字起卦】上数：{num1}，下数：{num2}"
    else:
        # 时间起卦算法
        # 1. 获取农历参数
        y_n, m_n, d_n, h_n, lunar_str = get_time_gua_numbers(div_date, div_time)
        
        # 2. 梅花易数时间起卦公式
        # 上卦 = (年+月+日) / 8
        sum_shang = y_n + m_n + d_n
        shang_num = sum_shang % 8 or 8
        
        # 下卦 = (年+月+日+时) / 8
        sum_xia = y_n + m_n + d_n + h_n
        xia_num = sum_xia % 8 or 8
        
        # 动爻 = (年+月+日+时) / 6
        dong_yao = sum_xia % 6 or 6
        
        qigua_info = f"【时间起卦】{lunar_str} (年{y_n}+月{m_n}+日{d_n}=上卦{shang_num}，加时{h_n}=下卦{xia_num}/动爻{dong_yao})"

    # 本卦
    ben_shang = GUA_DATA[shang_num]
    ben_xia = GUA_DATA[xia_num]
    ben_yao_list = ben_xia["binary"] + ben_shang["binary"]

    # 变卦 (动爻反转)
    bian_yao_list = ben_yao_list.copy()
    idx = dong_yao - 1
    bian_yao_list[idx] = 1 - bian_yao_list[idx]

    bian_xia_id = get_gua_id_by_binary(bian_yao_list[0:3])
    bian_shang_id = get_gua_id_by_binary(bian_yao_list[3:6])
    bian_shang = GUA_DATA[bian_shang_id]
    bian_xia = GUA_DATA[bian_xia_id]

    # 互卦 (234爻做下互, 345爻做上互)
    hu_xia_bits = ben_yao_list[1:4] 
    hu_shang_bits = ben_yao_list[2:5]
    hu_xia_id = get_gua_id_by_binary(hu_xia_bits)
    hu_shang_id = get_gua_id_by_binary(hu_shang_bits)
    hu_xia = GUA_DATA[hu_xia_id]
    hu_shang = GUA_DATA[hu_shang_id]

    # 体用判断
    if dong_yao > 3: # 动在上卦
        ti_gua = ben_xia
        yong_gua = ben_shang
        bian_res_gua = bian_shang
    else: # 动在下卦
        ti_gua = ben_shang
        yong_gua = ben_xia
        bian_res_gua = bian_xia

    # ================= 结果展示 =================
    st.markdown("---")
    st.markdown("### 📊 排盘结果")

    # 4列布局：本 -> 互 -> 箭头 -> 变
    g1, g2, g3, g4 = st.columns([2, 2, 0.5, 2])

    with g1:
        st.markdown(f"<div class='gua-title'>本卦<br>{ben_shang['name']}{ben_xia['name']}</div>", unsafe_allow_html=True)
        for i in range(5, -1, -1):
            st.markdown(draw_yao_html(ben_yao_list[i] == 1, i == idx), unsafe_allow_html=True)

    with g2:
        st.markdown(f"<div class='gua-title'>互卦<br>{hu_shang['name']}{hu_xia['name']}</div>", unsafe_allow_html=True)
        hu_full = hu_xia["binary"] + hu_shang["binary"]
        for i in range(5, -1, -1):
            st.markdown(draw_yao_html(hu_full[i] == 1, False), unsafe_allow_html=True)

    with g3:
        st.markdown("<div style='text-align:center;font-size:2em;padding-top:50px;color:#999;'>➜</div>", unsafe_allow_html=True)

    with g4:
        st.markdown(f"<div class='gua-title'>变卦<br>{bian_shang['name']}{bian_xia['name']}</div>", unsafe_allow_html=True)
        for i in range(5, -1, -1):
            st.markdown(draw_yao_html(bian_yao_list[i] == 1, i == idx), unsafe_allow_html=True)

    # 详细文字信息
    st.markdown(f"""
    <div class='info-box'>
        <b>📋 起卦信息：</b>{qigua_info}<br><br>
        <b>🎯 核心关系：</b><br>
        • 体卦 (自己/主体)：<b>{ti_gua['name']} ({ti_gua['wx']})</b><br>
        • 用卦 (对方/环境)：<b>{yong_gua['name']} ({yong_gua['wx']})</b><br>
        • 动爻：第 <b>{dong_yao}</b> 爻<br>
        • 变卦 (最终结果)：{bian_res_gua['name']} ({bian_res_gua['wx']})
    </div>
    """, unsafe_allow_html=True)

    # ================= AI 解读 =================
    # 构建 Bazi 部分提示词（保持原有逻辑，稍作修饰）
    bazi_prompt_part = ""
    if is_date_valid and t is not None:
        bazi_prompt_part = f"""
【命主八字参数】：
- 公历时间：{user_solar_str}
- 八字排盘：{user_bazi}
- 出生地点：{birth_place if birth_place else "未提供"} 
- **校验指令**：请判断日主强弱及喜用神。如果“体卦”五行是八字的喜用神，则吉上加吉；若是忌神，则吉处藏凶。
"""
    else:
        bazi_prompt_part = "【命主信息】：用户未提供详细生辰，请仅根据梅花易数卦象法则进行推演。"

    # ---------------------------------------------------------
    # 核心 Prompt 优化版
    # ---------------------------------------------------------
    prompt = f"""
# Role: 高级易学决策顾问
你是一位精通《梅花易数》与《子平真诠》的实战派易学专家。你的风格是**直断吉凶、拒绝模棱两可、提供具体行动指南**。

# Context (用户背景)
【用户提问】："{question}"
{bazi_prompt_part}

# Data (卦象数据)
- **本卦 (现状)**：{ben_shang['name']} (上{ben_shang['wx']} 下{ben_xia['wx']}) -> 互动关系：{ben_shang['wx']}{ben_xia['wx']}
- **互卦 (过程)**：{hu_shang['name']} (上{hu_shang['wx']} 下{hu_xia['wx']}) -> 事情发展的隐情或中间过程
- **变卦 (结果)**：{bian_shang['name']} (上{bian_shang['wx']} 下{bian_xia['wx']}) -> 最终走向
- **核心判定点**：
   - 体卦：{ti_gua['name']} (五行属{ti_gua['wx']}) | 用卦：{yong_gua['name']} (五行属{yong_gua['wx']})
   - 动爻：第{dong_yao}爻

# Workflow (推演逻辑)
请严格遵循以下步骤进行思考和输出，不要输出思考过程，直接输出结果：

1.  **梅花直断**：
    - 依据【体用生克】定基调：用生体(大吉/易成)、体克用(小吉/需努力)、用克体(凶/受阻)、体生用(泄气/损耗)、比和(吉/顺遂)。
    - 依据【动爻】看变卦五行对体卦的生克变化，判断结局。
2.  **八字修正** (如有)：
    - 分析八字喜忌，若体卦五行为喜用，成功率+20%；若为忌神，成功率-20%或提示副作用。
3.  **类象推演**：
    - 根据卦名（如乾为马、金、刚健；坎为水、险、车）结合用户问题，推导出具体的“现象”或“人物”。

# Output Format (输出要求 - 必须严格执行 Markdown)

##  核心结论
*(此处必须给出一个直观的分数 0-100分，并用一句话回答用户提问，例如：“75分，吉，事情前期有波折但最终能成。”)*

##  深度解析
**1. 现状与挑战（本卦）：**
*(解读本卦体用关系，描述当前局势)*

**2. 发展与隐情（互卦）：**
*(解读互卦，指出过程中可能遇到的干扰、中间人或突发状况)*

**3. 最终走向（变卦）：**
*(解读变卦，结合八字喜忌，给出最终定论)*

##  应期与现象
- **关键时间点**：*(推断可能发生转折或结果的月份/日期/时辰，依据五行旺相推算)*
- **相关类象**：*(描述可能出现的人、事、物特征，例如“与一位属水的女性有关”或“注意北方的机会”)*

##  决策建议
*(给出 3 条具体的、可执行的建议，语气要笃定)*
1. ...
2. ...
3. ...
"""

    st.markdown("### 🤖 AI 全息解读")
    res_box = st.empty()
    full_response = ""

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一位严谨、专业的易学决策顾问，擅长将古籍智慧转化为现代行动指南。"},
                {"role": "user", "content": prompt}
            ],
            stream=True,
            temperature=0.7, # 稍微降低温度，减少胡编乱造，增加逻辑性
            presence_penalty=0.3 # 鼓励输出更多样化的词汇
        )

        for chunk in stream:
            if not chunk.choices: continue
            delta = chunk.choices[0].delta
            
            # 兼容 reasoning_content (如果使用 deepseek-reasoner)
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                pass 
            
            if delta.content:
                full_response += delta.content
                res_box.markdown(full_response + "▌")

        res_box.markdown(full_response)

    except Exception as e:
        st.error(f"AI 请求发生错误: {e}")
