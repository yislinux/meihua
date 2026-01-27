import streamlit as st
from openai import OpenAI
import time

# ================= 1. 页面配置与样式 =================
st.set_page_config(
    page_title="AI梅花易数排盘",
    page_icon="☯️",
    layout="wide"
)

# 自定义 CSS 样式，用于绘制漂亮的卦爻
st.markdown("""
<style>
    .yao-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 5px 0;
        height: 30px;
    }
    .yang-yao {
        width: 100%;
        height: 20px;
        background-color: #3b82f6; /* 阳爻蓝色 */
        border-radius: 4px;
    }
    .yin-yao {
        display: flex;
        width: 100%;
        justify-content: space-between;
    }
    .yin-block {
        width: 45%;
        height: 20px;
        background-color: #f59e0b; /* 阴爻黄色 */
        border-radius: 4px;
    }
    .moving-yao .yang-yao, .moving-yao .yin-block {
        background-color: #ef4444 !important; /* 动爻红色高亮 */
        box-shadow: 0 0 8px rgba(239, 68, 68, 0.6);
    }
    .gua-title {
        text-align: center;
        font-weight: bold;
        color: #555;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ================= 2. 基础数据定义 =================
GUA_DATA = {
    1: {"name": "乾", "wx": "金", "binary": [1, 1, 1], "nature": "天"},
    2: {"name": "兑", "wx": "金", "binary": [1, 1, 0], "nature": "泽"},
    3: {"name": "离", "wx": "火", "binary": [1, 0, 1], "nature": "火"},
    4: {"name": "震", "wx": "木", "binary": [1, 0, 0], "nature": "雷"},
    5: {"name": "巽", "wx": "木", "binary": [0, 1, 1], "nature": "风"},
    6: {"name": "坎", "wx": "水", "binary": [0, 1, 0], "nature": "水"},
    7: {"name": "艮", "wx": "土", "binary": [0, 0, 1], "nature": "山"},
    8: {"name": "坤", "wx": "土", "binary": [0, 0, 0], "nature": "地"},
}

# ================= 3. 核心逻辑函数 =================

def get_gua_id_by_binary(bits):
    """根据二进制列表 [1,0,1] 反推卦ID"""
    for gid, data in GUA_DATA.items():
        if data["binary"] == bits:
            return gid
    return 8 # 默认坤

def draw_yao_html(is_yang, is_moving=False):
    """生成单爻的 HTML"""
    moving_class = "moving-yao" if is_moving else ""
    if is_yang:
        return f"""
        <div class='yao-container {moving_class}'>
            <div class='yang-yao'></div>
        </div>
        """
    else:
        return f"""
        <div class='yao-container {moving_class}'>
            <div class='yin-yao'>
                <div class='yin-block'></div>
                <div class='yin-block'></div>
            </div>
        </div>
        """

def get_api_client():
    """获取 API 客户端，优先从 Secrets 读取"""
    api_key = None
    base_url = "https://api.deepseek.com" # 默认 DeepSeek
    
    # 尝试从 Secrets 读取
    if "DEEPSEEK_API_KEY" in st.secrets:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
        if "DEEPSEEK_BASE_URL" in st.secrets:
            base_url = st.secrets["DEEPSEEK_BASE_URL"]
    
    return api_key, base_url

# ================= 4. 侧边栏与输入 =================

with st.sidebar:
    st.title("🔮 设置")
    
    # 获取 API Key (如果 Secrets 没配置，允许用户手动输入)
    api_key, base_url = get_api_client()
    
    if not api_key:
        st.warning("未检测到 Secrets 配置，请手动输入 Key")
        api_key = st.text_input("DeepSeek API Key", type="password")
        base_url = st.text_input("API Base URL", value="https://api.deepseek.com")
    
    model_name = st.selectbox("选择模型", ["DeepSeek-R1", "deepseek-reasoner"], index=0)
    st.markdown("---")
    st.info("💡 说明：\n1. 输入两个数字起卦。\n2. 系统自动推算体用五行。\n3. AI 大师进行详细解卦。")

# ================= 5. 主界面 =================

st.title("☯️ AI 梅花易数排盘系统")
st.caption("基于数理推演与大语言模型的智能占卜")

# 输入区域
col1, col2 = st.columns(2)
with col1:
    num1 = st.number_input("上卦数 (例如 3)", min_value=1, value=3, step=1)
with col2:
    num2 = st.number_input("下卦数 (例如 8)", min_value=1, value=8, step=1)

question = st.text_input("💭 请输入你想占卜的具体事项", placeholder="例如：这次面试能顺利通过吗？")

# 按钮
start_divination = st.button("🚀 开始排盘与解卦", use_container_width=True, type="primary")

if start_divination:
    if not api_key:
        st.error("请先配置 API Key！")
        st.stop()

    # --- 1. 数理计算 ---
    shang_num = num1 % 8 or 8
    xia_num = num2 % 8 or 8
    total_sum = num1 + num2
    dong_yao = total_sum % 6 or 6 # 动爻 (1-6)

    # 获取本卦数据
    ben_shang = GUA_DATA[shang_num]
    ben_xia = GUA_DATA[xia_num]
    
    # 组装本卦六爻 (下卦在下0-2，上卦在上3-5)
    ben_yao_list = ben_xia["binary"] + ben_shang["binary"] # [初,二,三,四,五,上]
    
    # --- 2. 变卦计算 ---
    bian_yao_list = ben_yao_list.copy()
    idx = dong_yao - 1 # 数组索引
    bian_yao_list[idx] = 1 - bian_yao_list[idx] # 0变1, 1变0
    
    # 反推变卦ID
    bian_xia_bits = bian_yao_list[0:3]
    bian_shang_bits = bian_yao_list[3:6]
    bian_xia_id = get_gua_id_by_binary(bian_xia_bits)
    bian_shang_id = get_gua_id_by_binary(bian_shang_bits)
    
    bian_shang = GUA_DATA[bian_shang_id]
    bian_xia = GUA_DATA[bian_xia_id]

    # --- 3. 体用判定 ---
    if dong_yao > 3: # 动在上，上为用，下为体
        ti_gua = ben_xia
        yong_gua = ben_shang
        bian_res_gua = bian_shang # 变卦结果看动的那部分
        ti_pos, yong_pos = "下卦", "上卦"
    else: # 动在下，下为用，上为体
        ti_gua = ben_shang
        yong_gua = ben_xia
        bian_res_gua = bian_xia
        ti_pos, yong_pos = "上卦", "下卦"

    # ================= 6. 卦象可视化展示 =================
    st.markdown("### 📊 排盘结果")
    
    # 布局：本卦 - 箭头 - 变卦
    g_col1, g_col2, g_col3 = st.columns([3, 1, 3])
    
    # --- 画本卦 ---
    with g_col1:
        st.markdown(f"<div class='gua-title'>【本卦】<br>{ben_shang['name']}{ben_xia['name']} <br> <span style='font-size:0.8em;color:#888'>上{ben_shang['name']}{ben_shang['wx']} / 下{ben_xia['name']}{ben_xia['wx']}</span></div>", unsafe_allow_html=True)
        # 倒序画爻 (从上爻到初爻)
        for i in range(5, -1, -1):
            is_moving = (i == (dong_yao - 1))
            st.markdown(draw_yao_html(ben_yao_list[i] == 1, is_moving), unsafe_allow_html=True)
            
    # --- 中间箭头 ---
    with g_col2:
        st.markdown("<br><br><br><div style='text-align:center; font-size:2em; color:#888'>➜<br><span style='font-size:0.4em'>动爻</span></div>", unsafe_allow_html=True)

    # --- 画变卦 ---
    with g_col3:
        st.markdown(f"<div class='gua-title'>【变卦】<br>{bian_shang['name']}{bian_xia['name']} <br> <span style='font-size:0.8em;color:#888'>上{bian_shang['name']}{bian_shang['wx']} / 下{bian_xia['name']}{bian_xia['wx']}</span></div>", unsafe_allow_html=True)
        for i in range(5, -1, -1):
            is_moving = (i == (dong_yao - 1))
            st.markdown(draw_yao_html(bian_yao_list[i] == 1, is_moving), unsafe_allow_html=True)

    # --- 体用分析文字 ---
    st.info(f"""
    **🔍 体用分析：**
    - **体卦 (代表自己)**：{ti_gua['name']} (五行：{ti_gua['wx']})
    - **用卦 (代表事情)**：{yong_gua['name']} (五行：{yong_gua['wx']})
    - **变卦 (代表结果)**：变为 {bian_res_gua['name']} (五行：{bian_res_gua['wx']})
    """)

    # ================= 7. AI 解卦 =================
    st.markdown("### 🤖 大师解卦")
    
    # 构造 Prompt
    prompt = f"""
    你是一位精通梅花易数的国学大师。请根据以下排盘数据为用户解卦。
    
    【用户问题】：{question if question else "求测运势"}
    
    【卦象数据】：
    1. 本卦：上{ben_shang['name']}({ben_shang['wx']}) 下{ben_xia['name']}({ben_xia['wx']})。
    2. 动爻：第 {dong_yao} 爻发动。
    3. 变卦：变为 上{bian_shang['name']} 下{bian_xia['name']}。
    
    【体用生克】：
    - 体卦（自己）：{ti_gua['name']} ({ti_gua['wx']})
    - 用卦（事情）：{yong_gua['name']} ({yong_gua['wx']})
    - 变卦（结果）：变为了 {bian_res_gua['name']} ({bian_res_gua['wx']})
    
    请按以下结构输出：
    1. **卦象分析**：简述卦象含义。
    2. **五行生克**：分析体用关系（如用生体大吉，体克用小吉，用克体大凶等）及变卦对体卦的影响。
    3. **大师结论**：针对用户问题给出明确的吉凶判断。
    4. **建议**：简短的行动建议。
    """
    
    res_box = st.empty()
    full_response = ""
    
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一位专业的易经大师，语气沉稳，逻辑严密。"},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        
        # 流式输出
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                full_response += content
                res_box.markdown(full_response + "▌")
        
        res_box.markdown(full_response)
        
    except Exception as e:
        st.error(f"AI 请求失败: {str(e)}")
