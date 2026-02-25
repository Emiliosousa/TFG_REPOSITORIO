import re

def clean_html(html):
    return re.sub(r'^\s+', '', html, flags=re.MULTILINE)

with open("app_premier.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Fix dc_cells build loop to avoid leading spaces that trigger markdown code blocks
# We'll use a more robust way to build it.
content = content.replace('                            dc_cells += f"""\n                            <div', '                            dc_cells += f"""<div')

# 2. Wrap all st.markdown with clean_html for those that don't have it
# Specifically the ones I added for Double Chance and Risk
content = content.replace('st.markdown(dc_html, unsafe_allow_html=True)', 'st.markdown(clean_html(dc_html), unsafe_allow_html=True)')
content = content.replace('st.markdown(risk_html, unsafe_allow_html=True)', 'st.markdown(clean_html(risk_html), unsafe_allow_html=True)')
content = content.replace('st.markdown(stake_html, unsafe_allow_html=True)', 'st.markdown(clean_html(stake_html), unsafe_allow_html=True)')
content = content.replace('st.markdown(grid_html, unsafe_allow_html=True)', 'st.markdown(clean_html(grid_html), unsafe_allow_html=True)')
content = content.replace('st.markdown(rat_html, unsafe_allow_html=True)', 'st.markdown(clean_html(rat_html), unsafe_allow_html=True)')

# 3. Ensure dc_html and others don't have leading spaces in their triple quotes
content = content.replace('                        dc_html = f"""\n                        <div', '                        dc_html = f"""<div')
content = content.replace('                        risk_html = f"""\n                        <div', '                        risk_html = f"""<div')
content = content.replace('                        stake_html = f"""<table', '                        stake_html = f"""<table')

with open("app_premier.py", "w", encoding="utf-8") as f:
    f.write(content)

print("done")
