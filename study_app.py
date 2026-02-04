import streamlit as st
import pandas as pd
from datetime import datetime
import time
from supabase import create_client, Client

# --- 設定 ---
st.set_page_config(page_title="Study Battle 🔥", page_icon="👑", layout="centered")

# --- 関数: Supabaseクライアントの初期化 ---
# リソースを節約するためキャッシュ化
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_supabase()

# --- 関数: データの読み込み (Supabase版) ---
def load_data():
    try:
        # Supabaseから全データを取得
        response = supabase.table("study_logs").select("*").execute()
        
        # データがない場合の処理
        if not response.data:
            return pd.DataFrame(columns=['ユーザー名', '科目', '時間', '日付', '日時詳細'])
        
        # データをDataFrameに変換
        df = pd.DataFrame(response.data)
        
        # Supabaseの英語カラム名を、アプリで使う日本語名にリネーム
        df = df.rename(columns={
            'user_name': 'ユーザー名',
            'subject': '科目',
            'study_time': '時間',
            'study_date': '日付',
            'created_at': '日時詳細'
        })
        
        # 日時詳細はUTC(世界標準時)で返ってくることが多いので、見やすく調整（簡易的）
        # 必要に応じて pd.to_datetime で変換などを行いますが、
        # 今回は表示用としてそのまま、あるいは文字列として扱います
        
        return df
    except Exception as e:
        # エラー時は空のデータを返す（デバッグ用にエラー表示しても良い）
        st.error(f"データ読み込みエラー: {e}")
        return pd.DataFrame(columns=['ユーザー名', '科目', '時間', '日付', '日時詳細'])

# --- 関数: データの保存 (Supabase版) ---
def save_data(user, subject, minutes):
    try:
        now = datetime.now()
        
        # データベースに挿入するデータ
        data = {
            "user_name": user,
            "subject": subject,
            "study_time": minutes,
            "study_date": now.strftime('%Y-%m-%d'),
            # created_atはSupabaseが自動で入れることもできますが、
            # タイムゾーンを日本時間に合わせるため明示的に入れてもOK
            # ここではSupabaseのデフォルト(自動)に任せるか、現在時刻を入れる
            "created_at": now.isoformat() 
        }
        
        # Insert実行 (行を追加するだけなので競合しない！)
        supabase.table("study_logs").insert(data).execute()
        
    except Exception as e:
        st.error(f"保存エラー: {e}")
        raise e

# --- UI: ログイン画面 (変更なし) ---
def login_screen(df):
    st.title("🎓 Study Battle Login")
    
    existing_users = []
    if not df.empty and 'ユーザー名' in df.columns:
        existing_users = df['ユーザー名'].unique().tolist()
    
    st.write("過去のユーザーから選択、または新規登録")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_user = st.selectbox("自分の名前を選ぶ", ["選択してください"] + existing_users)
    
    with col2:
        new_user = st.text_input("または新しい名前を入力")

    if st.button("ログイン / スタート", type="primary", use_container_width=True):
        name_to_check = ""
        if new_user:
            name_to_check = new_user
        elif selected_user != "選択してください":
            name_to_check = selected_user
        
        if name_to_check:
            # 🚫 「こはく」が含まれているかチェック
            if "こはく" in name_to_check:
                st.session_state['banned'] = True
                st.rerun()
            else:
                st.session_state['user_name'] = name_to_check
                st.rerun()
        else:
            st.warning("名前を選択するか入力してください")

# --- メイン処理 ---
def main():
    # 🚫 BANチェック
    if st.session_state.get('banned'):
        st.error("### ⚠️ アクセス拒否")
        st.title("あなたは永久BANされました。")
        st.write("このアプリを利用することはできません。")
        st.stop()

    # データをロード
    df = load_data()

    # ログインチェック
    if 'user_name' not in st.session_state:
        login_screen(df)
        return

    current_user = st.session_state['user_name']
    if "こはく" in current_user:
        st.session_state['banned'] = True
        st.rerun()

    # --- 以下、アプリ画面 ---
    c1, c2 = st.columns([3, 1])
    with c1:
        st.write(f"お疲れ様です、**{current_user}** さん！ 👋")
    with c2:
        if st.button("ログアウト"):
            del st.session_state['user_name']
            st.rerun()

    st.divider()

    # --- 1. 入力フォーム ---
    with st.expander("✏️ 勉強記録をつける", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            subject = st.selectbox("科目", ["数学", "英語", "国語", "理科", "社会", "プログラミング", "その他"])
        with c2:
            study_time = st.number_input("時間 (分)", min_value=1, step=5, value=30)
        
        if st.button("投稿する 🔥", use_container_width=True, type="primary"):
            save_data(current_user, subject, study_time)
            st.success("記録しました！")
            time.sleep(1)
            st.rerun()

    # --- 2. ランキング ---
    st.subheader("👑 ランキング")
    
    if not df.empty:
        # 数値型への変換を念のため行う
        df['時間'] = pd.to_numeric(df['時間'], errors='coerce').fillna(0)
        
        tab1, tab2 = st.tabs(["📅 今日の1位", "🏆 総合ランキング"])
        today_str = datetime.now().strftime('%Y-%m-%d')

        with tab1:
            # 日付フィルタリング
            today_df = df[df['日付'] == today_str]
            if not today_df.empty:
                daily_ranking = today_df.groupby('ユーザー名')['時間'].sum().reset_index().sort_values('時間', ascending=False)
                top_user = daily_ranking.iloc[0]['ユーザー名']
                top_score = daily_ranking.iloc[0]['時間']
                
                if top_user == current_user:
                    st.balloons()
                    st.markdown(f"<div style='text-align: center; color: #FFD700;'><h1>Congratulations!!</h1><h2>👑 今日のキングはあなたです！ 👑</h2></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"### 👑 今日の暫定1位: **{top_user}** ({top_score}分)")
                st.table(daily_ranking.set_index('ユーザー名'))
            else:
                st.info("今日はまだ誰も記録していません。")

        with tab2:
            total_ranking = df.groupby('ユーザー名')['時間'].sum().reset_index().sort_values('時間', ascending=False)
            if not total_ranking.empty:
                top_user_all = total_ranking.iloc[0]['ユーザー名']
                if top_user_all == current_user:
                    st.snow()
                    st.markdown(f"<h3 style='color:orange; text-align:center;'>Excellent! You are the Legend! 🏆</h3>", unsafe_allow_html=True)
                st.bar_chart(total_ranking.set_index('ユーザー名'), color="#FF4B4B")
                st.table(total_ranking.set_index('ユーザー名'))

    # --- 3. タイムライン ---
    st.divider()
    st.caption("みんなの足跡")
    if not df.empty and '日時詳細' in df.columns:
        # 日時詳細でソート (文字列比較になるがISOフォーマットなら概ねOK)
        recent_logs = df.sort_values('日時詳細', ascending=False).head(10)
        for _, row in recent_logs.iterrows():
            # Supabaseのタイムスタンプは "2023-10-27T10:00:00+00:00" のような形式
            time_str = str(row['日時詳細'])
            # 表示用に簡易整形 (Tをスペースに置換など)
            display_time = time_str.replace("T", " ").split(".")[0] 
            st.text(f"{row['ユーザー名']}: {row['科目']} ({row['時間']}分) - {display_time}")

if __name__ == "__main__":
    main()
