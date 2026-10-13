import streamlit as st

from gatekeeper import needs_approval, route, safe_to_remember


st.set_page_config(page_title="AskIT Gatekeeper", page_icon="🛡️", layout="centered")

st.title("AskIT Gatekeeper")
st.write("Test the routing, approval, and memory safety rules from gatekeeper.py.")

text = st.text_area("Text", height=140, placeholder="Enter a ticket, action description, or fact to evaluate.")

col1, col2, col3 = st.columns(3)

if col1.button("Route"):
    try:
        st.success(route(text))
    except ValueError as error:
        st.error(str(error))

if col2.button("Needs approval"):
    try:
        result = needs_approval("reset_password", "EMP-1002", 10)
        st.json(result)
    except ValueError as error:
        st.error(str(error))

if col3.button("Safe to remember"):
    try:
        st.success(str(safe_to_remember(text)))
    except ValueError as error:
        st.error(str(error))