import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 設定 ---
DATA_FILE = 'study_log.csv'

# --- 関数: データの読み込み ---
def load_data():
    if not os.path.exists(DATA_FILE):
        # ファイルがない場合は空のデータフレームを作成
        return pd.DataFrame(columns=['ユーザー名', '科目', '時間(分)', '日時'])
    return pd.read_csv(DATA_FILE)

# --- 関数: データの保存 ---
def save_data(user, subject, minutes):
    df = load_data()
    new_data = pd.DataFrame({
        'ユーザー名': [user],
        '科目': [subject],
        '時間(分)': [minutes],
        '日時': [datetime.now().strftime('%Y-%m-%d %H:%M')]
    })
    # データを結合してCSVに保存
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

# --- メイン画面の構成 ---
st.set_page_config(page_title="Study Battle 🔥", page_icon="📚")

st.title("📚 Study Battle 🔥")
st.markdown("勉強時間を記録して、ライバルと競い合おう！")

# 1. サイドバー：入力フォーム
st.sidebar.header("✏️ 学習記録をつける")
user_name = st.sidebar.text_input("名前（ニックネーム）")
subject = st.sidebar.selectbox("科目", ["数学", "英語", "国語", "理科", "社会", "プログラミング", "その他"])
study_time = st.sidebar.number_input("勉強時間（分）", min_value=1, step=10, value=60)

if st.sidebar.button("投稿する"):
    if user_name:
        save_data(user_name, subject, study_time)
        st.sidebar.success(f"{user_name}さんの記録（{subject} {study_time}分）を保存しました！")
        # 画面をリロードしてデータを反映させるためのおまじない
        st.rerun() 
    else:
        st.sidebar.error("名前を入力してください！")

# データを読み込む
df = load_data()

# データがある場合のみ表示
if not df.empty:
    
    # 2. ランキングセクション（アプリの目玉機能）
    st.header("🏆 現在のランキング")
    
    # ユーザーごとの合計時間を計算
    ranking_df = df.groupby('ユーザー名')['時間(分)'].sum().reset_index()
    ranking_df = ranking_df.sort_values('時間(分)', ascending=False) # 降順に並び替え
    
    # 上位3名を目立たせる
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("### 順位表")
        # インデックスを1から始まる順位にする
        ranking_display = ranking_df.copy()
        ranking_display.index = range(1, len(ranking_display) + 1)
        st.table(ranking_display)

    with col2:
        st.write("### 勉強時間グラフ")
        st.bar_chart(ranking_df.set_index('ユーザー名'))

    st.divider() # 区切り線

    # 3. タイムライン（みんなの投稿）
    st.subheader("📝 みんなの学習ログ")
    
    # 最新の投稿が上に来るように並び替え
    recent_logs = df.sort_values('日時', ascending=False)
    
    for index, row in recent_logs.iterrows():
        # カードのような見た目で表示
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 2, 1])
            c1.markdown(f"**👤 {row['ユーザー名']}**")
            c2.text(f"📖 {row['科目']} を {row['時間(分)']}分 勉強しました")
            c3.caption(f"{row['日時']}")

else:
    st.info("まだ記録がありません。サイドバーから最初の投稿をしてみましょう！")