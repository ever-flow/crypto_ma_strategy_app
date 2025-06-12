import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import datetime
from dateutil.relativedelta import relativedelta
import warnings
warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="🚀 암호화폐 최적 전략 분석",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 미니멀한 커스텀 CSS
st.markdown("""
<style>
    /* 전체 배경 */
    .main {
        background: #fafafa;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        padding: 1rem;
    }
    
    /* 헤더 - 미니멀한 그레이 톤 */
    .hero-section {
        background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 20px rgba(107, 114, 128, 0.15);
    }
    
    .hero-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .hero-subtitle {
        font-size: 1rem;
        opacity: 0.9;
        font-weight: 400;
    }
    
    /* 업데이트 정보 */
    .update-info {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e5e7eb;
        font-size: 0.875rem;
    }
    
    .update-title {
        font-weight: 600;
        color: #374151;
        margin-bottom: 0.5rem;
    }
    
    .update-text {
        color: #6b7280;
        margin: 0.25rem 0;
    }
    
    /* 차트 컨테이너 */
    .chart-section {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border: 1px solid #e5e7eb;
    }
    
    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #374151;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    /* 설명 박스 */
    .explanation-box {
        background: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 6px 6px 0;
    }
    
    .explanation-title {
        font-weight: 600;
        color: #1e40af;
        margin-bottom: 0.5rem;
    }
    
    .explanation-text {
        color: #475569;
        font-size: 0.875rem;
        line-height: 1.5;
    }
    
    /* 반응형 */
    @media (max-width: 768px) {
        .hero-title { font-size: 1.5rem; }
        .hero-subtitle { font-size: 0.875rem; }
    }
    
    /* Streamlit 기본 요소 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* 데이터프레임 스타일링 */
    .dataframe {
        border: none !important;
        border-radius: 6px !important;
        overflow: hidden !important;
        font-size: 0.875rem !important;
    }
    
    .dataframe th {
        background: #f9fafb !important;
        color: #374151 !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.75rem !important;
    }
    
    .dataframe td {
        border: none !important;
        padding: 0.5rem 0.75rem !important;
        border-bottom: 1px solid #f3f4f6 !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_strategy_results():
    """저장된 전략 결과를 로드"""
    try:
        with open('strategy_results.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ 전략 결과 파일을 찾을 수 없습니다. 데이터 업데이트가 필요합니다.")
        return None
    except Exception as e:
        st.error(f"❌ 데이터 로드 오류: {e}")
        return None

def format_datetime(iso_string):
    """ISO 형식 날짜를 한국어 형식으로 변환"""
    try:
        dt = datetime.datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.strftime('%Y년 %m월 %d일 %H시 %M분')
    except:
        return iso_string

def get_period_performance(cumulative_series_dict, period_years):
    """특정 기간의 성과를 계산"""
    if not cumulative_series_dict:
        return None, None, None
    
    # 딕셔너리를 pandas Series로 변환
    dates = [pd.to_datetime(k) for k in cumulative_series_dict.keys()]
    values = list(cumulative_series_dict.values())
    series = pd.Series(values, index=dates).sort_index()
    
    if series.empty or len(series) < 2:
        return None, None, None
    
    last_date = series.index[-1]
    start_date = last_date - relativedelta(years=period_years)
    period_series = series[series.index >= start_date]
    
    if len(period_series) < 2:
        return None, None, None
    
    ret_factor = period_series.iloc[-1] / period_series.iloc[0]
    ret_pct = (ret_factor - 1) * 100
    years = max((period_series.index[-1] - period_series.index[0]).days / 365.25, 1/365.25)
    cagr = ((ret_factor ** (1 / years)) - 1) * 100 if years > 0 else 0
    
    # MDD 계산
    cummax = period_series.cummax()
    drawdown = (period_series / cummax) - 1
    mdd = drawdown.min() * 100
    
    return ret_pct, cagr, mdd

def create_strategy_card_streamlit(strategy_name, strategy_data, emoji):
    """Streamlit 네이티브 컴포넌트로 전략 카드 생성"""
    signal = strategy_data.get('signal', '데이터 부족')
    signal_color = strategy_data.get('signal_color', 'gray')
    
    # 컨테이너 생성
    with st.container():
        # 헤더 행
        col_title, col_signal = st.columns([3, 1])
        with col_title:
            st.markdown(f"### {emoji} {strategy_name}")
        with col_signal:
            if signal_color == "#28a745":  # 초록색
                st.success(signal)
            elif signal_color == "#dc3545":  # 빨간색
                st.error(signal)
            else:
                st.info(signal)
        
        # 최적 MA 표시
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: #f9fafb; border-radius: 6px; margin: 1rem 0;">
            <div style="font-size: 2.5rem; font-weight: 800; color: #6b7280; margin: 0; line-height: 1;">
                {strategy_data['optimal_ma']}
            </div>
            <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem; font-weight: 500;">
                최적 이동평균 (일)
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 메트릭 그리드
        col1, col2 = st.columns(2)
        with col1:
            st.metric("스마트 점수", f"{strategy_data['combined_sortino']:.3f}", help="높을수록 좋은 전략입니다")
            st.metric("최대 손실", f"{strategy_data['drawdown']*100:.1f}%", help="투자 기간 중 가장 큰 손실률")
        with col2:
            cagr_delta = f"{strategy_data['cagr']*100:.1f}%" if strategy_data['cagr'] > 0 else None
            st.metric("연평균 수익률", f"{strategy_data['cagr']*100:.1f}%", delta=cagr_delta, help="1년 동안 평균적으로 얻는 수익률")
            st.metric("위험 대비 수익", f"{strategy_data['sharpe']:.2f}", help="위험 대비 얼마나 좋은 수익을 내는지 측정")

def main():
    # 헤더
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">🚀 암호화폐 최적 전략 분석</h1>
        <p class="hero-subtitle">AI 기반 이동평균 최적화 • 실시간 매수/매도 신호 • 고도화된 성과 분석</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 데이터 로드
    results = load_strategy_results()
    if not results:
        st.stop()
    
    # 업데이트 정보 표시
    last_updated = format_datetime(results.get('last_updated', ''))
    data_period = results.get('data_period', {})
    start_date = format_datetime(data_period.get('start', ''))
    end_date = format_datetime(data_period.get('end', ''))
    
    st.markdown(f"""
    <div class="update-info">
        <div class="update-title">📊 실시간 데이터 정보</div>
        <div class="update-text"><strong>최근 업데이트:</strong> {last_updated}</div>
        <div class="update-text"><strong>분석 기간:</strong> {start_date} ~ {end_date}</div>
        <div class="update-text"><strong>업데이트 주기:</strong> 매일 오전 9시 자동 업데이트</div>
        <div class="update-text"><strong>최적화 방식:</strong> 스마트 점수 (전체 30% + 최근3년 40% + 최근1년 30%)</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 스마트 점수 설명
    st.markdown("""
    <div class="explanation-box">
        <div class="explanation-title">💡 스마트 점수란?</div>
        <div class="explanation-text">
            스마트 점수는 투자 전략의 우수성을 측정하는 지표입니다. 단순히 수익률만 보는 것이 아니라, 
            <strong>위험 대비 얼마나 안정적으로 수익을 내는지</strong>를 종합적으로 평가합니다.
            <br><br>
            • <strong>높을수록 좋은 전략</strong>: 1.0 이상이면 우수, 1.5 이상이면 매우 우수<br>
            • <strong>최근 성과 중시</strong>: 과거보다 최근 3년, 1년 성과에 더 높은 가중치 부여<br>
            • <strong>안정성 고려</strong>: 같은 수익률이라도 변동성이 적은 전략이 더 높은 점수
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 전략 카드들
    st.markdown('<div class="section-title">🏆 최적 이동평균 전략 및 현재 신호</div>', unsafe_allow_html=True)
    
    strategy_configs = [
        ('BTC', 'BTC 단독 투자', '₿'),
        ('ETH', 'ETH 단독 투자', '⟠'),
        ('Rebal_50_50', '50:50 리밸런싱', '⚖️'),
        ('Rebal_60_40', '60:40 리밸런싱', '📊')
    ]
    
    # 2x2 그리드로 카드 배치
    col1, col2 = st.columns(2)
    
    for i, (key, name, emoji) in enumerate(strategy_configs):
        if key in results:
            strategy_data = results[key]
            
            if i % 2 == 0:
                with col1:
                    with st.container():
                        st.markdown(f"""
                        <div style="background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; 
                                   border: 1px solid #e5e7eb; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        """, unsafe_allow_html=True)
                        create_strategy_card_streamlit(name, strategy_data, emoji)
                        st.markdown("</div>", unsafe_allow_html=True)
            else:
                with col2:
                    with st.container():
                        st.markdown(f"""
                        <div style="background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; 
                                   border: 1px solid #e5e7eb; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        """, unsafe_allow_html=True)
                        create_strategy_card_streamlit(name, strategy_data, emoji)
                        st.markdown("</div>", unsafe_allow_html=True)
    
    # 이동평균 설명
    st.markdown("""
    <div class="explanation-box">
        <div class="explanation-title">📈 이동평균이란?</div>
        <div class="explanation-text">
            이동평균은 <strong>최근 N일간의 평균 가격</strong>을 의미합니다. 예를 들어 110일 이동평균은 최근 110일간의 평균 가격입니다.
            <br><br>
            • <strong>매수 신호</strong>: 현재 가격이 이동평균보다 높을 때 → 상승 추세로 판단<br>
            • <strong>매도 신호</strong>: 현재 가격이 이동평균보다 낮을 때 → 하락 추세로 판단<br>
            • <strong>리밸런싱 전략</strong>: BTC와 ETH를 정해진 비율로 섞어서 투자하는 방법
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 누적 수익률 비교 차트
    st.markdown('<div class="chart-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📈 누적 수익률 비교</div>', unsafe_allow_html=True)
    
    fig = go.Figure()
    
    colors = {
        'BTC': '#f7931a',
        'ETH': '#627eea', 
        'Rebal_50_50': '#10b981',
        'Rebal_60_40': '#8b5cf6'
    }
    
    strategy_names = {
        'BTC': 'BTC 단독',
        'ETH': 'ETH 단독', 
        'Rebal_50_50': '50:50 리밸런싱',
        'Rebal_60_40': '60:40 리밸런싱'
    }
    
    for key, name in strategy_names.items():
        if key in results:
            strategy_data = results[key]
            cumulative_dict = strategy_data['cumulative_series']
            
            if cumulative_dict:
                dates = [pd.to_datetime(k) for k in cumulative_dict.keys()]
                values = list(cumulative_dict.values())
                
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=values,
                    name=f"{name} (MA {strategy_data['optimal_ma']}일)",
                    line=dict(color=colors[key], width=2.5),
                    hovertemplate=f"<b>{name}</b><br>" +
                                "날짜: %{x}<br>" +
                                "누적 수익률: %{y:.2f}배<br>" +
                                "<extra></extra>"
                ))
    
    fig.update_layout(
        xaxis_title="",
        yaxis_title="누적 수익률 (배수)",
        hovermode='x unified',
        template='plotly_white',
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.8)"
        ),
        font=dict(size=11, family="Inter"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 차트 설명
    st.markdown("""
    <div class="explanation-text" style="text-align: center; margin-top: 1rem; color: #6b7280;">
        💡 <strong>차트 해석법:</strong> 선이 위로 올라갈수록 수익이 많이 난 것입니다. 
        가장 위에 있는 선이 가장 좋은 성과를 낸 전략입니다.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 상세 성과 테이블
    st.markdown('<div class="chart-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📋 상세 성과 지표</div>', unsafe_allow_html=True)
    
    table_data = []
    
    for key, name in strategy_names.items():
        if key in results:
            strategy_data = results[key]
            cumulative_dict = strategy_data['cumulative_series']
            
            # 기간별 성과 계산
            ret_5y, cagr_5y, mdd_5y = get_period_performance(cumulative_dict, 5)
            ret_1y, cagr_1y, mdd_1y = get_period_performance(cumulative_dict, 1)
            
            # 신호 정보
            signal_info = strategy_data.get('signal', '데이터 부족')
            
            table_data.append({
                '전략': name,
                '최적 MA': f"{strategy_data['optimal_ma']}일",
                '현재 신호': signal_info,
                '스마트 점수': f"{strategy_data['combined_sortino']:.3f}",
                '전체 연평균 수익률': f"{strategy_data['cagr']*100:.1f}%",
                '전체 최대 손실': f"{strategy_data['drawdown']*100:.1f}%",
                '5년 연평균 수익률': f"{cagr_5y:.1f}%" if cagr_5y is not None else "N/A",
                '1년 연평균 수익률': f"{cagr_1y:.1f}%" if cagr_1y is not None else "N/A",
                '위험 대비 수익': f"{strategy_data['sharpe']:.2f}",
                '연간 변동성': f"{strategy_data['volatility']*100:.1f}%"
            })
    
    if table_data:
        df_table = pd.DataFrame(table_data)
        st.dataframe(df_table, use_container_width=True, hide_index=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 설명 섹션
    st.markdown('<div class="chart-section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📖 쉬운 용어 설명</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 투자 전략 설명
        - **BTC/ETH 단독**: 비트코인이나 이더리움 하나만 투자하는 방법
        - **리밸런싱**: 두 개 암호화폐를 정해진 비율로 섞어서 투자
        - **50:50**: BTC 50%, ETH 50%로 투자
        - **60:40**: BTC 60%, ETH 40%로 투자
        
        ### 📊 매수/매도 신호
        - **매수**: 지금 사면 좋다는 신호 (가격이 상승 추세)
        - **매도**: 지금 팔고 현금으로 보관하라는 신호 (가격이 하락 추세)
        - **이동평균**: 최근 N일간의 평균 가격으로 추세를 판단
        """)
    
    with col2:
        st.markdown("""
        ### 📈 성과 지표 쉬운 설명
        - **연평균 수익률**: 1년 동안 평균적으로 얻는 수익률
        - **최대 손실**: 투자 기간 중 가장 큰 손실률 (낮을수록 좋음)
        - **위험 대비 수익**: 위험 대비 얼마나 좋은 수익을 내는지 (높을수록 좋음)
        - **변동성**: 가격이 얼마나 많이 오르락내리락 하는지 (낮을수록 안정적)
        - **스마트 점수**: 종합적인 투자 전략 우수성 (높을수록 좋음)
        
        ### ⚠️ 주의사항
        - 과거 성과가 미래 수익을 보장하지 않습니다
        - 투자는 본인 책임이며, 충분한 공부 후 결정하세요
        - 이 분석은 교육 목적으로 제작되었습니다
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

