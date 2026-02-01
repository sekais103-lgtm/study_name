import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 設定 ---
st.set_page_config(page_title="Study Battle 🔥", page_icon="👑", layout="centered")

# --- 関数: データの読み込み (スプレッドシート) ---
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        # キャッシュを使わずに常に最新を取りに行く(ttl=0)
        df = conn.read(worksheet="Sheet1", ttl=0)
        # 空の場合やエラー対策
        if df.empty:
             return pd.DataFrame(columns=['ユーザー名', '科目', '時間', '日付', '日時詳細'])
        return df
    except:
        return pd.DataFrame(columns=['ユーザー名', '科目', '時間', '日付', '日時詳細'])

# --- 関数: データの保存 ---
def save_data(user, subject, minutes):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = load_data()
    
    now = datetime.now()
    new_data = pd.DataFrame({
        'ユーザー名': [user],
        '科目': [subject],
        '時間': [minutes],
        '日付': [now.strftime('%Y-%m-%d')], # 集計用
        '日時詳細': [now.strftime('%Y-%m-%d %H:%M:%S')] # 表示用
    })
    
    updated_df = pd.concat([df, new_data], ignore_index=True)
    conn.update(worksheet="Sheet1", data=updated_df)

# --- UI: ログイン画面（簡易版） ---
def login_screen(df):
    st.title("🎓 Study Battle Login")
    
    # 既存ユーザーから選ぶ
    existing_users = []
    if not df.empty and 'ユーザー名' in df.columns:
        existing_users = df['ユーザー名'].unique().tolist()
    
    st.write("過去のユーザーから選択、または新規登録")
    
    col1, col2 = st.columns(2)
    with col1:
        # 既存ユーザー選択
        selected_user = st.selectbox("自分の名前を選ぶ", ["選択してください"] + existing_users)
    
    with col2:
        # 新規ユーザー入力
        new_user = st.text_input("または新しい名前を入力")

    if st.button("ログイン / スタート", type="primary", use_container_width=True):
        if new_user:
            st.session_state['user_name'] = new_user
            st.rerun()
        elif selected_user != "選択してください":
            st.session_state['user_name'] = selected_user
            st.rerun()
        else:
            st.warning("名前を選択するか入力してください")

# --- メイン処理 ---
def main():
    # データをロード
    df = load_data()

    # ログインチェック
    if 'user_name' not in st.session_state:
        login_screen(df)
        return

    # ログイン中のユーザー名
    current_user = st.session_state['user_name']
    
    # --- ヘッダー ---
    c1, c2 = st.columns([3, 1])
    with c1:
        st.write(f"お疲れ様です、**{current_user}** さん！ 👋")
    with c2:
        # ここを修正しました
        if st.button("ログアウト"):
            del st.session_state['user_name']
            st.rerun()

    st.divider()

    # --- 1. 入力フォーム (スマホで見やすくアコーディオン化) ---
    with st.expander("✏️ 勉強記録をつける", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            subject = st.selectbox("科目", ["数学", "英語", "国語", "理科", "社会", "プログラミング", "その他"])
        with c2:
            study_time = st.number_input("時間 (分)", min_value=1, step=5, value=30)
        
        if st.button("投稿する 🔥", use_container_width=True, type="primary"):
            save_data(current_user, subject, study_time)
            st.success("記録しました！")
            st.rerun()

    # --- 2. ランキング (タブで切り替え) ---
    st.subheader("👑 ランキング")
    
    if not df.empty:
        # データ型の調整（エラー防止）
        df['時間'] = pd.to_numeric(df['時間'], errors='coerce').fillna(0)
        
        tab1, tab2 = st.tabs(["📅 今日の1位", "🏆 総合ランキング"])

        # 今日の日付
        today_str = datetime.now().strftime('%Y-%m-%d')

        with tab1:
            # 今日のデータで集計
            today_df = df[df['日付'] == today_str]
            if not today_df.empty:
                daily_ranking = today_df.groupby('ユーザー名')['時間'].sum().reset_index().sort_values('時間', ascending=False)
                
                # 1位の取得
                top_user = daily_ranking.iloc[0]['ユーザー名']
                top_score = daily_ranking.iloc[0]['時間']
                
                # 自分なら祝う
                if top_user == current_user:
                    st.balloons()
                    st.markdown(f"""
                    <div style="text-align: center; color: #FFD700;">
                        <h1>Congratulations!!</h1>
                        <h2>👑 今日のキングはあなたです！ 👑</h2>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"### 👑 今日の暫定1位: **{top_user}** ({top_score}分)")

                st.table(daily_ranking.set_index('ユーザー名'))
            else:
                st.info("今日はまだ誰も記録していません。一番乗りを目指そう！")

        with tab2:
            # 全期間で集計
            total_ranking = df.groupby('ユーザー名')['時間'].sum().reset_index().sort_values('時間', ascending=False)
            
            # 1位の取得
            if not total_ranking.empty:
                top_user_all = total_ranking.iloc[0]['ユーザー名']
                
                # 自分が総合1位なら雪のエフェクト
                if top_user_all == current_user:
                    st.snow()
                    st.markdown(f"<h3 style='color:orange; text-align:center;'>Excellent! You are the Legend! 🏆</h3>", unsafe_allow_html=True)

                # グラフ表示（スマホで見やすいように横棒グラフ）
                st.bar_chart(total_ranking.set_index('ユーザー名'), color="#FF4B4B")
                st.table(total_ranking.set_index('ユーザー名'))

    # --- 3. タイムライン ---
    st.divider()
    st.caption("みんなの足跡")
    if not df.empty:
        # 最新10件を表示
        if '日時詳細' in df.columns:
            recent_logs = df.sort_values('日時詳細', ascending=False).head(10)
            for _, row in recent_logs.iterrows():
                # 日時がある場合のみ表示
                time_str = str(row['日時詳細'])
                display_time = time_str[5:-3] if len(time_str) > 10 else time_str
                st.text(f"{row['ユーザー名']}: {row['科目']} ({row['時間']}分) - {display_time}")

if __name__ == "__main__":
    main()
