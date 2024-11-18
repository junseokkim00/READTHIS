import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="Read This",
    page_icon="👀",
    layout="wide"
)

with st.sidebar:
    openai_api_key = st.text_input("OpenAI api key", type="password")
    st.markdown(
            "[Learn more about OpenAI API](https://platform.openai.com/api-keys)")
    save_configuration = st.button("Save configuration")
    if save_configuration and openai_api_key != "":
        st.session_state['openai_api_key'] = openai_api_key
        st.toast("✅ Openai api key ready!")

st.write("# Read :red[This]! 👨‍🔬")
logo = Image.open("assets/logo.png")
st.image(logo,width=500)

st.markdown(
    """
    ReadThis is an open-source application for finding research paper like a pro
    We have several services for users.
    1. 📄 `What's Next?`: find the next paper based on your currently readings
    2. 📝 `Daily Papers`: find related papers based on your :red[Zotero] collection
    3. 🕵️‍♂️ `Paper Hunt`: find the latest paper from the latest arxiv :orange[rss feed]
    ### How to use this?
    1. configure `openai_api_key` in the left sidebar by adding your `OPENAI_API_KEY`
        - we use text-embedding from openai, so it should not be a huge burden for the user.
    2. Specially for `Daily Papers` service, you need to connect your Zotero in order to use the service
    
    ### Contact us
     + [Linkedin](https://www.linkedin.com/in/junseok-kim-b93373214/)
     + Contribution [Github repo](https://github.com/junseokkim00/READTHIS.git)
"""
)