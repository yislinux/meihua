import streamlit as st
from openai import OpenAI
# 引入农历转换库
from lunar_python import Solar

# ================= 1. 页面配置 =================
st.set_page_config(
    page_title="AI梅花易数排盘 Pro",
    page_icon="☯️",
    layout="wide"
)

# ================= 2. 朴素化 CSS =================
st.markdown("""
<style>
    .yao-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 4px 0;
        height: 26px;
    }
    .yang-yao {
        width: 100%;
        height: 18px;
        background-color: #333;
        border-radius: 3px;
    }
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
    .moving-yao .yang-yao,
    .moving-yao .yin-block {
        background-color: #C0392B !important; /* 动爻标红 */
        box-shadow: none;
    }
    .gua-title {
        text-align: center;
        font-weight: bold;
        color: #444;
        margin-bottom: 8px;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #ff4b4b;
    }
</style>
""", unsafe_allow_html=True)

# ================= 3. 基础数据 =================
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

# ================= 4. 工具函数 =================
def get_gua_id_by_binary(bits):
    for gid, data in GUA_DATA.items():
        if data["binary"] == bits:
            return gid
    return 8

def draw_yao_html(is_yang, is_moving=False):
    moving_class = "moving-yao" if is_moving else ""
    if is_yang:
        return f"""<div class='yao-container {moving_class}'><div class='yang-yao'></div></div>"""
    else:
        return f"""<div class='yao-container {moving_class}'><div class='yin-yao'><div class='yin-block'></div><div class='yin-block'></div></div></div>"""

def get_api_client():
    api_key = None
    base_url = "https://api.deepseek.com"
    if "DEEPSEEK_API_KEY" in st.secrets:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
        if "DEEPSEEK_BASE_URL" in st.secrets:
            base_url = st.secrets["DEEPSEEK_BASE_URL"]
    return api_key, base_url

def calculate_bazi(year, month, day, hour, minute):
    """根据公历计算八字"""
    try:
        solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
        lunar = solar.getLunar()
        ba_zi = convert_bazi_format(lunar)
        return ba_zi, f"{year}-{month}-{day} {hour}:{minute}"
    except Exception as e:
        return f"计算出错: {str(e)}", ""

def convert_bazi_format(lunar):
    """格式化八字输出"""
    gan_zhi_year = lunar.getYearInGanZhi()
    gan_zhi_month = lunar.getMonthInGanZhi()
    gan_zhi_day = lunar.getDayInGanZhi()
    gan_zhi_time = lunar.getTimeInGanZhi()
    
    # 简单的五行对应（可让AI做更深层分析，这里只做基础展示）
    return f"{gan_zhi_year}年 {gan_zhi_month}月 {gan_zhi_day}日 {gan_zhi_time}时"

# ================= 5. 侧边栏 =================
with st.sidebar:
    st.title("🔮 全息设置")
    
    api_key, base_url = get_api_client()

    if not api_key:
        st.warning("未检测到 Secrets，请手动输入 Key")
        api_key = st.text_input("DeepSeek API Key", type="password")
        base_url = st.text_input("API Base URL", value="https://api.deepseek.com")

    model_name = st.selectbox(
        "选择模型",
        ["deepseek-R1", "deepseek-chat"], # 推荐reasoner
        index=0,
        help="reasoner模型通过思维链能更好地推演复杂的卦象逻辑"
    )

    st.markdown("---")
    st.info("💡 说明：\n此版本结合了出生时间（八字命理）、出生地点（空间方位）与数字起卦（时空触机），进行多维度的综合排盘。")

# ================= 6. 主界面 =================
st.title("☯️ AI 全息梅花易数")
st.caption("命理(八字) + 地理(方位) + 卦理(梅花) 三才合一")

# --- 第一部分：起卦数字 ---
st.subheader("1. 触机起卦 (数字)")
col_num1, col_num2 = st.columns(2)
with col_num1:
    num1 = st.number_input("上卦数 (天)", min_value=1, value=3, step=1, help="心中想到的第一个数字")
with col_num2:
    num2 = st.number_input("下卦数 (地)", min_value=1, value=8, step=1, help="心中想到的第二个数字")

question = st.text_input("🔮 占卜事项", placeholder="例如：近期换工作去北京发展是否顺利？")

# --- 第二部分：个人信息 (折叠区域) ---
st.subheader("2. 命主信息 (八字与空间)")
with st.expander("点击展开/折叠 个人详细信息设置", expanded=True):
    col_date, col_time = st.columns(2)
    with col_date:
        d = st.date_input("出生日期 (公历)", value=None, min_value=None, max_value=None)
    with col_time:
        t = st.time_input("出生时间", value=None)
        
    birth_place = st.text_input("📍 出生地点", placeholder="例如：中国山东济南 / 美国纽约", help="出生地影响真太阳时及地理五行气场")
    
    # 实时计算八字预览
    user_bazi = "未完整填写日期时间"
    user_solar_str = ""
    if d and t:
        user_bazi, user_solar_str = calculate_bazi(d.year, d.month, d.day, t.hour, t.minute)
        st.success(f"📅 您的八字排盘：**{user_bazi}**")
    elif d or t:
        st.caption("请补全日期和时间以计算八字")

# --- 开始按钮 ---
start_divination = st.button("🚀 开始全息排盘与解卦", use_container_width=True)

if start_divination:
    if not api_key:
        st.error("请先配置 API Key！")
        st.stop()
    if not question:
        st.warning("请填写占卜事项，由于有了八字信息，问题越具体越好。")
        st.stop()

    # ================= 数理起卦逻辑 =================
    shang_num = num1 % 8 or 8
    xia_num = num2 % 8 or 8
    total_sum = num1 + num2
    dong_yao = total_sum % 6 or 6

    ben_shang = GUA_DATA[shang_num]
    ben_xia = GUA_DATA[xia_num]
    ben_yao_list = ben_xia["binary"] + ben_shang["binary"]

    # 变卦逻辑
    bian_yao_list = ben_yao_list.copy()
    idx = dong_yao - 1
    bian_yao_list[idx] = 1 - bian_yao_list[idx] # 动爻反转

    bian_xia_id = get_gua_id_by_binary(bian_yao_list[0:3])
    bian_shang_id = get_gua_id_by_binary(bian_yao_list[3:6])

    bian_shang = GUA_DATA[bian_shang_id]
    bian_xia = GUA_DATA[bian_xia_id]

    # 体用判断
    # 动爻在1,2,3 -> 下卦变，上卦为体，下卦为用
    # 动爻在4,5,6 -> 上卦变，下卦为体，上卦为用
    if dong_yao > 3:
        ti_gua = ben_xia
        yong_gua = ben_shang
        bian_res_gua = bian_shang # 变卦中变的那个卦
    else:
        ti_gua = ben_shang
        yong_gua = ben_xia
        bian_res_gua = bian_xia

    # 互卦逻辑 (梅花易数重要参考)
    # 互卦：由本卦的234爻组成下互，345爻组成上互
    # list index: 0(初),1(二),2(三),3(四),4(五),5(上)
    hu_xia_bits = ben_yao_list[1:4] # 2,3,4
    hu_shang_bits = ben_yao_list[2:5] # 3,4,5
    hu_xia_id = get_gua_id_by_binary(hu_xia_bits)
    hu_shang_id = get_gua_id_by_binary(hu_shang_bits)
    hu_xia = GUA_DATA[hu_xia_id]
    hu_shang = GUA_DATA[hu_shang_id]

    # ================= 展示卦象 =================
    st.markdown("---")
    st.markdown("### 📊 排盘结果")

    # 使用 columns 布局卦象
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
         st.markdown("<div style='text-align:center;font-size:2em;padding-top:50px;'>➜</div>", unsafe_allow_html=True)

    with g4:
        st.markdown(f"<div class='gua-title'>变卦<br>{bian_shang['name']}{bian_xia['name']}</div>", unsafe_allow_html=True)
        for i in range(5, -1, -1):
            st.markdown(draw_yao_html(bian_yao_list[i] == 1, i == idx), unsafe_allow_html=True)

    # 结果摘要
    st.markdown(f"""
    <div class='info-box'>
        <b>体卦（自己/现状）：</b>{ti_gua['name']} ({ti_gua['wx']}) <br>
        <b>用卦（人/事/环境）：</b>{yong_gua['name']} ({yong_gua['wx']}) <br>
        <b>互卦（过程/隐情）：</b>{hu_shang['name']}{hu_xia['name']} <br>
        <b>变卦（结果/趋势）：</b>{bian_res_gua['name']} ({bian_res_gua['wx']}) <br>
        <b>动爻：</b>第 {dong_yao} 爻
    </div>
    """, unsafe_allow_html=True)

    # ================= AI 解卦 Prompt 构建 =================
    bazi_info = ""
    if d and t:
        bazi_info = f"""
【命主信息】：
- 出生公历：{user_solar_str}
- 出生地点：{birth_place if birth_place else "未提供"} (请考虑出生地的地理五行属性对八字强弱的影响)
- 八字排盘：{user_bazi}
- 命理要求：请分析八字的日主强弱、喜用神，并以此为基础，判断卦象中"体卦"五行是否为命主喜用。
"""
    else:
        bazi_info = "【命主信息】：用户未提供详细八字，仅按纯卦象分析。"

    prompt = f"""
你是一位精通《梅花易数》、《渊海子平》与现代地理命理学的国学大师。请针对用户问题进行综合排盘解读。

【用户提问】：{question}

{bazi_info}

【卦象数据】：
1. **本卦** (开始)：上{ben_shang['name']}({ben_shang['wx']}) 下{ben_xia['name']}({ben_xia['wx']})
2. **互卦** (过程)：上{hu_shang['name']}({hu_shang['wx']}) 下{hu_xia['name']}({hu_xia['wx']})
3. **变卦** (结局)：上{bian_shang['name']}({bian_shang['wx']}) 下{bian_xia['name']}({bian_xia['wx']})
4. **核心关系**：
   - 体卦：{ti_gua['name']} ({ti_gua['wx']})
   - 用卦：{yong_gua['name']} ({yong_gua['wx']})
   - 动爻：第{dong_yao}爻

【分析要求】：
1. **八字简批**（若有八字）：分析日干五行及喜忌，判断当下流年运势是否利于此事。
2. **梅花卦象深度解析**：
   - **体用生克**：分析体卦与用卦的五行生克关系（吉凶主基调）。
   - **结合八字**：卦中"体卦"五行是否辅助了八字喜用神？（例如：八字喜水，体卦为坎水，则大吉）。
   - **出生地影响**：出生地点的方位五行对此次占卜是否有加持或减损（例如出生在北方水地）。
3. **过程与结果**：结合本卦（现状）、互卦（过程）、变卦（结果）的时间线推演。
4. **决策建议**：给出明确的行动建议。

请用专业的周易术语结合通俗易懂的语言输出，排版清晰。
"""

    st.markdown("### 🤖 AI 全息解读")
    
    res_box = st.empty()
    full_response = ""

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)

        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一位精通梅花易数与八字命理的国学大师。"},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                full_response += delta.content
                res_box.markdown(full_response + "▌")
            elif hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                # 兼容 deepseek-reasoner 的思维链输出 (如果有)
                pass 

        res_box.markdown(full_response)

    except Exception as e:
        st.error(f"AI 请求错误: {e}")
