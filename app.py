import pandas as pd
import streamlit as st
from datetime import date, datetime
from dateutil import parser
#################################################
######### go to the folder Exce_Webapp ##########
######### execute: streamlit run 'app.py' #######
#################################################
import plotly.express as px
# from PIL import Image

st.set_page_config(page_title='Dashboard')
st.header('Performance Overview')
st.subheader('Installed DCU Status')

### --- LOAD DATAFRAME
excel_file = 'plc_to_st.xlsx'
sheet_name = 'Sheet1'

df = pd.read_excel(excel_file, sheet_name=sheet_name)
del df["Unnamed: 0"]
df.rename(columns={"Collector/DCU": "DCU", "Meter ID": "Nb Meter"}, inplace=True)

st.write(df.iloc[:, :-1].astype(str))

# df_rw_ww = pd.read_excel("df_rw_ww.xlsx", engine="openpyxl", parse_dates=True, dtype=str)
df_rw_ww_t = pd.read_excel("df_rw_ww_transposed.xlsx", engine="openpyxl", parse_dates=True, dtype=str)
df_rw_ww_t.set_index("Unnamed: 0", inplace=True)
del df_rw_ww_t["Total Collectable"]

df_fig = df_rw_ww_t.reset_index().rename(columns={"Unnamed: 0": "Date"})
df_fig["Date"] = df_fig["Date"].astype(str).apply(lambda x: parser.parse(x).date()).apply(lambda x: x.strftime("%d %b"))
df_fig["Performance"] = df_fig["Performance"].astype(str).apply(lambda x: x[:-1]).astype(float)

st.subheader('Official Performance Calculation')
# st.write(df_rw_ww.astype(str))
# st.table(df_rw_ww.astype(str))
# st.dataframe(df_rw_ww.astype(str))
st.dataframe(df_rw_ww_t)
# st.line_chart(df_rw_ww_t["Performance"])

fig = px.line(df_fig, x="Date", y="Performance", title='KPI', markers=True, text="Performance")
fig.update_xaxes(visible=True, fixedrange=False)
fig.update_layout(
    showlegend=True,
    plot_bgcolor="silver",
    font_family="Courier New",
    font_color="black",
    title_font_family="Times New Roman",
    title_font_color="blue",
    legend_title_font_color="green")
fig.update_traces(textposition="bottom center")
st.plotly_chart(fig)

# --- STREAMLIT SELECTION
DCU = df['DCU'].unique().tolist()
#
dc_selection = st.multiselect('Select a DCU:', DCU)


# --- FILTER DATAFRAME BASED ON SELECTION
# mask = (df['Age'].between(*age_selection)) & (df['Department'].isin(department_selection))
mask = df["DCU"].isin(dc_selection)
number_of_result = df[mask].shape[0]
st.markdown(f'*Available Results: {number_of_result}*')

# --- GROUP DATAFRAME AFTER SELECTION
df_grouped = df[mask].groupby("DCU").agg("sum")
df_grouped = df_grouped.reset_index()[["DCU", "Nb Meter"]]

# agg({'B': ['min', 'max'], 'C': 'sum'})
df_selection = df[mask][["DCU", "Marker", "Nb Meter"]]

# --- PLOT BAR CHART
bar_chart = px.bar(df_selection,
                   x='DCU',
                   y='Nb Meter',
                   color="Marker",
                   text='Marker',
                   text_auto=True,
                   title=f"Selected DCU Status on {df.columns[-1]}")
st.plotly_chart(bar_chart)
st.write(df_grouped.astype(str))

df_kpi_dc = pd.read_excel("st_df_kpi_dc.xlsx")
# df_kpi_dc = df_kpi_dc.set_index(df_kpi_dc.DCU)

st.subheader("Selected DCU Performance :")
duration_selection = st.slider('Days', min_value= 5, max_value= 90)

df_kpi_dc_selected_col = ["DCU", "Info"] + [col for col in df_kpi_dc.columns[-duration_selection-2:-2]]
df_kpi_dc_selected = df_kpi_dc[df_kpi_dc["DCU"].isin(dc_selection)][df_kpi_dc_selected_col].set_index("DCU")
st.write(df_kpi_dc_selected.astype(str))

df_chart_kpi_dc = df_kpi_dc_selected.drop("Info", axis=1).T.reset_index().rename(columns={"index": "Date"})
# st.write(df_chart_kpi_dc.astype(str))

for col in df_chart_kpi_dc.columns[1:]:
    fig_kpi_dc = px.line(df_chart_kpi_dc, x="Date", y=f"{col}", title=f"{col}", markers=True, text=f"{col}")
    fig_kpi_dc.update_xaxes(visible=True, fixedrange=False)
    fig_kpi_dc.update_layout(
        showlegend=True,
        plot_bgcolor="silver",
        font_family="Courier New",
        font_color="black",
        title_font_family="Times New Roman",
        title_font_color="blue",
        legend_title_font_color="green")
    fig_kpi_dc.update_traces(textposition="bottom center")
    st.plotly_chart(fig_kpi_dc)
###########################################
#### ---- Drop DC FollowUP ---- ###########
###########################################
import sqlite3
conn = sqlite3.connect('data.db')
cur =conn.cursor()

st.subheader("Drop DC Followup")
df_dc_drop_info = pd.read_excel("drop_dc.xlsx").astype(str)
df_dc_drop_info["DCU"] = df_dc_drop_info["DCU"].apply(lambda x: "SAG099000000" + x[0:4])
df_dc_drop_info["Identification_Date"] = df_dc_drop_info["Identification_Date"].apply(lambda x: "not defined" if x == 'nan' else parser.parse(x).date())

######## Populate the excel into data.db ###########
try:
    df_dc_drop_info.to_sql(name="drop_table", con=conn, if_exists="fail", index=False)
    conn.commit()
except:
    pass

def sql(query, cursor):
    # Takes an SQL query string, and outputs a dataframe representation of the query result
    cursor.execute(query)
    # Get the query into a dataframe and set columns
    df_temp = pd.DataFrame(cursor.fetchall())
    df_temp.columns = [x[0] for x in cursor.description] # récupérer tous les columns_name de la database dans le dataframe

    # Set the sql id as the dataframe index
    # index_column = df_temp.columns[0] # récupérer la colonne "Index" de la database
    # df_temp.set_index(index_column, drop=True, inplace=True)
    return df_temp


df_drop_table = sql('SELECT * FROM drop_table', cur)


def dcu_info_form():
    st.write("_"*100)
    st.subheader("\n" + "Insert DCU Info & Analysis in the Drop DCU Table :")
    dc = st.selectbox('Select the concerned DCU:', DCU[1:])

    with st.form(key="Information form"):

        date_info =st.date_input("Identification/Update Date of DCU Drop/info :")
        if dc in df_drop_table['DCU'].tolist():
            injection = st.text_input("Current injection on the concerned DCU :", value=f"{df_drop_table[df_drop_table['DCU'] == dc]['Injection'].item()}")
            discovered = st.text_input("Number of Discovered meters :", f"{df_drop_table[df_drop_table['DCU'] == dc]['Discovered_Meters'].item()}")
            dropped = st.text_input("Number of Dropped meters :", f"{df_drop_table[df_drop_table['DCU'] == dc]['Dropped_Meters'].item()}")
            cause = st.text_area("Cause of Drop :", f"{df_drop_table[df_drop_table['DCU'] == dc]['Cause'].item()}")
            action = st.text_area("Historique des Actions effectuée :", f"{df_drop_table[df_drop_table['DCU'] == dc]['Action'].item()}")
        else:
            injection = st.text_input("Current injection on the concerned DCU :")
            discovered = st.text_input("Number of Discovered meters :")
            dropped = st.text_input("Number of Dropped meters :")
            cause = st.text_area("Cause of Drop :")
            action = st.text_area("Historique des Actions effectuée :")
        submission = st.form_submit_button("Submit your Changes !")
        if submission == True:
            if dc not in df_drop_table["DCU"].tolist():
                st.write("DC not in the drop_table and will be added to the database !")
                add_data(date_info, dc, injection, cause, action)
            else:
                st.write("DC already in the drop_table and will be updated in the database !")
                update_data(date_info, dc, injection, cause, action)


def add_data(date_to_insert, dc, inject, cause, action):
    # cur.execute("""CREATE TABLE IF NOT EXISTS drop_table(Identification Date TEXT, DCU TEXT, Injection TEXT, Discovered Meters TEXT, Dropped Meters TEXT, Meter Status WebGui TEXT,
    #     Cause TEXT, Action TEXT, DCU Replacement TEXT, Related SDCU TEXT, Status TEXT, Effectiveness of Remote Actions TEXT)""")

    cur.execute("INSERT INTO drop_table (Identification_Date, DCU, Injection, Cause, Action) VALUES (?,?,?,?,?)", (date_to_insert, dc, inject, cause, action))
    conn.commit()
    conn.close()
    st.success("Successfully Submitted")


def update_data(date_to_insert, dc, inject, cause, action):
    cur.execute("UPDATE drop_table SET Identification_Date = ?, Injection = ?, Cause = ?, Action = ? WHERE DCU = ?", (date_to_insert, inject, cause, action, dc))
    conn.commit()
    conn.close()
    st.success("Successfully Submitted")


st.write(df_drop_table.astype(str))
dcu_info_form()


# --- DISPLAY IMAGE & DATAFRAME
col1, col2 = st.columns(2)
# image = Image.open('images/survey.jpg')

# col1.image(image, caption='Designed by slidesgo / Freepik', use_column_width=True)

# col2.dataframe(df_dc_drop_info.astype(str))
#
# # --- PLOT PIE CHART
# pie_chart = px.pie(df_participants,
#                 title='Total No. of Participants',
#                 values='Participants',
#                 names='Departments')
#
# st.plotly_chart(pie_chart)
