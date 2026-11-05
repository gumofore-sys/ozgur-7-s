import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression

st.set_page_config(page_title="7S Hibrit Bot",page_icon="📊",layout="wide")
st.title("📊 Ücretsiz 7 Saniyelik Hibrit Analiz Botu")
st.caption("Teknik analiz + istatistiksel model + kronolojik test. Otomatik işlem açmaz.")
st.warning("Kazanç garantisi yoktur. 7 saniyelik tahmin çok zordur. Önce demo kullanın; Martingale yapmayın. OTC ve gerçek piyasa verilerini ayrı test edin.")
st.download_button("Örnek CSV şablonunu indir","timestamp,price,market\n2026-01-01 10:00:00.000,1.10000,REAL\n2026-01-01 10:00:00.250,1.10002,REAL\n","ornek_fiyat_verisi.csv","text/csv")
f=st.file_uploader("Timestamp ve price sütunlu fiyat CSV dosyanı yükle",type=["csv"])
if not f:
 st.info("Not: Pocket Option işlem geçmişi Excel'i tek başına fiyat yönü eğitimi için yeterli değildir. Tick/saniyelik fiyat verisi gerekir.")
 st.stop()
raw=pd.read_csv(f); cols=list(raw.columns)
c1,c2,c3=st.columns(3)
tc=c1.selectbox("Zaman sütunu",cols,cols.index("timestamp") if "timestamp" in cols else 0)
pc=c2.selectbox("Fiyat sütunu",cols,cols.index("price") if "price" in cols else min(1,len(cols)-1))
mc=c3.selectbox("Piyasa sütunu",["Yok"]+cols,("market" if "market" in cols else "Yok"))
payout=st.slider("Ödeme oranı (%)",50,95,80)
test_pct=st.slider("Son dönem test yüzdesi",20,40,30)
conf_min=st.slider("Sinyal güven eşiği (%)",50,90,60)
d=raw.copy(); d["_t"]=pd.to_datetime(d[tc],errors="coerce",utc=True); d["_p"]=pd.to_numeric(d[pc],errors="coerce")
d=d.dropna(subset=["_t","_p"]).sort_values("_t").drop_duplicates("_t").reset_index(drop=True)
d["_market"]=d[mc].astype(str).str.upper().str.strip() if mc!="Yok" else "UNSPECIFIED"
if len(d)<100: st.error("Temizlenmiş veri 100 satırdan az."); st.stop()
market=st.selectbox("Piyasayı ayrı seç",sorted(d["_market"].unique()))
d=d[d["_market"]==market].copy().reset_index(drop=True)
p=d["_p"]
for n in [1,2,3,5,10,20]: d[f"ret{n}"]=p.pct_change(n)
d["ema20"]=p.ewm(span=20,adjust=False).mean(); d["ema50"]=p.ewm(span=50,adjust=False).mean()
d["ema_gap"]=(d.ema20-d.ema50)/p.replace(0,np.nan)
delta=p.diff(); gain=delta.clip(lower=0).ewm(alpha=1/7,adjust=False).mean(); loss=(-delta.clip(upper=0)).ewm(alpha=1/7,adjust=False).mean()
d["rsi7"]=100-100/(1+gain/loss.replace(0,np.nan))
d["vol5"]=d.ret1.rolling(5).std(); d["vol20"]=d.ret1.rolling(20).std()
d["range20"]=(p-p.rolling(20).min())/(p.rolling(20).max()-p.rolling(20).min()).replace(0,np.nan)
d["mom3"]=p.pct_change(3); d["mom10"]=p.pct_change(10)
tn=d["_t"].astype("int64").to_numpy(); ix=np.searchsorted(tn,tn+7_000_000_000,side="left")
future=np.full(len(d),np.nan); ok=ix<len(d); future[ok]=p.to_numpy()[ix[ok]]
d["future"]=future; d["y"]=np.where(d.future>p,1,np.where(d.future<p,0,np.nan))
features=["ret1","ret2","ret3","ret5","ret10","ret20","ema_gap","rsi7","vol5","vol20","range20","mom3","mom10"]
ds=d.replace([np.inf,-np.inf],np.nan).dropna(subset=features+["y"]).copy(); ds["y"]=ds.y.astype(int)
a,b,c=st.columns(3); a.metric("Fiyat kaydı",f"{len(d):,}"); b.metric("Etiketli örnek",f"{len(ds):,}"); c.metric("Piyasa",market)
if len(ds)<300 or ds.y.nunique()<2: st.error("Yeterli örnek veya iki yönlü sonuç yok. 1.000+ etiketli örnek hedefleyin."); st.stop()
split=int(len(ds)*(1-test_pct/100)); train=ds.iloc[:split]; test=ds.iloc[split:]
if len(train)<100 or len(test)<50 or train.y.nunique()<2: st.error("Eğitim/test bölümü yetersiz."); st.stop()
model=Pipeline([("impute",SimpleImputer(strategy="median")),("scale",StandardScaler()),("lr",LogisticRegression(max_iter=1500,class_weight="balanced"))])
model.fit(train[features],train.y)
prob=model.predict_proba(test[features])[:,1]; pred=(prob>=.5).astype(int)
test=test.copy(); test["prob_up"]=prob; test["confidence"]=np.maximum(prob,1-prob); test["correct"]=(pred==test.y).astype(int)
sig=test[test.confidence>=conf_min/100]; n=len(sig); wins=int(sig.correct.sum()); wr=wins/n*100 if n else np.nan
be=100/(1+payout/100); ev=(wr/100)*(payout/100)-(1-wr/100) if n else np.nan
def wilson(k,n):
 if not n:return (np.nan,np.nan)
 z=1.96; q=k/n; den=1+z*z/n; center=(q+z*z/(2*n))/den; half=z*np.sqrt((q*(1-q)+z*z/(4*n))/n)/den
 return ((center-half)*100,(center+half)*100)
lo,hi=wilson(wins,n)
st.subheader("Görülmemiş son dönem testi")
x1,x2,x3,x4=st.columns(4); x1.metric("Test örneği",len(test)); x2.metric("Eşik üstü sinyal",n); x3.metric("Win rate",f"{wr:.2f}%" if n else "Sinyal yok"); x4.metric("Başa baş",f"{be:.2f}%")
if n:
 st.write(f"Yaklaşık %95 güven aralığı: **{lo:.1f}%–{hi:.1f}%**")
 st.write(f"Teorik beklenti: **işlem başına {ev*100:+.2f}%** (maliyet ve gecikme hariç).")
 if ev>0 and lo>be: st.success("Bu test olumlu görünüyor; yeni ve bağımsız demo verisiyle tekrar doğrula.")
 elif ev>0: st.warning("Nokta tahmini pozitif ama belirsizlik yüksek; avantaj kanıtlanmadı.")
 else: st.error("Test beklentisi negatif. Gerçek parayla kullanma.")
else: st.warning("Güven eşiğini geçen sinyal yok. İşlem açmamak doğru olabilir.")
fig=px.line(test.tail(1500),x="_t",y="prob_up",title="Test döneminde yukarı olasılığı"); fig.add_hline(y=.5,line_dash="dash"); st.plotly_chart(fig,use_container_width=True)
out=test[["_t","_p","future","y","prob_up","confidence","correct"]].copy()
st.download_button("Test sonuçlarını CSV indir",out.to_csv(index=False).encode("utf-8-sig"),"7s_test_sonuclari.csv","text/csv")
last=d.replace([np.inf,-np.inf],np.nan).dropna(subset=features).tail(1)
if len(last):
 q=float(model.predict_proba(last[features])[:,1][0]); st.subheader("Son veri noktasının model tahmini")
 st.metric("Yukarı olasılığı",f"%{q*100:.1f}"); st.metric("Model yönü","YUKARI" if q>=.5 else "AŞAĞI"); st.metric("Güven",f"%{max(q,1-q)*100:.1f}")
 st.caption("Son satır tahmini canlı sinyal değildir; CSV'nin son gözleminden hesaplanır.")
st.caption("Model: lojistik regresyon + EMA/RSI/momentum/volatilite özellikleri. Son dönem test seti eğitimde kullanılmaz. Bu araştırma aracıdır, finansal tavsiye değildir.")
