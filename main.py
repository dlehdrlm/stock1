import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="글로벌 주가 분석",
    page_icon="📈",
    layout="wide"
)

st.title("📈 글로벌 주가 분석")
st.write("최근 1년간 삼성전자, SK하이닉스, 구글, 마이크로소프트, 애플의 주가를 비교합니다.")

TICKERS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "구글": "GOOGL",
    "마이크로소프트": "MSFT",
    "애플": "AAPL"
}


@st.cache_data(ttl=3600)
def load_data():
    all_data = []

    for company, ticker in TICKERS.items():
        try:
            df = yf.download(
                ticker,
                period="1y",
                progress=False,
                auto_adjust=True
            )

            if df.empty:
                continue

            # MultiIndex 대응
            if isinstance(df.columns, pd.MultiIndex):
                close = df[("Close", ticker)]
            else:
                close = df["Close"]

            temp = pd.DataFrame({
                "Date": close.index,
                "Close": close.values.flatten()
            })

            temp["Company"] = company

            all_data.append(temp)

        except Exception as e:
            st.warning(f"{company} 데이터 수집 실패: {e}")

    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)


df = load_data()

if df.empty:
    st.error("주가 데이터를 불러오지 못했습니다.")
    st.stop()

# ==========================
# 수익률 계산
# ==========================

returns = []

for company in df["Company"].unique():

    company_df = (
        df[df["Company"] == company]
        .sort_values("Date")
        .reset_index(drop=True)
    )

    start_price = company_df["Close"].iloc[0]
    end_price = company_df["Close"].iloc[-1]

    return_pct = ((end_price - start_price) / start_price) * 100

    returns.append({
        "종목": company,
        "1년 수익률(%)": round(return_pct, 2)
    })

returns_df = (
    pd.DataFrame(returns)
    .sort_values("1년 수익률(%)", ascending=False)
)

# ==========================
# 정규화 그래프
# ==========================

normalized_data = []

for company in df["Company"].unique():

    company_df = (
        df[df["Company"] == company]
        .sort_values("Date")
        .copy()
    )

    first_price = company_df["Close"].iloc[0]

    company_df["Performance"] = (
        company_df["Close"] / first_price * 100
    )

    normalized_data.append(company_df)

normalized_df = pd.concat(normalized_data)

st.subheader("📊 최근 1년 주가 비교")

fig = px.line(
    normalized_df,
    x="Date",
    y="Performance",
    color="Company",
    labels={
        "Performance": "상대 주가 (시작=100)"
    }
)

fig.update_layout(
    hovermode="x unified",
    height=600
)

st.plotly_chart(fig, use_container_width=True)

# ==========================
# 수익률 표
# ==========================

st.subheader("🏆 최근 1년 수익률")

st.dataframe(
    returns_df,
    use_container_width=True,
    hide_index=True
)

# ==========================
# 막대 그래프
# ==========================

fig2 = px.bar(
    returns_df,
    x="종목",
    y="1년 수익률(%)",
    text="1년 수익률(%)"
)

fig2.update_layout(height=500)

st.plotly_chart(fig2, use_container_width=True)

# ==========================
# 최고 종목
# ==========================

winner = returns_df.iloc[0]

st.success(
    f"🥇 최근 1년 최고 성과 종목: {winner['종목']} "
    f"({winner['1년 수익률(%)']}%)"
)
