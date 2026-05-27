import streamlit as st
import pandas as pd
import numpy as np
import influxdb_client
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Posture Tracker App",
    page_icon="🩺",
    layout="centered"
)

if 'started' not in st.session_state:
    st.session_state['started'] = False

st.markdown("""
<style>
    .stApp { background-color: #f2f7fb; }

    .block-container {
        max-width: 430px !important;
        padding: 2rem !important;
        background-color: #ffffff;
        border-radius: 40px;
        box-shadow: 0 10px 30px rgba(153,192,222,0.3);
        margin:auto;
        border:8px solid #d4e6f4;
        min-height:80vh;
    }

    h1,h2,h3 {
        color:#5c8cb3;
        text-align:center;
    }

    .stButton>button{
        width:100%;
        border-radius:20px;
        background-color:#d4e6f4;
        color:#5c8cb3;
        border:2px solid #b5d1e8;
        padding:10px;
        font-weight:bold;
    }

    div[data-testid="stMetric"]{
        background-color:#f0f6fc;
        border-radius:20px;
        padding:15px !important;
        border:2px solid #e1eef7;
    }
</style>
""", unsafe_allow_html=True)

if not st.session_state['started']:

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1>🩺</h1>", unsafe_allow_html=True)
    st.markdown("<h1>Posture Tracker</h1>", unsafe_allow_html=True)

    if st.button("Comenzar"):
        st.session_state['started']=True
        st.rerun()

else:

    st_autorefresh(
        interval=2000,
        key="datarefresh"
    )

    url="https://us-east-1-1.aws.cloud2.influxdata.com/"
    token="TU_TOKEN"
    org="Jojo"
    bucket="postura_ergonomia"

    try:

        client=influxdb_client.InfluxDBClient(
            url=url,
            token=token,
            org=org,
            timeout=3000
        )

        query_api=client.query_api()

        query=f'''
        from(bucket: "{bucket}")
          |> range(start: -24h)
          |> filter(fn: (r) => r["_measurement"] == "Postura")
          |> pivot(
              rowKey:["_time"],
              columnKey:["_field"],
              valueColumn:"_value"
          )
        '''

        df=query_api.query_data_frame(query)

        # Si devuelve varias tablas
        if isinstance(df,list):
            df=pd.concat(
                df,
                ignore_index=True
            )

        st.write("📋 Columnas encontradas:")
        st.write(df.columns.tolist())

        st.write("📊 Últimos registros:")
        st.write(df.tail(10))

        st.write("📈 Total filas:")
        st.write(len(df))

        if df.empty:
            st.error("No llegaron datos")
            raise ValueError()

        if 'distancia' not in df.columns:
            st.error(
                "No existe columna distancia"
            )
            raise ValueError()

        df['distancia']=pd.to_numeric(
            df['distancia'],
            errors='coerce'
        )

        df=df.dropna(
            subset=['distancia']
        )

        if 'alerta' in df.columns:

            df['alerta']=pd.to_numeric(
                df['alerta'],
                errors='coerce'
            ).fillna(0).astype(int)

        es_datos_reales=True

    except Exception as e:

        st.error("ERROR:")
        st.write(e)

        es_datos_reales=False

        distancia_fija=42

        df=pd.DataFrame({

            'distancia':
            [distancia_fija]*20,

            'alerta':
            [0]*20
        })

    st.markdown(
        "<h2>🩺 PostureCare</h2>",
        unsafe_allow_html=True
    )

    ultima_distancia=int(
        df['distancia'].iloc[-1]
    )

    if ultima_distancia<40:

        st.warning(
            "⚠️ Recupera tu postura"
        )

    else:

        st.success(
            "✨ Todo bien"
        )

    c1,c2=st.columns(2)

    c1.metric(
        "Distancia Actual",
        f"{ultima_distancia} cm"
    )

    if es_datos_reales:
        c2.metric(
            "Conexión",
            "En Vivo 📡"
        )
    else:
        c2.metric(
            "Conexión",
            "Simulado 🔄"
        )

    st.subheader(
        "📊 Historial"
    )

    st.line_chart(
        df['distancia'].tail(15)
    )

    if st.button(
        "Cerrar Sesión"
    ):
        st.session_state['started']=False
        st.rerun()
