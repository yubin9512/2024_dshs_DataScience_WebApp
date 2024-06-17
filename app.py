import numpy as np
import pyrebase
import re

import uuid

import firebase_admin
import streamlit as st
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from firebase_admin import db

import pandas as pd
import random
import seaborn as sns
import matplotlib.pyplot as plt
import datetime
import matplotlib.font_manager as fm
from streamlit_option_menu import option_menu
import plotly.graph_objects as go
from math import floor

@st.cache_data
def get_data():
    data = pd.read_csv('word_list_with_examples.csv',  delimiter=';', encoding='utf-8')
    word_data = pd.DataFrame(data)

    data = pd.read_csv('2023_kice_eng_text_sample.csv')
    kice_data = pd.DataFrame(data)

    filename = '2023_suneung_eng_18-45_text_.txt'
    f = open(filename, encoding='utf-8')
    text = f.read()
    suneung_text = text.lower().split()

    return word_data, kice_data, suneung_text

word_data, kice_data, suneung_text = get_data()

font_path = 'fonts/NanumGothic.ttf'
font_prop = fm.FontProperties(fname=font_path)
plt.rc('font', family=font_prop.get_name())
sns.set(font=font_prop.get_name(), rc={"axes.unicode_minus": False}, style='white')

try:
    app = firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate("serviceAccount.json")
    app = firebase_admin.initialize_app(cred, {
        'databaseURL': "https://tdiyd-voca1600-default-rtdb.firebaseio.com/"
    })


firebaseConfig = {
    'apiKey': "AIzaSyCW4Hd3Lwt6Xy57FDta3avmB10OjE1c0OA",
    'authDomain': "tdiyd-voca1600.firebaseapp.com",
    'databaseURL': "https://tdiyd-voca1600-default-rtdb.firebaseio.com",
    'projectId': "tdiyd-voca1600",
    'storageBucket': "tdiyd-voca1600.appspot.com",
    'messagingSenderId': "495912630083",
    'appId': "1:495912630083:web:5e24cc4f623faa080fe1f6"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

class DB:
    def __init__(self, user_id):
        self.user_id = user_id
        self.user_info_ref = db.reference(f'/user_infos/{self.user_id}')
        self.results_ref = db.reference(f'/results/{self.user_id}')

    def get_user_info(self):
        return self.user_info_ref.get()

    def save_user_info(self, user_data):
        self.user_info_ref.set(user_data)

    def update_user_info(self, updates):
        self.user_info_ref.update(updates)

    def delete_user_info(self):
        self.user_info_ref.delete()

    def get_results(self):
        return self.results_ref.get()

    def save_result(self, result_data):
        self.results_ref.push(result_data)

    def delete_result(self):
        self.results_ref.delete()

class Auth:

    @staticmethod
    def create_user(email, password):
        try:
            firebase_auth.create_user(
                email=email,
                password=password
            )
            return None
        except Exception as e:
            return e

    @staticmethod
    def reset_password(email):
        try:
            auth.send_password_reset_email(email)
            return not None
        except:
            return None

    @staticmethod
    def login_user(email, password):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            return user['idToken'], user['localId']
        except Exception as e:
            print(f"Login failed: {e}")
            return None, None

    @staticmethod
    def store_session(token, session_id):
        st.session_state[f'token_{session_id}'] = token

    @staticmethod
    def revoke_token(sessionId):
        if f'token_{sessionId}' in st.session_state:
            del st.session_state[f'token_{sessionId}']
        st.session_state['isLogin'] = False

    @staticmethod
    def delete_firebase_user(email):
        try:
            user = firebase_auth.get_user_by_email(email)
            firebase_auth.delete_user(user.uid)
            return True, "회원 탈퇴가 완료되었습니다."
        except Exception as e:
            return False, f"회원 탈퇴 중 문제가 발생했습니다: {e}"

def draw_figure1():
    pos_map = {
        '명': '명사',
        '동': '동사',
        '형': '형용사',
        '부': '부사',
        '전': '전치사',
        '접': '접사'
    }
    pos_counts = word_data['품사1'].map(pos_map).value_counts()
    plt.figure(figsize=(4, 4))
    st.write('**품사별 단어 수**')
    sns.barplot(x=pos_counts.index, y=pos_counts.values, palette=sns.color_palette("plasma")[::-1])
    plt.xlabel('품사', fontproperties=font_prop)
    plt.ylabel('단어 수', fontproperties=font_prop)
    plt.xticks(rotation=45, fontproperties=font_prop)
    st.pyplot(plt)

def draw_figure2():
    theme_counts = word_data['테마'].value_counts()
    plt.figure(figsize=(4, 4))
    st.write('**테마별 단어 분포**')
    sns.barplot(x=theme_counts.index, y=theme_counts.values/16, palette=sns.color_palette("plasma")[::-1])
    plt.xlabel('테마 종류', fontproperties=font_prop)
    plt.ylabel('단어 분포[%]', fontproperties=font_prop)
    plt.xticks([], [], fontproperties=font_prop)
    st.pyplot(plt)

def draw_figure3():
    theme_counts2 = word_data['테마'].value_counts()
    most_frequent_theme = theme_counts2.idxmax()
    theme_counts = theme_counts2.drop(most_frequent_theme)
    plt.figure(figsize=(4, 4))
    st.write('**기타 테마별 단어 수**')
    sns.barplot(x=theme_counts.index, y=theme_counts.values, palette=sns.color_palette("plasma")[::-1][1:])
    plt.xlabel('테마 종류(기타)', fontproperties=font_prop)
    plt.ylabel('단어 수', fontproperties=font_prop)
    plt.xticks(rotation=90, fontproperties=font_prop)
    st.pyplot(plt)

def draw_figure4():
    word_themes = word_data[word_data['영어단어'].isin(suneung_text)]['테마'].value_counts()
    plt.figure(figsize=(4, 4))
    st.write('**2024학년도 수능 시험지 내 테마 분포**')
    sns.barplot(x=word_themes.index, y=word_themes.values, palette=sns.color_palette("plasma")[::-1])
    plt.xlabel('테마 종류', fontproperties=font_prop)
    plt.ylabel('단어 수', fontproperties=font_prop)
    plt.xticks(rotation=90, fontproperties=font_prop)
    st.pyplot(plt)

def draw_figure5():
    word_themes = word_data[word_data['영어단어'].isin(suneung_text)]['테마'].value_counts()
    most_frequent_theme = word_themes.idxmax()
    theme_counts = word_themes.drop(most_frequent_theme)
    st.markdown(f"""
        <div style="font-weight: bold; font-size: 15px; line-height: 0.7;">
            2024학년도 수능 시험지 내 테마 분포
        </div>
        """, unsafe_allow_html=True)
    st.write('**(일상과 여가 생활 테마 제외)**')
    plt.figure(figsize=(4, 4))
    plt.pie(theme_counts, labels=theme_counts.index, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 10, 'fontproperties': font_prop})
    plt.axis('equal')
    st.pyplot(plt)
    st.write('')

def sanitize_filename(filename):
    """파일 이름을 안전하게 변환하여 JSON 키로 사용할 수 있도록 합니다."""
    return re.sub(r'\W+', '_', filename)  # 비문자/숫자를 언더스코어로 치환

def func_textAnalysis():
    text = st.text_input("아래 내용을 삭제하고 입력하세요", 'There is something deeply paradoxical about the professional status of sports journalism, especially in the medium of print.  In discharging their usual responsibilities of description and commentary, reporters’ accounts of sports events are eagerly consulted by sports fans, while in their broader journalistic role of covering sport in its many forms, sports journalists are among the most visible of all contemporary writers.  The ruminations of the elite class of ‘celebrity’ sports journalists are much sought after by the major newspapers, their lucrative contracts being the envy of colleagues in other ‘disciplines’ of journalism.  Yet sports journalists do not have a standing in their profession that corresponds to the size of their readerships or of their pay packets, with the old saying (now reaching the status of cliché) that sport is the ‘toy department of the news media’ still readily to hand as a dismissal of the worth of what sports journalists do.  This reluctance to take sports journalism seriously produces the paradoxical outcome that sports newspaper writers are much read but little admired.', placeholder='분석할 텍스트를 입력하세요.')
    with st.container():
        st.write('-'*70)
        st.write('**지문**')
        st.write(text)
        st.write('-'*70)

    words = text.lower().split()
    word_themes = word_data[word_data['영어단어'].isin(words)]['테마'].value_counts()
    dominant_theme = word_themes.idxmax() if not word_themes.empty else "No dominant theme"
    st.write(f'Dominant theme in the text:{dominant_theme}')

    col1, col2, col3 = st.columns([2,6,2])
    with col2:
        plt.figure(figsize=(4,4))
        plt.pie(word_themes, labels=word_themes.index, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 10, 'fontproperties': font_prop})
        plt.axis('equal')
        st.pyplot(plt)

    for theme in word_themes.index:
        theme_words = word_data[word_data['테마'] == theme]
        theme_words = theme_words[theme_words['영어단어'].isin(words)]
        st.write("-" * 30)
        st.write(f"**Theme: {theme}**")
        for _, row in theme_words.iterrows():
            meanings = ', '.join(
                [str(meaning) for meaning in [row['의미1'], row.get('의미2'), row.get('의미3')] if pd.notna(meaning)])
            st.write(f"**{row['영어단어']}**: {meanings}")

def func_showWords(wordId):
    if wordId in word_data['번호'].values:
        word_row = word_data.loc[word_data['번호'] == wordId].iloc[0]
        word = word_row['영어단어']
        theme = word_row['테마']
        pos1 = word_row['품사1']
        pos2 = word_row['품사2']
        pos3 = word_row['품사3']
        meaning1 = word_row['의미1']
        meaning2 = word_row['의미2']
        meaning3 = word_row['의미3']
        example1 = word_row['예시문1']
        example2 = word_row['예시문2']
        example3 = word_row['예시문3']

        st.title(word)
        st.write(f'**테마: {theme}**')
        st.write('_' * 50)
        col1, col2, col3 = st.columns([2, 1, 7])
        with col1:
            st.write(f'**{meaning1}**')
        with col2:
            st.write(f'{pos1}')
        with col3:
            st.write(example1)
        st.write('_' * 50)

        if not pd.isna(pos2):
            col1, col2, col3 = st.columns([2, 1, 7])
            with col1:
                st.write(f'**{meaning2}**')
            with col2:
                st.write(f'{pos2}')
            with col3:
                st.write(example2)
            st.write('_' * 50)

        if not pd.isna(pos3):
            col1, col2, col3 = st.columns([2, 1, 7])
            with col1:
                st.write(f'**{meaning3}**')
            with col2:
                st.write(f'{pos3}')
            with col3:
                st.write(example3)
            st.write('_' * 50)

        st.write('_' * 50)
        st.write(f'**평가원 예시문**')
        for i in range(395):
            sen = kice_data.loc[kice_data['key'] == i + 1].iloc[0]['문장']
            sen = sen.lower().replace(',', '').split()
            if word in sen:
                year = int(kice_data.loc[kice_data['key'] == i + 1].iloc[0]['응시년도'])
                month = int(kice_data.loc[kice_data['key'] == i + 1].iloc[0]['모의고사'])
                num = kice_data.loc[kice_data['key'] == i + 1].iloc[0]['문항번호']
                sen = kice_data.loc[kice_data['key'] == i + 1].iloc[0]['문장']
                st.write(f'**{year}.{month}.{num}번 문항** {sen}')
        st.write('_' * 50)

    else:
        st.write("ID not found.")

def func_createQuestions(num_questions):
    questions = []
    data = word_data.dropna(subset=['의미1'])
    meanings = list(data['의미1'])

    used_words = set()

    while len(questions) < num_questions:
        correct_row = data.sample(1)
        correct_word = correct_row['영어단어'].values[0]

        if correct_word in used_words:
            continue

        correct_meaning = correct_row['의미1'].values[0].split(",")[0].strip()

        used_words.add(correct_word)

        wrong_meanings = random.sample([m for m in meanings if m != correct_meaning], 3)
        choices = random.sample([correct_meaning] + wrong_meanings, k=4)

        questions.append({'word': correct_word, 'choices': choices, 'correct_answer': correct_meaning})

    random.shuffle(questions)

    return questions

def func_createReviewQuestions(incorrect_stats_df):
    num_questions = min(len(incorrect_stats_df), 50)
    st.session_state.testPageRequest = num_questions

    question_words = incorrect_stats_df['question'].sample(n=num_questions, replace=False).tolist()
    questions = []

    for word in question_words:
        correct_meaning = word_data[word_data['영어단어'] == word]['의미1'].values[0].strip()
        previous_incorrects = incorrect_stats_df[incorrect_stats_df['question'] == word]['responses'].values[0]

        # 과거 오답 중 최대 3개 선택
        if len(previous_incorrects) > 3:
            wrong_choices = random.sample(previous_incorrects, k=3)
        else:
            wrong_choices = previous_incorrects[:]

        # 부족한 선택지 수 계산
        needed_choices = 3 - len(wrong_choices)

        # 필요한 경우, word_data에서 추가 오답 선택
        if needed_choices > 0:
            additional_meanings = list(word_data[word_data['영어단어'] != word]['의미1'].dropna().unique())
            additional_wrong_choices = random.sample([m for m in additional_meanings if m not in previous_incorrects], k=needed_choices)
            wrong_choices.extend(additional_wrong_choices)

        # 모든 선택지를 섞음
        choices = random.sample([correct_meaning] + wrong_choices, k=4)

        # 문항 추가
        questions.append({
            'word': word,
            'choices': choices,
            'correct_answer': correct_meaning
        })

    # 문항 순서를 랜덤하게 섞음
    random.shuffle(questions)

    return questions

def func_withoutLoginNotice():
    if st.session_state.isLogin == False:
        with st.form(key='without_login_form'):
            st.markdown(f"""
                <div style="font-weight: bold; font-size: 18px; line-height: 0.8;">
                    비회원 사용 시 일부 기능이 제한될 수 있습니다.
                </div>
                """, unsafe_allow_html=True)
            col1, col2 = st.columns([8.5, 1])
            with col2:
                if st.form_submit_button('Login'):
                    st.session_state.username = 'DSHS'
                    st.session_state.dailyamount = 40
                    st.session_state.sessionnumber = 40
                    st.session_state.level = None
                    st.session_state.bookmarks = set()
                    st.session_state.learnPageRequest = 0
                    st.session_state.dayPageRequest = 0
                    st.session_state.testPageRequest = 50
                    st.session_state.questionPageRequest = 0
                    st.session_state.testPageResponses = 0
                    st.session_state.testQuestions = []
                    st.session_state.resultPageRequest = []
                    st.session_state.completed_days = []
                    st.session_state.page = 'Login'
                    st.experimental_rerun()

def func_getUserInfo(user_id):
    db_instance = DB(user_id)
    user_info = db_instance.get_user_info()
    if user_info:
        st.session_state.username = user_info.get('username')
        st.session_state.level = user_info.get('level')
        st.session_state.dailyamount = user_info.get('dailyamount')
        st.session_state.sessionnumber = user_info.get('sessionnumber')
        st.session_state.bookmarks = set(user_info.get('bookmarks', []))
        st.session_state.completed_days = user_info.get('completed_days')
        processed_files = user_info.get('processed_files', {})
        st.session_state.processed_files = processed_files if isinstance(processed_files, dict) else {}
        processed_test_results = user_info.get('processed_test_results', {})
        st.session_state.processed_test_results = processed_test_results if isinstance(processed_test_results, dict) else {}
        st.session_state.analysis_data = user_info.get('analysis_data', [])
    else:
        st.session_state.page = 'InputUsername'
        st.experimental_rerun()

def func_saveUserInfo(user_id, info_type, data):
    db_instance = DB(user_id)
    if isinstance(data, set):
        data = list(data)
    db_instance.update_user_info({info_type: data})
    st.session_state[info_type] = data

def func_saveAnalysisData(user_id, new_data):
    db_instance = DB(user_id)
    # Get current analysis data
    current_data = db_instance.user_info_ref.child('analysis_data').get() or []
    # Append new data
    current_data.append(new_data)
    # Save updated analysis data
    db_instance.user_info_ref.child('analysis_data').set(current_data)
    st.session_state['analysis_data'] = current_data

def func_sidebar(p):
    with st.sidebar:
        if st.session_state.isLogin:
            options = ['Home', 'My Page', '단어 학습', '테스트 응시', '성적 분석', '지문 분석(beta)', '단어장 설명']
            icons = ['house', 'archive', 'journal-text', 'file-earmark-text','clipboard-data', 'text-left', 'info-circle']
        else:
            options = ['Home', '단어 학습', '테스트 응시(beta)', '단어장 설명']
            icons = ['house', 'journal-text', 'file-earmark-text', 'info-circle']

        choice = option_menu("TDIYD VOCA1600", options=options, icons=icons,
                             menu_icon="app-indicator", default_index=p,
                             styles={
                                 "container": {"padding": "4!important", "background-color": "#fafafa"},
                                 "icon": {"color": "black", "font-size": "25px"},
                                 "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px",
                                              "--hover-color": "#fafafa"},
                                 "nav-link-selected": {"background-color": "#FFA500"},
                             }
                             )
        if choice == "Home" and st.session_state.page != 'Home':
            st.session_state.page = 'Home'
            st.experimental_rerun()
        elif choice == 'My Page' and st.session_state.page != 'MyPage' and st.session_state.page != 'DisplayResultFromFiles' :
            st.session_state.page = 'MyPage'
            st.experimental_rerun()
        elif choice == "단어 학습" and st.session_state.page != 'Learn' and st.session_state.page != 'Day' and st.session_state.page != 'Bookmark':
            st.session_state.page = 'Learn'
            st.experimental_rerun()
        elif choice == "테스트 응시" and st.session_state.page != 'Test' and st.session_state.page != 'Question' and st.session_state.page != 'Result':
            st.session_state.page = 'Test'
            st.experimental_rerun()
        elif choice == "테스트 응시(beta)" and st.session_state.page != 'TestWithoutLogin' and st.session_state.page != 'Question':
            st.session_state.page = 'TestWithoutLogin'
            st.experimental_rerun()
        elif choice == '성적 분석' and st.session_state.page != 'Analysis' and st.session_state.page != 'ReviewTest':
            st.session_state.page = 'Analysis'
            st.experimental_rerun()
        elif choice == '지문 분석(beta)' and st.session_state.page != 'TextAnalysis':
            st.session_state.page = 'TextAnalysis'
            st.experimental_rerun()
        elif choice == "단어장 설명" and st.session_state.page != 'Info':
            st.session_state.page = 'Info'
            st.experimental_rerun()

def page_login():
    st.title('The Day Is Your Day VOCA1600')
    st.write('')
    st.subheader('로그인')
    with st.form(key='login_form'):

        user_email = st.text_input('이메일')
        user_pw = st.text_input('비밀번호', type='password')

        btn_login = st.form_submit_button('로그인')

        if btn_login:
            idToken, user_id = Auth.login_user(user_email, user_pw)
            if idToken is not None and user_id is not None:
                Auth.store_session(idToken, st.session_state.sessionId)
                if 'email' not in st.session_state:
                    st.session_state.email = user_email
                st.session_state.isLogin = True
                st.session_state.userId = user_id
                func_getUserInfo(user_id)
                st.session_state.page = 'Home'
                st.experimental_rerun()
            else:
                st.error('아이디, 비밀번호를 확인한 후 다시 로그인하세요.')

    col1, col2, col3, col4, col5 = st.columns([1,1.1,1.1,1.1,1.2])
    with col1:
        if st.button('비회원 사용'):
            st.session_state.page = 'InputUsername'
            st.experimental_rerun()
    with col3:
        if st.button('사용자 등록'):
            st.session_state.page = 'Register'
            st.experimental_rerun()
    with col5:
        if st.button('비밀번호 초기화'):
            st.session_state.page = 'ResetPassword'
            st.experimental_rerun()

def page_register():
    if st.button('Login'):
        st.session_state.page = 'Login'
        st.experimental_rerun()

    st.title('The Day Is Your Day VOCA1600')
    st.subheader('사용자 등록')
    with st.form(key='user_ref_form'):

        user_email = st.text_input('이메일')
        user_pw = st.text_input('비밀번호', type='password')

        btn_user_reg = st.form_submit_button('사용자 등록')

        if btn_user_reg:
            res = None
            res = Auth.create_user(user_email, user_pw)
            if res is None:
                idToken, user_id = Auth.login_user(user_email, user_pw)
                if idToken is not None:
                    Auth.store_session(idToken, st.session_state.sessionId)
                    st.session_state.email = user_email
                    st.session_state.userId = user_id
                    st.session_state.isLogin = True
                st.session_state.page = 'InputUsername'
                st.experimental_rerun()
            else:
                st.error(res)

def page_resetPassword():
    if st.button('Login'):
        st.session_state.page = 'Login'
        st.experimental_rerun()

    st.title('The Day Is Your Day VOCA1600')
    st.subheader('비밀번호 초기화')
    with st.form(key='pw_reset_form'):
        user_email = st.text_input('이메일')
        btn_reset = st.form_submit_button('비밀번호 초기화 메일 발송')
        if btn_reset:
            if Auth.reset_password(user_email):
                st.info('이메일을 확인하세요.')
            else:
                st.error('이메일이 정확한지 확인하세요!')

def page_home():
    func_withoutLoginNotice()
    func_sidebar(0)
    if st.session_state.isLogin == True:
        func_getUserInfo(st.session_state.userId)
        today = datetime.datetime.now().strftime('%Y-%m-%d (%A)')
        st.write(f"Today: {today}")
    st.subheader(f"Hi, {st.session_state.username}!")
    if st.session_state.isLogin:
        st.header('단어 학습 시작하기')
    st.markdown(f"""
            <div style="color: gray; font-weight: bold; font-size: 25px;">
                최근 학습 진도
            </div>
            """, unsafe_allow_html=True)
    if True in st.session_state.completed_days:
        completed_count = len(st.session_state.completed_days) - st.session_state.completed_days[::-1].index(True)
    else:
        completed_count = 0
    if st.button(f"Day {completed_count + 1}"):
        st.session_state.learnPageRequest = completed_count + 1
        st.session_state.dayPageRequest = (st.session_state.learnPageRequest - 1) * st.session_state.dailyamount + 1
        st.session_state.page = 'Day'
        st.experimental_rerun()
    st.write('')
    col1, col2 = st.columns(2)
    with col1:
        with st.container():
            text = f'{sum(st.session_state.completed_days) * st.session_state.dailyamount} / 1600 단어'
            st.markdown(f"""
                    <div style="color: gray; font-weight: bold; font-size: 25px; line-height: 0.7;">
                        학습 진행도
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown(f"""
                    <div style="color: gray; font-size: 18px;">
                        ({text})
                    </div>
                    """, unsafe_allow_html=True)

            progress = sum(st.session_state.completed_days) / st.session_state.sessionnumber * 100
            sizes = [progress, 100 - progress]
            colors = ['orange', 'gray']
            fig1, ax1 = plt.subplots()
            ax1.pie(sizes, colors=colors, startangle=90, counterclock=False)
            centre_circle = plt.Circle((0, 0), 0.80, fc='white')
            fig = plt.gcf()
            fig.gca().add_artist(centre_circle)
            ax1.text(0, 0, f'{progress:.1f}%', ha='center', va='center', fontsize=20, color='black')
            ax1.axis('equal')

            st.pyplot(fig1)

    with col2:
        with st.container():
            st.markdown(f"""
                    <div style="color: gray; font-weight: bold; font-size: 25px; line-height: 1.2;">
                        나만의 북마크
                    </div>
                    """, unsafe_allow_html=True)
            if len(st.session_state.bookmarks) <= 20:
                max_range = 20
                steps = [
                        {'range': [0, 5], 'color': "#fff2e6"},
                        {'range': [5, 10], 'color': "#ffebcc"},
                        {'range': [10, 15], 'color': "#ffe0b3"},
                        {'range': [15, 20], 'color': "#ffd699"}
                    ]
                tickvals = [0, 5, 10, 15, 20]
                ticktexts = ["0", "5", "10", "15", "20"]
            elif len(st.session_state.bookmarks) <= 100:
                max_range = 100
                steps = [
                    {'range': [0, 25], 'color': "#fff2e6"},
                    {'range': [25, 50], 'color': "#ffebcc"},
                    {'range': [50, 75], 'color': "#ffe0b3"},
                    {'range': [75, 100], 'color': "#ffd699"}
                ]
                tickvals = [0, 25, 50, 75, 100]
                ticktexts = ["0", "25", "50", "75", "100"]
            elif len(st.session_state.bookmarks) <= 200:
                max_range = 200
                steps = [
                    {'range': [0, 50], 'color': "#fff2e6"},
                    {'range': [50, 100], 'color': "#ffebcc"},
                    {'range': [100, 150], 'color': "#ffe0b3"},
                    {'range': [150, 200], 'color': "#ffd699"}
                ]
                tickvals = [0, 50, 100, 150, 200]
                ticktexts = ["0", "50", "100","150", "200"]
            elif len(st.session_state.bookmarks) <= 1000:
                max_range = 1000
                steps = [
                    {'range': [0, 250], 'color': "#fff2e6"},
                    {'range': [250, 500], 'color': "#ffebcc"},
                    {'range': [500, 750], 'color': "#ffe0b3"},
                    {'range': [750, 1000], 'color': "#ffd699"}
                ]
                tickvals = [0, 250, 500, 750, 1000]
                ticktexts = ["0", "250", "500", "750", "1000"]
            else:
                max_range = 1600
                steps = [
                    {'range': [0, 400], 'color': "#fff2e6"},
                    {'range': [400, 800], 'color': "#ffebcc"},
                    {'range': [800, 1200], 'color': "#ffe0b3"},
                    {'range': [1200, 1600], 'color': "#ffd699"}
                ]
                tickvals = [0, 400, 800, 1200, 1600]
                ticktexts = ["0", "400", "800", "1200", "1600"]

            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=len(st.session_state.bookmarks),
                number={'font': {'size': 35}},
                gauge={
                    'axis': {'range': [0, max_range], 'tickwidth': 1, 'tickcolor': "orange",
                             'tickvals': tickvals,
                             'ticktext': ticktexts},
                    'bar': {'color': "orange"},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "orange",
                    'steps': steps,
                    'threshold': {
                        'line': {'color': "orange", 'width': 2},
                        'thickness': 0.75,
                        'value': len(st.session_state.bookmarks)
                    }
                }
            ))
            fig.update_layout(
                autosize=False,
                width=300,  # 원하는 폭으로 설정
                height=200,  # 원하는 높이로 설정
                margin=dict(l=15, r=30, t=20, b=0)  # 여백 설정
            )
            col1, col2, col3 = st.columns([1,8,1])
            with col2:
                st.plotly_chart(fig)
            col1, col2 = st.columns([8, 2])
            with col1:
                with st.container():
                    st.markdown(f"""
                                <div style="color: gray; font-weight: bold; font-size: 22px; line-height: 0.7;">
                                    추가된 단어
                                </div>
                                """, unsafe_allow_html=True)
                    st.markdown(f"""
                                <div style="font-weight: bold; font-size: 20px;">
                                    {len(st.session_state.bookmarks)}단어
                                </div>
                                """, unsafe_allow_html=True)
            with col2:
                if st.button('→'):
                    st.session_state.page = 'Bookmark'
                    st.experimental_rerun()

    st.write('')

    if st.session_state.isLogin:
        btn_logout = st.button('로그아웃')
        if btn_logout:
            Auth.revoke_token(st.session_state.sessionId)
            st.session_state.clear()
            st.experimental_rerun()

def page_inputUsername():
    func_withoutLoginNotice()
    st.title("The Day Is Your Day VOCA 1600")
    st.write("**PC환경에서 가장 쾌적하게 사용할 수 있습니다.**")
    name = st.text_input("Enter your name (10자 이내):", max_chars=10, placeholder="user name")
    if st.button("Submit"):
        st.session_state.username = name
        if st.session_state.isLogin == True:
            func_saveUserInfo(user_id=st.session_state.userId, info_type='username', data=name)
        st.session_state.page = 'SelectLevel'
        st.experimental_rerun()

def page_selectLevel():
    func_withoutLoginNotice()

    st.title("The Day Is Your Day VOCA 1600")
    st.write("**PC환경에서 가장 쾌적하게 사용할 수 있습니다.**")
    st.write("Choose your level:")
    level_options = ["Beginner", "Intermediate", "Advanced"]
    level = st.radio("", level_options)
    st.write('고3 영어 기준, 1등급 (Advanced), 1~2등급 (Intermediate), 3등급 이하 (Beginner)이 적정합니다')
    if st.button("Submit"):
        st.session_state.level = level
        if st.session_state.isLogin == True:
            func_saveUserInfo(user_id=st.session_state.userId, info_type='level', data=level)
        st.session_state.page = 'SelectDailyAmount'
        st.experimental_rerun()

def page_selectDailyAmount():
    func_withoutLoginNotice()

    st.title("The Day Is Your Day VOCA 1600")
    st.write("**PC환경에서 가장 쾌적하게 사용할 수 있습니다.**")
    st.write("Choose your daily amount:")
    amount_options = ["25개 (64일 완성)", "40개 (40일 완성)", "50개 (32일 완성)"]
    option = st.radio("", amount_options, key="daily_words")
    if st.button("Submit"):
        if option == "25개 (64일 완성)":
            st.session_state.dailyamount = 25
            st.session_state.sessionnumber = 64
        elif option == "40개 (40일 완성)":
            st.session_state.dailyamount = 40
            st.session_state.sessionnumber = 40
        else:
            st.session_state.dailyamount = 50
            st.session_state.sessionnumber = 32
        st.session_state.completed_days = [False] * st.session_state.sessionnumber
        if st.session_state.isLogin == True:
            func_saveUserInfo(user_id=st.session_state.userId, info_type='dailyamount', data=st.session_state.dailyamount)
            func_saveUserInfo(user_id=st.session_state.userId, info_type='sessionnumber', data=st.session_state.sessionnumber)
            func_saveUserInfo(user_id=st.session_state.userId, info_type='completed_days', data=st.session_state.completed_days)
            func_saveUserInfo(user_id=st.session_state.userId, info_type='bookmarks', data=st.session_state.bookmarks)
        st.session_state.page = 'Home'
        st.experimental_rerun()

def page_bookmark():
    func_withoutLoginNotice()

    if st.session_state.isLogin == True:
        func_getUserInfo(st.session_state.userId)
        func_sidebar(2)
    else:
        func_sidebar(1)

    st.title("북마크")
    st.write("**북마크한 단어를 확인해 보세요.**")
    for wordId in st.session_state.bookmarks:
        word_row = word_data.loc[word_data['번호'] == wordId].iloc[0]
        word = word_row['영어단어']
        theme = word_row['테마']
        pos1 = word_row['품사1']
        pos2 = word_row['품사2']
        pos3 = word_row['품사3']
        meaning1 = word_row['의미1']
        meaning2 = word_row['의미2']
        meaning3 = word_row['의미3']
        example1 = word_row['예시문1']
        example2 = word_row['예시문2']
        example3 = word_row['예시문3']

        with st.form(str(wordId)):
            st.title(word)
            st.write(f'**테마: {theme}**')
            st.write('_' * 50)
            col1, col2, col3 = st.columns([2, 1, 7])
            with col1:
                st.write(f'**{meaning1}**')
            with col2:
                st.write(f'{pos1}')
            with col3:
                st.write(example1)
            st.write('_' * 50)

            if not pd.isna(pos2):
                col1, col2, col3 = st.columns([2, 1, 7])
                with col1:
                    st.write(f'**{meaning2}**')
                with col2:
                    st.write(f'{pos2}')
                with col3:
                    st.write(example2)
                st.write('_' * 50)

            if not pd.isna(pos3):
                col1, col2, col3 = st.columns([2, 1, 7])
                with col1:
                    st.write(f'**{meaning3}**')
                with col2:
                    st.write(f'{pos3}')
                with col3:
                    st.write(example3)
                st.write('_' * 50)

            if st.form_submit_button('북마크 제거'):
                st.session_state.bookmarks.remove(wordId)
                func_saveUserInfo(user_id=st.session_state.userId, info_type='bookmarks', data=st.session_state.bookmarks)
                st.experimental_rerun()

def page_learn():
    func_withoutLoginNotice()

    if st.session_state.isLogin == True:
        func_getUserInfo(st.session_state.userId)
        func_sidebar(2)
    else:
        func_sidebar(1)

    st.title("단어 학습")
    st.write(f"**하루에 {st.session_state.dailyamount}단어씩 학습합니다.**")
    col1, col2, col3 = st.columns([1, 7, 2])
    with col1:
        st.write('<div style="text-align: center; font-weight: bold;">Day</div>', unsafe_allow_html=True)
    with col2:
        st.write('**Theme**')
    with col3:
        st.write('**완료 여부**')
    for i in range(int(st.session_state.sessionnumber)):
        with st.container():
            col1, col2, col3 = st.columns([1, 7, 2])
            with col1:
                if st.button(f'**Day {i+1}**'):
                    st.session_state.learnPageRequest = i + 1
                    st.session_state.dayPageRequest = (st.session_state.learnPageRequest - 1) * st.session_state.dailyamount + 1
                    st.session_state.page = 'Day'
                    st.experimental_rerun()
            with col2:
                themes = ', '.join(word_data.loc[(word_data['번호'] > i * st.session_state.dailyamount) &
                                                 (word_data['번호'] <= (i + 1) * st.session_state.dailyamount), '테마'].unique())
                st.write(themes)
            with col3:
                if st.session_state.completed_days[i]:
                    st.write('완료')
                else:
                    st.write('미완료')

def page_day():

    if st.session_state.isLogin == True:
        func_getUserInfo(st.session_state.userId)

    if st.session_state.isLogin == True:
        func_getUserInfo(st.session_state.userId)
        func_sidebar(2)
    else:
        func_sidebar(1)

    st.title(f'**단어 학습 Day {st.session_state.learnPageRequest}**')
    current_word_index = st.session_state.dayPageRequest - (st.session_state.learnPageRequest - 1) * st.session_state.dailyamount
    progress = current_word_index / st.session_state.dailyamount
    progress_bar_html = f"""
        <div style="width: 100%; background-color: lightgray; border-radius: 5px;">
            <div style="width: {progress * 100}%; background-color: orange; height: 15px; border-radius: 5px;"></div>
        </div>
        """
    st.markdown(progress_bar_html, unsafe_allow_html=True)
    st.write('')
    col1, col2, col3 = st.columns([4.3, 5.3, 1.1])
    with col1:
        if current_word_index > 1:
            if st.button('이전'):
                st.session_state.dayPageRequest -= 1
                if st.session_state.dayPageRequest < (st.session_state.learnPageRequest - 1) * st.session_state.dailyamount + 1:
                    st.session_state.learnPageRequest -= 1
                    st.session_state.dayPageRequest = (st.session_state.learnPageRequest - 1) * st.session_state.dailyamount + st.session_state.dailyamount
                st.experimental_rerun()
    with col2:
        if st.button('북마크 추가'):
            st.session_state.bookmarks.add(st.session_state.dayPageRequest)
            if st.session_state.isLogin == True:
                func_saveUserInfo(user_id=st.session_state.userId, info_type='bookmarks', data=st.session_state.bookmarks)
            st.experimental_rerun()
    with col3:
        if progress == 1:
            st.session_state.completed_days[st.session_state.learnPageRequest - 1] = True
            if st.session_state.isLogin == True:
                func_saveUserInfo(user_id=st.session_state.userId, info_type='completed_days',data=st.session_state.completed_days)
        else:
            if st.button('다음'):
                st.session_state.dayPageRequest += 1
                st.experimental_rerun()

    func_showWords(st.session_state.dayPageRequest)

    st.page_link('http://www.eng-exams.net/quizbank/qbank.php', label='수능 영어 기출 문제 바로가기')

def page_test():
    st.title("테스트 응시")
    st.write("**테스트를 통해 모르는 단어를 점검해 보세요**")
    if st.button('20단어 테스트'):
        st.session_state.testPageRequest = 20
        st.session_state.questionPageRequest = 0
        st.session_state.testQuestions = func_createQuestions(st.session_state.testPageRequest)
        st.session_state.testPageResponses = []
        st.session_state.test_id = str(uuid.uuid4())
        st.session_state.page = 'Question'
        st.experimental_rerun()
    if st.button('30단어 테스트'):
        st.session_state.testPageRequest = 30
        st.session_state.questionPageRequest = 0
        st.session_state.testQuestions = func_createQuestions(st.session_state.testPageRequest)
        st.session_state.testPageResponses = []
        st.session_state.test_id = str(uuid.uuid4())
        st.session_state.page = 'Question'
        st.experimental_rerun()
    if st.button('50단어 테스트'):
        st.session_state.testPageRequest = 50
        st.session_state.questionPageRequest = 0
        st.session_state.testQuestions = func_createQuestions(st.session_state.testPageRequest)
        st.session_state.testPageResponses = []
        st.session_state.test_id = str(uuid.uuid4())
        st.session_state.page = 'Question'
        st.experimental_rerun()

    func_sidebar(3)

def page_testWithoutLogin():
    func_withoutLoginNotice()
    st.title("테스트 응시")
    st.write("**테스트를 통해 모르는 단어를 점검해 보세요**")
    if st.button('20단어 테스트'):
        st.session_state.testPageRequest = 20
        st.session_state.questionPageRequest = 0
        st.session_state.testQuestions = func_createQuestions(st.session_state.testPageRequest)
        st.session_state.testPageResponses = []
        st.session_state.page = 'Question'
        st.experimental_rerun()
    if st.button('30단어 테스트'):
        st.session_state.testPageRequest = 30
        st.session_state.questionPageRequest = 0
        st.session_state.testQuestions = func_createQuestions(st.session_state.testPageRequest)
        st.session_state.testPageResponses = []
        st.session_state.page = 'Question'
        st.experimental_rerun()
    if st.button('50단어 테스트'):
        st.session_state.testPageRequest = 50
        st.session_state.questionPageRequest = 0
        st.session_state.testQuestions = func_createQuestions(st.session_state.testPageRequest)
        st.session_state.testPageResponses = []
        st.session_state.page = 'Question'
        st.experimental_rerun()

    func_sidebar(2)

def page_question():
    test_id = st.session_state.test_id
    if st.session_state.isLogin == True:
        func_getUserInfo(st.session_state.userId)
        func_sidebar(3)
    else:
        func_sidebar(2)

    if st.session_state.questionPageRequest == st.session_state.testPageRequest:
        st.title('테스트 결과')
        results_df = pd.DataFrame(st.session_state.testPageResponses)
        if 'processed_test_results' not in st.session_state:
            st.session_state['processed_test_results'] = {}
        if test_id not in st.session_state['processed_test_results'] and st.session_state.isLogin == True:
            st.session_state['processed_test_results'][test_id] = False
            db_instance = DB(st.session_state.userId)
            db_instance.save_result(results_df.to_dict('records'))
            st.session_state['processed_test_results'][test_id] = True
            func_saveUserInfo(st.session_state.userId, 'processed_test_results', st.session_state.processed_test_results)
            st.write("테스트 결과가 성공적으로 저장되었습니다.")
        st.write('_' * 50)
        results_df.index = results_df.index + 1
        col1, col2 = st.columns(2)
        with col1:
            st.write(f'**테스트 결과**')
            st.write(results_df, height=500)
        with col2:
            st.write(f'**{st.session_state.questionPageRequest}문항 테스트 정답률**')
            incorrect_words = []
            col1, col2, col3 = st.columns([1.5, 7, 1.5])
            with col2:
                result = results_df['correct'].value_counts()
                colors = ['orange', 'gray']
                fig1, ax1 = plt.subplots()
                ax1.pie(result, colors=colors, startangle=90)
                centre_circle = plt.Circle((0, 0), 0.75, fc='white')
                fig = plt.gcf()
                fig.gca().add_artist(centre_circle)
                ax1.text(0, 0, f'{result[0]}/{len(results_df)}', ha='center', va='center', fontsize=25, color='black')
                st.pyplot(fig1)
            st.write('_' * 20)

            st.write('**틀린 문항 확인**')
            incorrect = results_df.loc[results_df['correct'] == False]
            incorrect_words.extend(incorrect['question'].tolist())
            st.write(incorrect)
        st.write('_' * 50)
        if st.session_state.isLogin == True:
            if st.button("성적 분석"):
                st.session_state.resultPageRequest = incorrect_words
                st.session_state.page = 'Result'
                st.session_state.results_saved = False
                st.experimental_rerun()


    else:
        st.write(f'**{st.session_state.questionPageRequest + 1}/{st.session_state.testPageRequest}**')
        question = st.session_state.testQuestions[st.session_state.questionPageRequest]
        st.title(f'**{question["word"]}**')

        col1, col2 = st.columns(2)
        with col1:
            if st.button(f'1. {question["choices"][0]}', key='choice1'):
                user_answer = question["choices"][0]
                is_correct = user_answer == question['correct_answer']
                st.session_state.testPageResponses.append(
                    {'question': question['word'], 'user_answer': user_answer, 'correct': is_correct})
                st.session_state.questionPageRequest += 1
                st.experimental_rerun()
            if st.button(f'3. {question["choices"][2]}', key='choice3'):
                user_answer = question["choices"][2]
                is_correct = user_answer == question['correct_answer']
                st.session_state.testPageResponses.append(
                    {'question': question['word'], 'user_answer': user_answer, 'correct': is_correct})
                st.session_state.questionPageRequest += 1
                st.experimental_rerun()

        with col2:
            if st.button(f'2. {question["choices"][1]}', key='choice2'):
                user_answer = question["choices"][1]
                is_correct = user_answer == question['correct_answer']
                st.session_state.testPageResponses.append(
                    {'question': question['word'], 'user_answer': user_answer, 'correct': is_correct})
                st.session_state.questionPageRequest += 1
                st.experimental_rerun()
            if st.button(f'4. {question["choices"][3]}', key='choice4'):
                user_answer = question["choices"][3]
                is_correct = user_answer == question['correct_answer']
                st.session_state.testPageResponses.append(
                    {'question': question['word'], 'user_answer': user_answer, 'correct': is_correct})
                st.session_state.questionPageRequest += 1
                st.experimental_rerun()

def page_displayResultFromFiles():
    # 사용자 정보 및 파일 처리 상태 불러오기
    func_getUserInfo(st.session_state.userId)
    func_sidebar(1)

    st.title("테스트 응시 결과 분석")
    st.write("**분석할 테스트 결과 파일을 업로드해주세요.**")
    uploaded_files = st.file_uploader("Choose a CSV file", accept_multiple_files=True)

    if uploaded_files:
        if 'processed_files' not in st.session_state:
            st.session_state['processed_files'] = {}

        incorrect_words = []

        for file in uploaded_files:
            safe_name = sanitize_filename(file.name)
            if safe_name not in st.session_state['processed_files']:
                st.session_state['processed_files'][safe_name] = False  # 파일 처리 상태 초기화

                name = file.name
                st.write(name)
                file_data = pd.read_csv(file)
                file_data = pd.DataFrame(file_data)
                results_df = file_data.drop(columns=['Unnamed: 0'])

                db_instance = DB(st.session_state.userId)
                db_instance.save_result(results_df.to_dict('records'))
                st.session_state['processed_files'][safe_name] = True
                func_saveUserInfo(st.session_state.userId, 'processed_files', st.session_state.processed_files)

                file_data.index = file_data.index + 1
                col1, col2 = st.columns(2)
                with col1:
                    result = file_data.drop(columns=['Unnamed: 0'])
                    st.write(result)
                with col2:
                    st.write(f"{name.split('-')[0]}년 {name.split('-')[1]}월 {name.split('-')[2][:2]}일 응시")
                    st.write(f'**{len(file_data)}문항 테스트 응시 결과**')
                    col1, col2, col3 = st.columns([1.5, 7, 1.5])
                    with col2:
                        result = result['correct'].value_counts()
                        colors = ['orange', 'gray']
                        fig1, ax1 = plt.subplots()
                        ax1.pie(result, colors=colors, startangle=90)
                        centre_circle = plt.Circle((0, 0), 0.75, fc='white')
                        fig = plt.gcf()
                        fig.gca().add_artist(centre_circle)
                        ax1.text(0, 0, f'{result[0]}/{len(file_data)}', ha='center', va='center', fontsize=25,
                                 color='black')
                        st.pyplot(fig1)

                    st.write('_' * 20)

                    st.write('**틀린 문항 확인**')
                    incorrect = file_data.loc[file_data['correct'] == False]
                    incorrect_words.extend(incorrect['question'].tolist())
                    incorrect = incorrect.drop(columns=['Unnamed: 0', 'correct'])
                    st.write(incorrect)
                st.write('_' * 50)

                if st.session_state['processed_files'][safe_name]:
                    st.write("테스트 결과가 성공적으로 저장되었습니다.")

            else:
                st.write('이미 업로드한 파일입니다')

        safe_names = [sanitize_filename(file.name) for file in uploaded_files]

        if uploaded_files and all(st.session_state['processed_files'].get(safe_name, False) for safe_name in safe_names):
            if st.button("Submit"):
                st.session_state.resultPageRequest = incorrect_words
                st.session_state.page = 'MyPage'
                st.experimental_rerun()

def page_result():
    if st.session_state.isLogin == True:
        func_getUserInfo(st.session_state.userId)
    func_sidebar(3)
    st.title("틀린 단어 학습")
    if st.button('학습 완료'):
        st.session_state.page = 'Home'
        st.experimental_rerun()
    st.markdown('<hr style="border:1.5px solid black">', unsafe_allow_html=True)
    incorrect_words = st.session_state.resultPageRequest
    for word in incorrect_words:
        word_row = word_data.loc[word_data['영어단어'] == word].iloc[0]
        wordId = word_row['번호']
        word = word_row['영어단어']
        theme = word_row['테마']
        pos1 = word_row['품사1']
        pos2 = word_row['품사2']
        pos3 = word_row['품사3']
        meaning1 = word_row['의미1']
        meaning2 = word_row['의미2']
        meaning3 = word_row['의미3']
        example1 = word_row['예시문1']
        example2 = word_row['예시문2']
        example3 = word_row['예시문3']

        wordId = wordId.astype(np.string_)
        with st.form(key=wordId):
            st.title(word)
            st.write(f'**테마: {theme}**')
            st.write('_' * 50)
            col1, col2, col3 = st.columns([2, 1, 7])
            with col1:
                st.write(f'**{meaning1}**')
            with col2:
                st.write(f'{pos1}')
            with col3:
                st.write(example1)
            st.write('_' * 50)

            if not pd.isna(pos2):
                col1, col2, col3 = st.columns([2, 1, 7])
                with col1:
                    st.write(f'**{meaning2}**')
                with col2:
                    st.write(f'{pos2}')
                with col3:
                    st.write(example2)
                st.write('_' * 50)

            if not pd.isna(pos3):
                col1, col2, col3 = st.columns([2, 1, 7])
                with col1:
                    st.write(f'**{meaning3}**')
                with col2:
                    st.write(f'{pos3}')
                with col3:
                    st.write(example3)
                st.write('_' * 50)

            if st.form_submit_button('북마크 추가'):
                wordId = int(wordId)
                st.session_state.bookmarks.add(wordId)
                if st.session_state.isLogin == True:
                    func_saveUserInfo(user_id=st.session_state.userId, info_type='bookmarks',data=st.session_state.bookmarks)
                st.experimental_rerun()

def page_analysis():
    func_getUserInfo(st.session_state.userId)
    func_sidebar(4)
    if 'process' not in st.session_state:
        st.session_state.process = False
    if st.session_state.process:
        st.warning('응시한 결과가 반영되지 않았다면, 로그아웃을 시도한 후 다시 로그인을 시도하십시오.')
        st.title('성적 분석')
        st.subheader(f'{st.session_state.username} 님은 현재 {st.session_state.level} level입니다.')
        if st.session_state.resultsDB_error_rate > 25:
            st.write('**아직 실력이 부족해요! 단어 학습하기부터 차근차근 진행하는 것을 추천해요!**')
            if st.session_state.level != 'Beginner':
                st.write('**지금은 Beginner level이 적당해요**')
                st.session_state.level = 'Beginner'
                func_saveUserInfo(st.session_state.userId, 'level', st.session_state.level)
        elif st.session_state.resultsDB_error_rate > 10:
            st.write('**잘하고 있어요! 아래에서 틀린 단어 위주로 학습하면 실력을 더 올릴 수 있을거에요.**')
        elif st.session_state.resultsDB_error_rate > 5:
            st.write(f'**휼륭해요! {st.session_state.username} 님 수준이면, Intermediate level이 적당해요.**')
            st.session_state.level = 'Intermediate'
            func_saveUserInfo(st.session_state.userId, 'level', st.session_state.level)
        else:
            st.write(f'**완벽해요! 단어 학습이 제대로 되어 있습니다. {st.session_state.username} 님 수준이면, **Advanced** level이 적당해요.**')
        st.write('-'*50)
        col1, col2 = st.columns(2)
        with col1:
            st.write(f'**누적 오답률:**')
            sizes = [st.session_state.resultsDB_error_rate, 100-st.session_state.resultsDB_error_rate]
            colors = ['orange', 'gray']
            fig1, ax1 = plt.subplots()
            ax1.pie(sizes, colors=colors, startangle=90, counterclock=False)
            centre_circle = plt.Circle((0, 0), 0.80, fc='white')
            fig = plt.gcf()
            fig.gca().add_artist(centre_circle)
            ax1.text(0, 0, f'{st.session_state.resultsDB_error_rate:.2f}%', ha='center', va='center', fontsize=20, color='black')
            ax1.axis('equal')
            st.pyplot(fig1)
        with col2:
            st.write(f'**누적 응시 횟수: {len(st.session_state.resultsDB)}**')

            bookmark_count = len(st.session_state.resultsDB)
            total_icons = 10
            filled_icons = floor(bookmark_count / total_icons)
            partial_fill = (bookmark_count % total_icons) / total_icons

            def create_icon_html(filled, partial_fill=0):
                filled_icon = '<i class="fas fa-file-alt" style="color: orange; font-size: 24px; margin-right: 10px;"></i>'
                empty_icon = '<i class="fas fa-file-alt" style="color: lightgrey; font-size: 24px; margin-right: 10px;"></i>'
                partial_icon = f'<i class="fas fa-file-alt" style="color: orange; opacity: {partial_fill}; font-size: 24px; margin-right: 10px;"></i>'

                icons_html = filled_icon * filled + (partial_icon if partial_fill else empty_icon) + empty_icon * (
                        total_icons - filled - 1)
                return icons_html

            icons_html = create_icon_html(filled_icons, partial_fill)
            st.markdown(f'<div style="display: flex;">{icons_html}</div>', unsafe_allow_html=True)

            st.markdown(
                '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">',
                unsafe_allow_html=True)

            st.write('**성적 분석 결과 동향**')
            analysis_data = st.session_state.analysis_data
            error_rates = [result['error_rate'] for result in analysis_data]
            test_attempts = [data['test_attempts'] for data in analysis_data]
            timestamps = [datetime.datetime.fromisoformat(result['timestamp']).strftime('%y-%m-%d') for result in analysis_data]

            fig, ax1 = plt.subplots(figsize=(10, 5))

            color = 'gray'
            ax2 = ax1.twinx()
            ax2.set_ylabel('누적 응시 횟수', color=color, fontsize=25, fontproperties=font_prop)
            ax2.plot(timestamps, test_attempts, color=color, marker='o', linestyle='-', linewidth=2, zorder=2)
            ax2.tick_params(axis='y', labelcolor=color)

            color = 'orange'
            ax1.set_ylabel('누적 오답률(%)', color=color, fontsize=25, fontproperties=font_prop)
            ax1.plot(timestamps, error_rates, color=color, marker='o', linestyle='-', linewidth=2, zorder=1)
            ax1.tick_params(axis='y', labelcolor=color)
            ax1.set_xticklabels(timestamps, fontsize=20)

            plt.title('Recent Analysis Results', fontsize=25)
            plt.show()

            fig.tight_layout()
            st.pyplot(fig)

        st.write('-'*50)
        st.subheader('복습 테스트')
        st.write('**이전에 틀린 단어들로 이루어진 테스트를 통해, 실력을 향상시켜보세요!**')
        if st.button('복습 테스트 응시'):
            resultsDB_incorrect_stats = st.session_state.resultsDB_incorrect_stats
            st.session_state.test_id = str(uuid.uuid4())
            st.session_state.testQuestions = func_createReviewQuestions(resultsDB_incorrect_stats)
            st.session_state.testPageRequest = len(st.session_state.testQuestions)
            st.session_state.questionPageRequest = 0
            st.session_state.testPageResponses = []
            st.session_state.page = 'ReviewTest'
            st.experimental_rerun()

        st.write('-'*50)
        st.subheader('자주 틀리는 단어 TOP 5')
        st.write('')
        resultsDB_incorrect_stats = st.session_state.resultsDB_incorrect_stats
        resultsDB_incorrect_stats = resultsDB_incorrect_stats.sort_values(by='incorrect_rate', ascending=False)
        for result in resultsDB_incorrect_stats.head(5)['question']:
            word_row = word_data.loc[word_data['영어단어'] == result].iloc[0]
            wordId = word_row['번호']
            word = word_row['영어단어']
            theme = word_row['테마']
            pos1 = word_row['품사1']
            pos2 = word_row['품사2']
            pos3 = word_row['품사3']
            meaning1 = word_row['의미1']
            meaning2 = word_row['의미2']
            meaning3 = word_row['의미3']
            example1 = word_row['예시문1']
            example2 = word_row['예시문2']
            example3 = word_row['예시문3']

            wordId = wordId.astype(np.string_)
            with st.form(key=wordId):
                st.title(word)
                st.write(f'**테마: {theme}**')
                st.write('_' * 50)
                col1, col2, col3 = st.columns([2, 1, 7])
                with col1:
                    st.write(f'**{meaning1}**')
                with col2:
                    st.write(f'{pos1}')
                with col3:
                    st.write(example1)
                st.write('_' * 50)

                if not pd.isna(pos2):
                    col1, col2, col3 = st.columns([2, 1, 7])
                    with col1:
                        st.write(f'**{meaning2}**')
                    with col2:
                        st.write(f'{pos2}')
                    with col3:
                        st.write(example2)
                    st.write('_' * 50)

                if not pd.isna(pos3):
                    col1, col2, col3 = st.columns([2, 1, 7])
                    with col1:
                        st.write(f'**{meaning3}**')
                    with col2:
                        st.write(f'{pos3}')
                    with col3:
                        st.write(example3)
                    st.write('_' * 50)

                incorrect_rate = resultsDB_incorrect_stats[resultsDB_incorrect_stats['question'] == result]['incorrect_rate'].values[0]
                responses = resultsDB_incorrect_stats[resultsDB_incorrect_stats['question'] == result]['responses'].values[0]
                st.write(f'**단어별 누적 오답률: {round(incorrect_rate)}%**')
                st.write('**내가 선택한 오답:**', ", ".join(responses))

                if st.form_submit_button('북마크 추가'):
                    wordId = int(wordId)
                    st.session_state.bookmarks.add(wordId)
                    if st.session_state.isLogin == True:
                        func_saveUserInfo(user_id=st.session_state.userId, info_type='bookmarks',
                                          data=st.session_state.bookmarks)
                    st.experimental_rerun()

    else:
        st.info('데이터베이스에서 분석할 데이터를 가져오고 있습니다')
        db_instance = DB(st.session_state.userId)
        resultsDB = db_instance.get_results()
        if resultsDB:
            st.session_state.resultsDB = resultsDB
            results = []
            for result in resultsDB:
                results.append(pd.DataFrame(st.session_state.resultsDB[f'{result}']))
            all_result_df = pd.concat(results, ignore_index=True)

            total_questions = len(all_result_df)
            incorrect_questions = all_result_df['correct'].value_counts().get(False)
            error_rate = (incorrect_questions / total_questions) * 100 if total_questions else 0
            if 'resultsDB_error_rate' not in st.session_state:
                st.session_state.resultsDB_error_rate = error_rate

            incorrect_answers = all_result_df[all_result_df['correct'] == False]
            word_counts = all_result_df['question'].value_counts()  # Total occurrences of each word

            incorrect_stats = incorrect_answers.groupby('question').apply(lambda x: pd.Series({
                'total_incorrect': len(x),
                'incorrect_rate': (len(x) / word_counts[x.name]) * 100,  # Use total occurrences for rate calculation
                'responses': list(x['user_answer'])
            })).reset_index()

            if 'resultsDB_incorrect_stats' not in st.session_state:
                st.session_state.resultsDB_incorrect_stats = incorrect_stats

            st.session_state.process = True

            if st.session_state.process:
                analysis_data = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'error_rate': st.session_state.resultsDB_error_rate,
                    'test_attempts': len(st.session_state.resultsDB)
                }
                func_saveAnalysisData(st.session_state.userId, analysis_data)
                st.success('분석 결과가 성공적으로 업로드되었습니다.')

            st.experimental_rerun()
        else:
            st.warning('분석할 데이터가 없습니다. 테스트 결과를 업로드하거나 테스트 응시를 먼저 진행해주세요.')

def page_reviewTest():
    func_getUserInfo(st.session_state.userId)
    func_sidebar(4)

    test_id = st.session_state.test_id

    if st.session_state.questionPageRequest == st.session_state.testPageRequest:
        st.title('테스트 결과')
        results_df = pd.DataFrame(st.session_state.testPageResponses)
        if 'processed_test_results' not in st.session_state:
            st.session_state['processed_test_results'] = {}
        if test_id not in st.session_state['processed_test_results']:
            st.session_state['processed_test_results'][test_id] = False
            db_instance = DB(st.session_state.userId)
            db_instance.save_result(results_df.to_dict('records'))
            st.session_state['processed_test_results'][test_id] = True
            func_saveUserInfo(st.session_state.userId, 'processed_test_results',
                              st.session_state.processed_test_results)
        st.write("테스트 결과가 성공적으로 저장되었습니다.")
        st.write('_' * 50)
        results_df.index = results_df.index + 1
        col1, col2 = st.columns(2)
        with col1:
            st.write(f'**테스트 결과**')
            st.write(results_df, height=500)
        with col2:
            st.write(f'**{st.session_state.questionPageRequest}문항 테스트 정답률**')
            incorrect_words = []
            col1, col2, col3 = st.columns([1.5, 7, 1.5])
            with col2:
                result = results_df['correct'].value_counts()
                colors = ['orange', 'gray']
                fig1, ax1 = plt.subplots()
                ax1.pie(result, colors=colors, startangle=90)
                centre_circle = plt.Circle((0, 0), 0.75, fc='white')
                fig = plt.gcf()
                fig.gca().add_artist(centre_circle)
                ax1.text(0, 0, f'{result[0]}/{len(results_df)}', ha='center', va='center', fontsize=25, color='black')
                st.pyplot(fig1)
            st.write('_' * 20)

            st.write('**틀린 문항 확인**')
            incorrect = results_df.loc[results_df['correct'] == False]
            incorrect_words.extend(incorrect['question'].tolist())
            st.write(incorrect)
        st.write('_' * 50)
        if st.button("성적 분석"):
            st.session_state.resultPageRequest = incorrect_words
            st.session_state.page = 'Result'
            st.session_state.results_saved = False
            st.experimental_rerun()
    else:
        st.write(f'**{st.session_state.questionPageRequest + 1}/{st.session_state.testPageRequest}**')
        question = st.session_state.testQuestions[st.session_state.questionPageRequest]
        st.title(f'**{question["word"]}**')

        if 'selected_answer' in st.session_state:
            st.write(f"**내가 선택한 선지: {st.session_state['selected_answer'][0]}**")
            if st.session_state['selected_answer'][1]:  # If the answer was correct
                st.success('Correct answer!')
            else:
                st.error('Wrong answer!')

            st.write('')
            resultsDB_incorrect_stats = st.session_state.resultsDB_incorrect_stats
            word_row = word_data.loc[word_data['영어단어'] == question["word"]].iloc[0]
            wordId = word_row['번호']
            word = word_row['영어단어']
            theme = word_row['테마']
            pos1 = word_row['품사1']
            pos2 = word_row['품사2']
            pos3 = word_row['품사3']
            meaning1 = word_row['의미1']
            meaning2 = word_row['의미2']
            meaning3 = word_row['의미3']
            example1 = word_row['예시문1']
            example2 = word_row['예시문2']
            example3 = word_row['예시문3']

            wordId = wordId.astype(np.string_)
            with st.form(key=wordId):
                st.title(word)
                st.write(f'**테마: {theme}**')
                st.write('_' * 50)
                col1, col2, col3 = st.columns([2, 1, 7])
                with col1:
                    st.write(f'**{meaning1}**')
                with col2:
                    st.write(f'{pos1}')
                with col3:
                    st.write(example1)
                st.write('_' * 50)
                if not pd.isna(pos2):
                    col1, col2, col3 = st.columns([2, 1, 7])
                    with col1:
                        st.write(f'**{meaning2}**')
                    with col2:
                        st.write(f'{pos2}')
                    with col3:
                        st.write(example2)
                    st.write('_' * 50)
                if not pd.isna(pos3):
                    col1, col2, col3 = st.columns([2, 1, 7])
                    with col1:
                        st.write(f'**{meaning3}**')
                    with col2:
                        st.write(f'{pos3}')
                    with col3:
                        st.write(example3)
                    st.write('_' * 50)

                responses = \
                resultsDB_incorrect_stats[resultsDB_incorrect_stats['question'] == question['word']]['responses'].values[0]
                st.write('**내가 선택한 오답:**', ", ".join(responses))

                if st.form_submit_button('북마크 추가'):
                    wordId = int(wordId)
                    st.session_state.bookmarks.add(wordId)
                    if st.session_state.isLogin == True:
                        func_saveUserInfo(user_id=st.session_state.userId, info_type='bookmarks',
                                          data=st.session_state.bookmarks)
                    st.experimental_rerun()

            if st.button('Next', key='next_button'):
                st.session_state.testPageResponses.append({
                    'question': question['word'],
                    'user_answer': st.session_state['selected_answer'][0],
                    'correct': st.session_state['selected_answer'][1]
                })
                st.session_state.questionPageRequest += 1
                del st.session_state['selected_answer']
                st.experimental_rerun()
        else:
            col1, col2 = st.columns(2)
            choices = question["choices"]
            for idx, choice in enumerate(choices, start=1):
                if idx % 2 == 1:
                    container = col1
                else:
                    container = col2
                if container.button(f'{idx}. {choice}', key=f'choice{idx}'):
                    is_correct = choice == question['correct_answer']
                    st.session_state['selected_answer'] = (choice, is_correct)
                    st.experimental_rerun()

def page_textAnalysis():
    st.title("지문 분석(beta)")
    st.write("**지문 분석 기능은 구현했으나, minor한 기능이라 beta로 구분했습니다.**")
    func_textAnalysis()

    func_sidebar(5)

def page_info():
    func_withoutLoginNotice()

    if st.session_state.isLogin == True:
        func_sidebar(6)
    else:
        func_sidebar(3)

    st.title("단어장 정보")
    col1, col2 = st.columns(2)
    with col1:
        with st.container():
            draw_figure1()
            col3, col4 = st.columns([1.2,8])
            with col4:
                st.markdown(f"""
                    <div style="color: orange; font-weight: bold; font-size: 15px; line-height: 0.7;">
                        데이터과학 comment
                    </div>
                    """, unsafe_allow_html=True)
                st.write('1600개의 단어 중, 동사와 명사로 쓰이는 단어가 가장 많았습니다.')
    with col2:
        with st.container():
            obtion = st.selectbox('**품사별 단어 학습 전략**',('명사', '동사'))
            if obtion == '명사':
                st.write('**명사 학습 전략**')
                st.write('1. **분류별 학습**: 명사를 그룹화하여 학습하는 것이 좋습니다. 예를 들어, 생활용품, 식료품, 직업, 장소 등으로 분류하여 각 카테고리에 속한 명사를 함께 배울 수 있습니다. 이 방법은 관련 단어들 사이의 연관성을 이해하는 데 도움이 됩니다.')
                st.write('2. **시각 자료 활용**: 명사는 구체적인 사물이나 개념을 나타내므로 이미지, 사진 또는 실제 물건을 사용하여 학습하는 것이 효과적입니다. 이를 통해 단어와 그 대상의 시각적 연관성을 강화할 수 있습니다.')
                st.write("3. **맥락 연결**: 명사를 배울 때 그 명사가 사용되는 일반적인 상황이나 문맥을 함께 고려하면 좋습니다. 예를 들어 '커피'(명사)는 '마시다', '주문하다' 등의 동사와 자주 쓰이므로 이런 연결을 이해하는 것이 중요합니다.")
            if obtion == '동사':
                st.write('**동사 학습 전략**')
                st.write('1. **동사의 변형 연습**: 동사는 시제, 인칭, 수에 따라 형태가 변하는 경우가 많으므로, 다양한 변형을 연습하는 것이 중요합니다. 이를 위해 간단한 변형 표를 만들어 연습하거나, 해당 동사를 사용한 문장을 만들어보는 것이 도움이 됩니다.')
                st.write('2. **동사의 기능 이해**: 동사는 동작, 상태, 발생을 나타내므로, 각 동사가 어떤 동작이나 상태를 의미하는지, 어떤 상황에서 사용되는지를 명확히 이해하는 것이 중요합니다. 이를 위해 동사를 문장 안에서 사용해 보고, 해당 동작을 직접 수행해 보거나 시각화해 보는 것도 좋습니다.')
                st.write("3. **동사와 명사의 조합 연습**: 동사는 특정 명사와 자주 쓰이는 경향이 있습니다. 예를 들어 '쓰다'는 '편지', '노트', '리포트' 등과 같이 사용됩니다. 이러한 조합을 함께 연습함으로써 보다 자연스럽게 언어를 사용할 수 있습니다.")

    st.write('_'*50)
    col1, col2 = st.columns(2)
    with col1:
        with st.container():
            st.write('**단어 테마 분석**')
            st.write("**TDIYD VOCA1600** 단어장은 단어를 테마 **10개**의 테마로 나눠 학습에 도움을 주고 있습니다. 그외 테마는 '기타'로 구분하였습니다. 단어의 테마 분류는 실사용에서 어떻게 사용되는지, 단어장에서 어떤 의미를 소개하고 있는지를 반영하여 생성형 AI 서비스, ChatGPT의 도움을 받아 분류하였습니다.")
            st.write('')
            st.write('**1. 일상 및 여가 생활**: 일상에서 경험하는 다양한 활동과 여가 시간을 보내는 방법에 초점을 맞춘 테마입니다. 취미, 가정 생활, 그리고 일상의 소소한 즐거움을 다룹니다.')
            st.write('**2. 문화와 예술**: 다양한 문화적 배경과 예술 형태를 탐험하는 테마입니다. 전통 예술, 현대 미술, 그리고 문화적 상징과 행사를 포함합니다.')
            st.write('**3. 음식과 요리**: 음식 준비, 조리법, 그리고 세계 각국의 요리를 소개하는 테마입니다. 건강식에서부터 길거리 음식까지, 음식에 대한 폭넓은 이해를 제공합니다.')
            st.write('**4. 정치, 법률 및 사회**: 정치 이론, 법률 체계, 그리고 사회적 이슈에 대해 다룹니다. 이 테마는 현대 사회의 구조와 그 안에서 일어나는 다양한 변화에 주목합니다.')
            st.write('**5. 건강과 의료**: 건강 유지와 질병 예방에 초점을 맞춘 테마입니다. 의료 기술의 발전과 함께, 일반인을 위한 건강 관리 팁도 다룹니다.')
            st.write('**6. 과학과 기술**: 과학적 발견과 기술적 혁신을 다루는 테마입니다. 이는 새로운 과학 이론과 일상 생활에 영향을 미치는 기술 발전을 포함합니다.')
            st.write('**7. 교육과 학습**: 학습 방법, 교육 이론, 그리고 학교 생활에 관한 정보를 제공하는 테마입니다. 이는 평생 교육의 중요성과 다양한 학습 기회에 대해 조명합니다.')
            st.write('**8. 경제, 금융 및 산업**: 경제 이론, 금융 시장, 그리고 산업 발전을 탐험하는 테마입니다. 경제적 사건과 트렌드가 개인과 사회에 미치는 영향을 다룹니다.')
            st.write('**9. 음악과 엔터테인먼트**: 음악, 영화, 그리고 다른 형태의 엔터테인먼트를 소개하는 테마입니다. 창의적인 표현과 대중 문화의 다양한 측면을 탐구합니다.')
            st.write('**10. 스포츠**: 다양한 스포츠 활동과 그에 따른 경쟁, 건강, 그리고 팀워크의 중요성을 다루는 테마입니다. 전 세계적인 스포츠 이벤트와 지역 경기까지 포함합니다.')
            st.write('**기타**: 30단어 미만으로 세팅하여 미분류된 단어의 수를 줄였습니다.')
    with col2:
        with st.container():
            draw_figure2()
            draw_figure3()
            col3, col4 = st.columns([1.2, 8])
            with col4:
                st.markdown(f"""
                                <div style="color: orange; font-weight: bold; font-size: 15px; line-height: 0.7;">
                                    데이터과학 comment
                                </div>
                                """, unsafe_allow_html=True)
                st.write("일상에서 가장 많이 쓰는 표현들을 담은 **'일상 및 여가 생활'** 테마가 주를 이뤘고, 이에는 인간 관계나 감정어 등이 포함되었습니다. 또한, 이 테마를 제외한 나머지 테마에도 적지 않은 분량의 단어를 배치하여 테마 기반 학습의 효용성을 높였습니다")

    st.write('_'*50)
    col1, col2 = st.columns(2)
    with col1:
        with st.container():
            draw_figure4()
            col3, col4 = st.columns([1.2, 8])
            with col4:
                st.markdown(f"""
                    <div style="color: orange; font-weight: bold; font-size: 15px; line-height: 0.7;">
                        데이터과학 comment
                    </div>
                    """, unsafe_allow_html=True)
                st.write("2024 수능 영어 영역에서 출제된 지문들의 테마별 단어 분포와 단어장 내 테마별 단어 분포가 유사함을 통해, 해당 단어장이 수능 영어 공부에 실질적으로 도움이 될 수 있음을 알 수 있었습니다.")
    with col2:
        with st.container():
            draw_figure5()

def page_myPage():
    if st.session_state.isLogin == True:
        func_getUserInfo(st.session_state.userId)
    st.title('My Page')
    with st.form("update_info"):
        st.subheader('사용자 기본 정보')
        new_username = st.text_input('사용자 이름', value=st.session_state.username)
        new_level = st.selectbox('사용자 level', ['Beginner', 'Intermediate', 'Advanced'],
                                 index=['Beginner', 'Intermediate', 'Advanced'].index(st.session_state.level))
        new_dailyamount = st.selectbox('Day별 학습량', [25, 40, 50], index=[25, 40, 50].index(st.session_state.dailyamount))

        submit_button = st.form_submit_button("수정하기")
        if submit_button:
            st.session_state.username = new_username
            st.session_state.level = new_level
            st.session_state.dailyamount = new_dailyamount
            st.session_state.sessionnumber = 1600 // new_dailyamount
            st.session_state.completed_days = [False]*st.session_state.sessionnumber
            func_saveUserInfo(st.session_state.userId, 'username', new_username)
            func_saveUserInfo(st.session_state.userId, 'level', new_level)
            func_saveUserInfo(st.session_state.userId, 'dailyamount', new_dailyamount)
            func_saveUserInfo(st.session_state.userId, 'sessionnumber', st.session_state.sessionnumber)
            func_saveUserInfo(st.session_state.userId, 'completed_days', st.session_state.completed_days)
            st.success('정보가 성공적으로 업데이트되었습니다.')

    st.write('')
    with st.form('DB 정보'):
        st.subheader('DB 정보')
        st.write('사용자 DB ID: ', st.session_state.userId)
        st.write('테스트 응시 데이터:')

        if st.form_submit_button('파일에서 테스트 결과 업로드'):
            st.session_state.page = 'DisplayResultFromFiles'
            st.experimental_rerun()

    st.write('')

    if st.button('회원탈퇴'):
        user_email = st.session_state.email
        success, message = Auth.delete_firebase_user(user_email)
        if success:
            db_instance = DB(st.session_state.userId)
            db_instance.delete_user_info()
            db_instance.delete_result()
            st.session_state.clear()
            st.success(message)
            st.experimental_rerun()
        else:
            st.error(message)

    st.write('기타 문의(이메일): songyu0205@naver.com')

    func_sidebar(1)

if 'sessionId' not in st.session_state:
    st.session_state['sessionId'] = str(uuid.uuid4())

if 'isLogin' not in st.session_state:
    st.session_state['isLogin'] = False
if 'userId' not in st.session_state:
    st.session_state.userId = None
if 'username' not in st.session_state:
    st.session_state.username = 'DSHS'
if 'dailyamount' not in st.session_state:
    st.session_state.dailyamount = 40
if 'sessionnumber' not in st.session_state:
    st.session_state.sessionnumber = 40
if 'sessionnumber' not in st.session_state:
    st.session_state.level = None
if 'bookmarks' not in st.session_state:
    st.session_state.bookmarks = set()
if 'learnPageRequest' not in st.session_state:
    st.session_state.learnPageRequest = 0
if 'dayPageRequest' not in st.session_state:
    st.session_state.dayPageRequest = 0
if 'testPageRequest' not in st.session_state:
    st.session_state.testPageRequest = 50
if 'test_id' not in st.session_state:
    st.session_state.test_id = 0
if 'questionPageRequest' not in st.session_state:
    st.session_state.questionPageRequest = 0
if 'testPageResponses' not in st.session_state:
    st.session_state.testPageResponses = 0
if 'testQuestions' not in st.session_state:
    st.session_state.testQuestions = []
if 'resultPageRequest' not in st.session_state:
    st.session_state.resultPageRequest = []
if 'completed_days' not in st.session_state:
    st.session_state.completed_days = []


if 'page' not in st.session_state:
    st.session_state.page = 'Login'

if st.session_state.page == 'Login':
    page_login()
elif st.session_state.page == 'Register':
    page_register()
elif st.session_state.page == 'Home':
    page_home()
elif st.session_state.page == 'ResetPassword':
    page_resetPassword()
elif st.session_state.page == 'InputUsername':
    page_inputUsername()
elif st.session_state.page == 'SelectLevel':
    page_selectLevel()
elif st.session_state.page == 'SelectDailyAmount':
    page_selectDailyAmount()
elif st.session_state.page == 'Learn':
    page_learn()
elif st.session_state.page == 'Day':
    page_day()
elif st.session_state.page == 'Test':
    page_test()
elif st.session_state.page == 'TestWithoutLogin':
    page_testWithoutLogin()
elif st.session_state.page == 'Question':
    page_question()
elif st.session_state.page == 'Bookmark':
    page_bookmark()
elif st.session_state.page == 'DisplayResultFromFiles':
    page_displayResultFromFiles()
elif st.session_state.page == 'Result':
    page_result()
elif st.session_state.page == 'Analysis':
    page_analysis()
elif st.session_state.page == 'ReviewTest':
    page_reviewTest()
elif st.session_state.page == 'TextAnalysis':
    page_textAnalysis()
elif st.session_state.page == 'Info':
    page_info()
elif st.session_state.page == 'MyPage':
    page_myPage()
