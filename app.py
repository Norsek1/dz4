import io
import urllib.parse
import requests
import streamlit as st
import cv2
import numpy as np
from PIL import Image

st.set_page_config(page_title="AI Studio", layout="wide")

def generate_image(prompt):
    try:
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&seed=42"
        res = requests.get(url, timeout=45)
        if res.status_code == 200:
            return res.content
    except:
        pass
    return None

st.title("AI Фотошоп")

prompt = st.text_area("Введіть запит:")

styles = {
    "Без стилю": "",
    "Реалістичний": ", photorealistic",
    "Акварель": ", watercolor style",
    "Мультяшний": ", 3d cartoon",
    "Піксель-Арт": ", pixel art"
}

style = st.selectbox("Стиль:", list(styles.keys()))

if st.button("Згенерувати") and prompt:
    with st.spinner("Генерація..."):
        img_data = generate_image(prompt + styles[style])
        if img_data:
            st.session_state["img"] = img_data
        else:
            st.error("Помилка генерації")

if "img" in st.session_state:
    image = Image.open(io.BytesIO(st.session_state["img"])).convert("RGB")
    img_array = np.array(image)

    st.sidebar.header("Фільтри")
    effect = st.sidebar.selectbox("Ефект:", [
        "Оригінал", "Чорно-білий", "Розмиття", 
        "Яскравість", "Інверсія", "Віддзеркалення", 
        "Контраст", "Колірний сплеск"
    ])

    res = img_array.copy()

    if effect == "Чорно-білий":
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        res = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

    elif effect == "Розмиття":
        res = cv2.GaussianBlur(img_array, (15, 15), 0)

    elif effect == "Яскравість":
        val = st.sidebar.slider("Рівень", -100, 100, 0)
        res = cv2.convertScaleAbs(img_array, alpha=1.0, beta=val)

    elif effect == "Інверсія":
        res = 255 - img_array

    elif effect == "Віддзеркалення":
        res = cv2.flip(img_array, 1)

    elif effect == "Контраст":
        val = st.sidebar.slider("Рівень", 0.5, 3.0, 1.0, step=0.1)
        res = cv2.convertScaleAbs(img_array, alpha=val, beta=0)

    elif effect == "Колірний сплеск":
        color = st.sidebar.selectbox("Колір:", ["Червоний", "Зелений", "Синій"])
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)

        if color == "Червоний":
            m1 = cv2.inRange(hsv, np.array([0, 50, 50]), np.array([10, 255, 255]))
            m2 = cv2.inRange(hsv, np.array([170, 50, 50]), np.array([180, 255, 255]))
            mask = cv2.bitwise_or(m1, m2)
        elif color == "Зелений":
            mask = cv2.inRange(hsv, np.array([35, 50, 50]), np.array([85, 255, 255]))
        elif color == "Синій":
            mask = cv2.inRange(hsv, np.array([100, 50, 50]), np.array([140, 255, 255]))

        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        gray_3ch = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
        mask_3ch = mask[:, :, np.newaxis]
        res = np.where(mask_3ch == 255, img_array, gray_3ch)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Оригінал")
        st.image(img_array, use_container_width=True)

    with col2:
        st.subheader("Результат")
        st.image(res, use_container_width=True)

        buf = io.BytesIO()
        Image.fromarray(res).save(buf, format="PNG")
        st.download_button("Завантажити", buf.getvalue(), "photo.png", "image/png")
