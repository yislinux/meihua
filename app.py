import streamlit as st
from openai import OpenAI

# ================= 1. 页面配置 =================
st.set_page_config(
    page_title="AI梅花易数排盘",
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
        background-color: #000 !important;
        box-shadow: none;
    }
    .gua-title {
        text-align: center;
        font-weight: bold;
        color: #444;
        margin-bottom: 8px;
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

# ================= 5. 侧边栏 =================
with st.sidebar:
    st.title("🔮 设置")

    api_key, base_url = get_api_client()

    if not api_key:
        st.warning("未检测到 Secrets，请手动输入 Key")
        api_key = st.text_input("DeepSeek API Key", type="password")
        base_url = st.text_input("API Base URL", value="https://api.deepseek.com")

    model_name = st.selectbox(
        "选择模型",
        ["deepseek-R1", "deepseek-reasoner"],
        index=0
    )

    st.markdown("---")
    st.caption("输入数字起卦，可选填八字综合分析。")

# ================= 6. 主界面 =================
st.title("☯️ AI 梅花易数排盘")
st.caption("数字起卦 + 八字补充（可选）")

col1, col2 = st.columns(2)
with col1:
    num1 = st.number_input("上卦数", min_value=1, value=3, step=1)
with col2:
    num2 = st.number_input("下卦数", min_value=1, value=8, step=1)

question = st.text_input("占卜事项", placeholder="例如：这次面试能顺利通过吗？")

bazi = st.text_input(
    "八字（可选）",
    placeholder="例如：甲子年 丙寅月 戊午日 壬申时（不填则只按梅花易数）"
)

start_divination = st.button("开始排盘与解卦", use_container_width=True)

if start_divination:
    if not api_key:
        st.error("请先配置 API Key！")
        st.stop()

    # ================= 数理起卦 =================
    shang_num = num1 % 8 or 8
    xia_num = num2 % 8 or 8
    total_sum = num1 + num2
    dong_yao = total_sum % 6 or 6

    ben_shang = GUA_DATA[shang_num]
    ben_xia = GUA_DATA[xia_num]

    ben_yao_list = ben_xia["binary"] + ben_shang["binary"]

    # ================= 变卦 =================
    bian_yao_list = ben_yao_list.copy()
    idx = dong_yao - 1
    bian_yao_list[idx] = 1 - bian_yao_list[idx]

    bian_xia_id = get_gua_id_by_binary(bian_yao_list[0:3])
    bian_shang_id = get_gua_id_by_binary(bian_yao_list[3:6])

    bian_shang = GUA_DATA[bian_shang_id]
    bian_xia = GUA_DATA[bian_xia_id]

    # ================= 体用 =================
    if dong_yao > 3:
        ti_gua = ben_xia
        yong_gua = ben_shang
        bian_res_gua = bian_shang
    else:
        ti_gua = ben_shang
        yong_gua = ben_xia
        bian_res_gua = bian_xia

    # ================= 展示卦象 =================
    st.markdown("### 📊 排盘结果")

    g1, g2, g3 = st.columns([3, 1, 3])

    with g1:
        st.markdown(
            f"<div class='gua-title'>本卦：{ben_shang['name']}{ben_xia['name']}</div>",
            unsafe_allow_html=True
        )
        for i in range(5, -1, -1):
            st.markdown(draw_yao_html(ben_yao_list[i] == 1, i == idx), unsafe_allow_html=True)

    with g2:
        st.markdown("<div style='text-align:center;font-size:2em;'>➜</div>", unsafe_allow_html=True)

    with g3:
        st.markdown(
            f"<div class='gua-title'>变卦：{bian_shang['name']}{bian_xia['name']}</div>",
            unsafe_allow_html=True
        )
        for i in range(5, -1, -1):
            st.markdown(draw_yao_html(bian_yao_list[i] == 1, i == idx), unsafe_allow_html=True)

    st.info(f"""
体卦：{ti_gua['name']}（{ti_gua['wx']}）  
用卦：{yong_gua['name']}（{yong_gua['wx']}）  
变卦结果：{bian_res_gua['name']}（{bian_res_gua['wx']}）
""")

    # ================= AI 解卦 Prompt =================
    bazi_text = ""
    if bazi.strip():
        bazi_text = f"""
【用户八字】：{bazi}
请结合八字命理与梅花易数综合判断。
"""

    prompt = f"""
你是一位精通梅花易数与八字命理的国学大师。

【用户问题】：{question if question else "求测运势"}

{bazi_text}

【卦象数据】：
本卦：上{ben_shang['name']}({ben_shang['wx']}) 下{ben_xia['name']}({ben_xia['wx']})
动爻：第{dong_yao}爻
变卦：上{bian_shang['name']} 下{bian_xia['name']}

体卦：{ti_gua['name']}（{ti_gua['wx']}）
用卦：{yong_gua['name']}（{yong_gua['wx']}）
变卦结果：{bian_res_gua['name']}（{bian_res_gua['wx']}）

请输出：
1. 卦象分析
2. 体用五行生克
3. 八字补充（若提供）
4. 综合结论（吉凶）
5. 建议
"""

    st.markdown("### 🤖 AI 解卦结果")

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

        res_box.markdown(full_response)

    except Exception as e:
        st.error(f"AI 请求错误: {e}")
