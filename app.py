import streamlit as st
import os
import pandas as pd
from openai import OpenAI

# Streamlit Cloudの環境変数からAPIキーを取得
api_key = st.secrets["OPENAI_API_KEY"]

# OpenAIのクライアントを初期化
client = OpenAI(api_key=api_key)

# APIキーが設定されていない場合のエラーハンドリング
if not api_key:
    st.error("OpenAI APIキーが設定されていません。Streamlit Cloudの設定でOPENAI_API_KEYを設定してください。")
    st.stop()

# CSVデータの読み込み
@st.cache_data
def load_data():
    file_path = 'shokusyu_videos.csv'  # アップロードされたファイルへのパスを使用
    return pd.read_csv(file_path, encoding='shift_jis', header=None)

df = load_data()

# 職種と報酬目安のマッピング
job_fee_mapping = {
    "フロントエンド": "70万円～90万円",
    "バックエンド": "70万円～90万円",
    "スマホ(ネイティブ)アプリエンジニア": "70万円～90万円",
    "スクラムマスター": "120万円～150万円",
    "クラウドエンジニア": "80万円～120万円",
    "SRE": "90万円～140万円",
    "データサイエンティスト": "100万円～140万円",
    "データアナリスト": "80万円～120万円",
    "DWHエンジニア(データエンジニア)": "80万円～120万円",
    "IOTエンジニア": "90万円～150万円"
}

st.title('IT職種解説アプリ')

# 職種のプルダウンメニューを作成
job_types = df.iloc[:,0].tolist()
selected_job = st.selectbox("職種を選択してください", job_types)

# 新たに業種のプルダウンメニューを作成
industry_types = ["スタートアップ", "事業会社(非IT企業)"]
selected_industry = st.selectbox("業種を選択してください", industry_types)

# 「事業会社(非IT企業)」が選択された場合のみ表示される「部署」プルダウンメニュー
department = None
if selected_industry == "事業会社(非IT企業)":
    departments = ["情報システム部", "DX部", "新規事業"]
    selected_department = st.selectbox("部署を選択してください", departments)
else:
    selected_department = ""

# chatGPTにリクエストするためのメソッドを設定
def run_gpt(ankenkpronputo, selected_job, selected_industry, selected_department):
    full_prompt = (ankenkpronputo
                   .replace("{selected_job}", selected_job)
                   .replace("{selected_industry}", selected_industry)
                   .replace("{selected_department}", selected_department))
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": full_prompt},
            ],
        )
        output_content = response.choices[0].message.content.strip()
        return output_content
    except Exception as e:
        st.error(f"OpenAI APIエラー: {str(e)}")
        return None

# 案件プロンプトの定義
ankenkpronputo = """
#依頼
{selected_job}を業務委託で募集します。
{selected_industry}と{selected_department}に合わせて案件表を作成してください。

#企業
{selected_industry}

#部署
{selected_department}

#制約条件
・600文字以上
・必ず{#出力形式}に沿って生成すること。
・必ず{#出力形式}の項目(■)を守ること。
・「当社」ではなく、「同社」と記載する

#出力形式
■職種の解説：
※初学者向けに解説。150文字以上で記載
■依頼業務：
※150文字以上で記載
■解決したい課題：
※選択された{selected_industry}と{selected_department}に合わせて、具体例を用いながら、現状の事業課題と解決したいことを文章で記載。100文字以上で記載。
■依頼業務詳細：
※箇条書きで5つ以上記載
■募集背景：
※120文字以上で記載
■組織構成:
※50文字以上で記載
■開発環境：
■必要な経験やスキル：
※箇条書きで3つ以上記載
"""

# 案件イメージ作成のボタンが押されたかどうかを管理
is_button_clicked = st.button('案件イメージ作成')

# ボタンが押された後もプルダウン項目を表示させる
if is_button_clicked:
    if (ankenkpronputo != ""):
        st.write("案件生成中・・")
        output_content_text = run_gpt(ankenkpronputo, selected_job, selected_industry, selected_department)
        if output_content_text:
            st.write(output_content_text)
            st.download_button(label='案件内容 Download', 
                               data=output_content_text, 
                               file_name='out_put.txt',
                               mime='text/plain',
                              )

            # 案件イメージ生成後に他の要素を表示
            if selected_job:
                fee_estimate = job_fee_mapping.get(selected_job, "報酬目安が設定されていません")
                st.markdown(f"<h2 style='font-size: 150%;'>{selected_job}の報酬目安: {fee_estimate}</h2>", unsafe_allow_html=True)

            if selected_job:
                job_info = df[df.iloc[:, 0] == selected_job].iloc[0]
                videos = job_info[1].split("\n")
                st.write(f"### {selected_job}の解説動画")
                for video in videos:
                    st.video(video)