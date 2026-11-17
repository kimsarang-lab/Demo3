from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='위고비 치료와 사망보험금 | 데모 3',page_icon='🔎',layout='wide')
st.markdown("""<style>
.block-container{max-width:1250px;padding-top:2rem}
h1{letter-spacing:-1.5px;font-size:2.7rem!important;line-height:1.25!important}
div[data-testid="stMetric"]{background:#eef5f8;border-radius:16px;padding:20px}
</style>""",unsafe_allow_html=True)

def people_grid(rate, color):
    # Fractional rates use a partial icon; each icon represents one percentage point.
    icons=[]
    for i in range(100):
        portion=max(0,min(1,rate*100-i))
        shape='<circle cx="10" cy="5" r="3.2"/><path d="M5 10 Q10 7 15 10 L16 20 L13 20 L12 29 L8 29 L7 20 L4 20 Z"/>'
        icons.append(f'<svg viewBox="0 0 20 32" role="presentation"><g fill="#dce5ed">{shape}</g><svg x="0" y="0" width="{portion*20}" height="32" viewBox="0 0 {max(portion*20,.001)} 32" overflow="hidden"><g fill="{color}">{shape}</g></svg></svg>')
    st.html('<div style="display:grid;grid-template-columns:repeat(20,minmax(0,1fr));gap:5px;max-width:520px;margin:16px 0" aria-label="100명 중 '+f'{rate*100:g}명 치료 시작 가정'+'">'+''.join(icons)+'</div>')

def evidence_path(a,r):
    cards=[('01','임상연구','문헌에서 확인한 치료 효과',f'사망 위험비 {a.hazard_ratio:g}'),('02','가입자 집단','임상시험과 비슷한 조건',f'{r.eligible_count:,.0f}명 / {a.population:,.0f}명'),('03','보험금 변화','같은 집단 · 다른 치료 시작률',f'{a.horizon_years:g}년간의 차이 추정')]
    html='<style>.evidence{display:flex;gap:14px;align-items:stretch;margin:16px 0}.evcard{flex:1;padding:24px;border:1px solid #d9e6ed;border-radius:18px;background:#f8fbfd}.evnum{font:700 13px sans-serif;color:#07877f}.evtitle{font:700 23px sans-serif;color:#18314c;margin:10px 0}.evdetail{font:14px sans-serif;color:#60748a;line-height:1.7}.evvalue{margin-top:16px;padding-top:14px;border-top:1px solid #dce7ec;color:#143e54;font-weight:700}.evarrow{align-self:center;color:#16877f;font-size:24px}@media(max-width:650px){.evidence{flex-direction:column}.evarrow{transform:rotate(90deg)}}</style><div class="evidence">'
    for i,(num,title,detail,val) in enumerate(cards):
        if i:html+='<div class="evarrow">→</div>'
        html+=f'<div class="evcard"><div class="evnum">{num}</div><div class="evtitle">{title}</div><div class="evdetail">{detail}</div><div class="evvalue">{val}</div></div>'
    st.html(html+'</div>')

st.caption('DEMO 03 · 임상연구에서 보험금 변화까지')
st.title('위고비 치료를 시작하는 사람이 늘면,\n사망보험금은 얼마나 달라질까?')
st.write('임상연구에서 얻은 치료 효과를 가상 보험가입자 집단에 적용했습니다. 치료를 시작하는 사람이 적을 때와 많을 때, 10년 동안 예상되는 차이를 비교해 보세요.')
st.caption('연구 결과 시연 · 제공된 분석값 사용 · 실제 관찰 결과가 아닌 모형 추정치')
base=Path(__file__).parent/'data'
st.sidebar.header('비교할 조건')
with st.sidebar.expander('연구자용 · 결과 CSV 교체'):
 upload=st.file_uploader('summary.csv 업로드',type='csv',help='차이값만 미리보기합니다. 공통 가정은 data/assumptions.csv를 함께 관리하세요.')
try:
 summary=pd.read_csv(upload if upload is not None else base/'summary.csv')
 details=pd.read_csv(base/'details.csv')
 assumptions=pd.read_csv(base/'assumptions.csv')
 req=['share_pct','eligible_count','additional_starters','deaths_reduced','nominal_reduction_krw','pv_reduction_krw','data_status','source_note']
 if set(req)-set(summary): raise ValueError('summary.csv 필수 열이 누락되었습니다.')
 numeric=req[:6]
 for c in numeric: summary[c]=pd.to_numeric(summary[c],errors='raise')
 if summary.empty or summary[req].isna().any().any() or not np.isfinite(summary[numeric].to_numpy()).all(): raise ValueError('차이값에는 빈칸 또는 무한값을 사용할 수 없습니다.')
 if summary.share_pct.duplicated().any(): raise ValueError('집단 비율이 중복되었습니다.')
 if not summary.share_pct.between(0,100).all() or (summary.eligible_count<=0).any(): raise ValueError('비율 또는 후보 인원을 확인하세요.')
 areq=['population','min_age','horizon_years','death_benefit_krw','low_start_probability','high_start_probability','hazard_ratio','effect_years','discount_rate']
 if len(assumptions)!=1 or set(areq)-set(assumptions): raise ValueError('assumptions.csv에는 공통 가정 한 행이 필요합니다.')
 a=assumptions.iloc[0]
 if not np.isfinite(a[areq].astype(float)).all() or a.population<=0 or a.horizon_years<=0: raise ValueError('공통 가정을 확인하세요.')
 if not np.allclose(summary.eligible_count,a.population*summary.share_pct/100): raise ValueError('후보 수와 전체 인원×비율이 일치하지 않습니다.')
 dreq=['share_pct','scenario','start_probability','starters','deaths','death_benefit_pv_krw','scope']
 if set(dreq)-set(details): raise ValueError('details.csv 필수 열이 누락되었습니다.')
 if details.duplicated(['share_pct','scenario']).any(): raise ValueError('상세값의 비율·시나리오가 중복됩니다.')
 if not set(details.scenario).issubset({'저확산','고확산'}): raise ValueError('상세 시나리오 이름을 확인하세요.')
 for c in ['share_pct','start_probability','starters','deaths','death_benefit_pv_krw']:
  details[c]=pd.to_numeric(details[c],errors='raise')
  if not np.isfinite(details[c]).all() or (details[c]<0).any(): raise ValueError('상세값은 유한한 비음수여야 합니다.')
except Exception as e:
 st.error(f'CSV를 읽을 수 없습니다: {e}');st.stop()
options=sorted(summary.share_pct.tolist())
share=st.sidebar.radio('임상시험과 비슷한 조건의 가입자는?',options,index=options.index(.3) if .3 in options else 0,format_func=lambda x:f'{a.population*x/100:,.0f}명 ({x:g}%)')
st.sidebar.caption(f'전체 가상 가입자 {a.population:,.0f}명 중 치료 효과를 적용할 후보입니다. 위험이 낮은 집단과 높은 집단을 나누는 선택이 아닙니다.')
r=summary[summary.share_pct==share].iloc[0]
if '가상' in str(r.data_status): st.warning('현재 선택한 결과는 가상 예시값입니다. 실제 분석 결과와 구분해 주세요.')
st.caption(f'공통 조건: {a.min_age:g}세 이상 {a.population:,.0f}명 · {a.horizon_years:g}년 · 사망보험금 1인당 {a.death_benefit_krw/100000000:g}억 원')

st.subheader('01  임상연구의 결과를 보험의 관점으로 연결했습니다')
evidence_path(a,r)
st.info('직접 관찰하기 어려운 장기 보험금 변화를, 임상연구의 근거와 대상자 규모를 연결한 모형으로 살펴봅니다.')
with st.expander('체계적 문헌고찰·메타분석은 어떻게 연결되나요?'):
 st.write('체계적 문헌고찰과 메타분석은 치료 효과의 근거를 검토하고 종합하는 데 활용할 수 있습니다. 이 화면에서는 그 근거를 보험가입자 집단에 적용했을 때의 결과를 보여줍니다.')
 st.write('현재 제공된 모형의 HR 0.81은 SELECT 임상시험 기반 입력값입니다. 메타분석으로 산출한 통합 효과값으로 표시하지 않습니다. 최종 연구의 통합 효과값을 적용하려면 해당 값으로 다시 계산한 결과표가 필요합니다.')

st.subheader('02  같은 가입자 집단에서, 치료 시작만 달라지면?')
st.write('두 상황의 가입자 조건과 치료 효과는 같습니다. **매년 치료를 시작할 확률**만 다르게 가정합니다.')
for col,title,rate in zip(st.columns(2),['치료를 시작하는 사람이 적을 때','치료를 시작하는 사람이 많을 때'],[a.low_start_probability,a.high_start_probability]):
 with col,st.container(border=True):
  st.markdown('### '+title)
  st.metric('매년 치료를 시작할 확률',f'{rate:.0%}')
  people_grid(rate, '#7b8ea7' if rate==a.low_start_probability else '#068a80')
  st.write(f'모형에서 그해 치료 시작 대상인 사람 **100명 중 약 {rate*100:g}명**이 시작한다고 가정합니다.')
  st.caption(f'임상시험과 비슷한 조건의 가입자: {r.eligible_count:,.0f}명으로 동일')
st.caption('사람 아이콘 1개 = 그해 치료 시작 대상 1명 · 100명으로 환산한 확률 그림이며 실제 연간 시작자 수가 아닙니다.')
st.caption('치료 시작확률은 비교를 위한 가정이며, 국내에서 관찰된 치료 시작률이 아닙니다. 특약 가입 여부에 따른 차이를 뜻하지 않습니다.')

st.subheader(f'03  치료 시작이 늘어나면, {a.horizon_years:g}년 동안 무엇이 달라질까요?')
c=st.columns(3)
c[0].metric('추가로 치료를 시작하는 사람',f'{r.additional_starters:,.2f}명')
c[1].metric('예상 사망 건수 감소',f'{r.deaths_reduced:,.2f}건')
c[2].metric('예상 사망보험금 감소 · 현재 가치',f'약 {r.pv_reduction_krw/10000:,.0f}만 원')
st.caption('위 결과는 선택한 집단 규모에서의 두 시나리오 차이입니다. 소수점 인원·건수는 모형의 기대값이며 실제 사람 수를 뜻하지 않습니다. 음수라면 표시한 방향과 반대입니다.')
st.html(f"""<div style="background:#103e4e;color:white;border-radius:20px;padding:28px;margin:20px 0;display:flex;align-items:center;flex-wrap:wrap;gap:25px">
<div style="flex:1;min-width:200px"><div style="font-size:14px;color:#b8d6df">{a.horizon_years:g}년간 예상 사망보험금 감소 · 현재 가치</div><div style="font-size:34px;font-weight:750;margin-top:10px">{r.pv_reduction_krw/10000:,.0f}만 원</div></div>
<div style="font-size:18px;color:#b8d6df">÷ 전체 가입자 {a.population:,.0f}명 →</div>
<div style="flex:1;min-width:170px"><div style="font-size:14px;color:#b8d6df">전체 가입자 1인당</div><div style="font-size:44px;font-weight:750;color:#83e2cc">약 {r.pv_reduction_krw/a.population:,.0f}원</div></div></div>""")
st.caption(f'위 금액은 {a.horizon_years:g}년 전체의 보험금 차이입니다. 개인이 받는 지원금 또는 매년 줄어드는 금액이 아닙니다.')
with st.expander('금액의 의미와 다른 기준으로 보기'):
 st.write('현재 가치는 미래에 지급할 보험금을 지금 시점의 금액으로 환산한 값입니다.')
 st.metric('할인을 적용하기 전 사망보험금 감소',f'약 {r.nominal_reduction_krw/10000:,.0f}만 원')
 unit=st.selectbox('현재 가치 감소액을 나눠 볼 기준',['전체 가입자 1인당','효과 적용 후보 1인당','추가 치료 시작자 1인당'])
 den={'전체 가입자 1인당':a.population,'효과 적용 후보 1인당':r.eligible_count,'추가 치료 시작자 1인당':r.additional_starters}[unit]
 if den>0: st.metric(unit,f'약 {r.pv_reduction_krw/den:,.0f}원')
 else: st.info('분모가 0 이하인 경우에는 환산하지 않습니다.')
 st.caption('기간 전체의 차이를 나눈 참고값입니다. 개인에게 보장되는 절감액이나 개인별 인과효과가 아닙니다.')

st.subheader('04  왜 전체 가입자 기준의 변화는 작게 나타날까요?')
left,right=st.columns([2,1])
with left:
 st.markdown(f'**전체 {a.population:,.0f}명 중, 색칠된 부분만 효과 적용 후보**')
 count=1000
 selected=count*share/100
 idx=np.arange(count)
 frac=np.clip(selected-idx,0,1)
 fig=go.Figure(go.Scatter(x=idx%50,y=-(idx//50),mode='markers',marker=dict(size=7,color=frac,colorscale=[[0,'#e0e7ef'],[1,'#068a80']],cmin=0,cmax=1,line=dict(width=0)),customdata=frac,hovertemplate='한 점: 전체 가입자 '+f'{a.population/count:g}'+'명<extra></extra>'))
 fig.update_layout(height=270,margin=dict(l=4,r=4,t=10,b=10),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',xaxis=dict(visible=False,fixedrange=True),yaxis=dict(visible=False,fixedrange=True),showlegend=False)
 st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False},key='cohort_grid')
 st.caption(f'점 1개 = {a.population/count:g}명 · 전체 1,000개 점 중 {selected:g}개에 해당하는 비중을 강조합니다. 소수점 점은 색 농도로 표시합니다.')
with right:
 st.markdown('**효과를 적용할 후보**')
 st.metric('전체 가입자 중 비중',f'{share:g}%')
 st.markdown(f'### {r.eligible_count:,.0f}명')
 st.caption('청록색: 임상시험과 비슷한 조건\n\n회색: 이 모형에서 치료 효과를 적용하지 않는 가입자')
with st.container(border=True):
 st.markdown('**그 후보 중에서도, 추가로 치료를 시작하는 사람은 일부입니다.**')
 ratio=r.additional_starters/r.eligible_count
 st.metric('두 시나리오의 누적 치료 시작자 차이',f'{r.additional_starters:,.2f}명')
 if 0<=ratio<=1:
  st.progress(float(ratio))
  st.caption(f'효과 적용 후보 {r.eligible_count:,.0f}명의 약 {ratio:.1%}에 해당하는 규모입니다. 연간 치료 시작률이 아닌 {a.horizon_years:g}년간 두 시나리오의 누적 차이입니다.')
 else:
  st.caption('추가 치료 시작자 차이는 제공된 분석값 그대로 표시합니다.')
st.write('치료 효과를 모든 가입자에게 적용하지 않으며, 효과 적용 후보 중에서도 일부만 추가로 치료를 시작합니다. 따라서 현재 가정에서는 전체 가입자 수준의 보험금 변화가 제한적으로 나타납니다.')
chart=summary.sort_values('share_pct').copy()
chart['효과 적용 후보']=chart.apply(lambda x:f'{x.eligible_count:,.0f}명 ({x.share_pct:g}%)',axis=1)
chart['현재 가치 감소액(만 원)']=chart.pv_reduction_krw/10000
fig=px.bar(chart,x='효과 적용 후보',y='현재 가치 감소액(만 원)',text='현재 가치 감소액(만 원)')
fig.update_traces(marker_color=['#14877c' if x==share else '#cedce7' for x in chart.share_pct],texttemplate='%{y:,.0f}만 원',textposition='outside',hovertemplate='%{x}<br>현재 가치 감소: %{y:,.0f}만 원<extra></extra>')
fig.update_layout(height=330,margin=dict(t=40),yaxis=dict(rangemode='tozero'))
st.plotly_chart(fig,use_container_width=True)
st.caption('효과 적용 후보 규모별 분석 결과 · 강조된 막대가 현재 선택한 조건입니다.')

with st.expander('분석 근거·가정·해석 안내'):
 st.write(f'데이터 구분: {r.data_status}')
 st.write(f'출처 메모: {r.source_note}')
 st.markdown('''- 이 앱은 제공된 반올림 분석값을 표시합니다. 원본 분석파일 검증이나 사망모형 재계산은 수행하지 않습니다.
- 현재 HR 0.81은 SELECT 임상시험 기반의 입력값이며, 국내 치료 효과 또는 메타분석 통합 추정값이 아닙니다.
- SELECT 유사 집단 추정의 근거 표본은 12명으로 작습니다. 유사 집단은 모든 비만인 또는 BMI 기준만 충족한 모든 사람과 같지 않습니다.
- 연 1%·3%는 시나리오 가정입니다. 특약 있음/없음의 인과효과를 비교하지 않습니다.
- 명목 감소액은 반올림된 사망 감소 건수에 사망보험금을 곱한 값입니다. 현재 가치 감소액은 별도로 제공된 분석값입니다.
- 원래 제공된 좌우 사망 건수·보험금 총액은 집계 대상 확인이 필요해 본 화면에서는 표시하지 않습니다. 차이값은 제공된 결과표를 사용합니다.
- 결과는 분석기간 내의 변화이며, 평생 보험금 감소 또는 약제비 특약의 수익성을 입증하지 않습니다.
- 가정 파일만 바꿔도 결과가 재계산되지 않습니다. 같은 가정으로 산출한 결과 CSV를 함께 교체해야 합니다.''')
 st.dataframe(assumptions,use_container_width=True,hide_index=True)
with st.expander('연구자용 · 결과표 확인 및 내려받기'):
 st.dataframe(summary,use_container_width=True,hide_index=True)
 st.download_button('분석 결과 CSV 다운로드',summary.to_csv(index=False).encode('utf-8-sig'),'summary.csv','text/csv')
