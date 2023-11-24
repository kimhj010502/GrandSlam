from flask import Flask, render_template, request, flash, session, redirect, url_for
import sys
import chardet

#DB 연결
from database import DBhandler
import hashlib
import json

#웹 크롤링
from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService


from datetime import datetime, timedelta
import requests

#그래프
import os.path
from os import path

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import plotly.graph_objects as go
from plotly.offline import iplot
import plotly.io as po
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler
import plotly.express as px

#경고 무시
import warnings
warnings.filterwarnings('ignore')

#matplotlib 한글 깨짐 방지
plt.rc('font', family='NanumBarunGothic')


application = Flask(__name__)
application.secret_key = 'grand_slam'

DB = DBhandler()

team = ['LG', '두산', '삼성', '롯데', '키움', 'KIA', '한화', 'NC', 'KT', 'SSG']

team_eng = {
    'LG': 'LG', 
    '두산': 'Doosan',
    '삼성': 'Samsung',
    '롯데': 'Lotte',
    '키움': 'Kiwoom',
    'KIA': 'KIA',
    '한화': 'Hanwha',
    'NC': 'NC',
    'KT': 'KT',
    'SSG': 'SSG' 
}

team_colors = {
    'SSG':'#CE0E2D',
    '키움':'#570514',
    'LG':'#C30452',
    'KT':'#000000',
    'KIA':'#EA0029',
    'NC':'#315288',
    '삼성':'#074CA1',
    '롯데':'#041E42',
    '두산':'#131230',
    '한화':'#FF6600'
}

today = datetime.today() #오늘 날짜

#필요한 파일 불러오기
team_df = pd.read_csv('static/data/final_team.csv')
player_df = pd.read_csv('static/data/final_player.csv')
match_df = None
team_info = pd.read_csv('static/data/team_information.csv')

hitter_df = pd.read_csv('static/data/hitter.csv', encoding='cp949')
pitcher_df = pd.read_csv('static/data/pitcher.csv')
defense_df = pd.read_csv('static/data/defense.csv')
ranking_df = pd.read_csv('static/data/teamrank_final.csv', encoding='cp949')

# Chrome WebDriver 실행

#웹 드라이버의 위치를 파이썬의 위치(which python)로 이동해줘야함 -> 리눅스
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=chrome_options)
print("웹드라이버")


#오늘 경기 일정 가져오기
def getTodayMatch():
    url = "https://www.koreabaseball.com/"
    driver.get(url)

    # 페이지가 로드될 때까지 기다림
    driver.implicitly_wait(3)  # 3초간 대기

    # 페이지 소스 가져오기
    html = driver.page_source

    # BeautifulSoup로 파싱
    soup = BeautifulSoup(html, "html.parser")
    game_schedule = soup.find("div", class_="today-game")
    game_info = game_schedule.find_all("li", class_="game-cont")

    game_list = []

    for game in game_info:
        location = game.find("div", class_="top").find("ul").find_all("li")[0].text
        time = game.find("div", class_="top").find("ul").find_all("li")[-1].text
        status = game.find("div", class_="middle").find("p").text
        away_team = game.find("div", class_="team away").find("img")["alt"]
        home_team = game.find("div", class_="team home").find("img")["alt"]
    
    
        #경기 전
        if status == '경기예정':
            away_pitcher = game.find("div", class_="team away").find("div", class_="today-pitcher").find("p")
            home_pitcher = game.find("div", class_="team home").find("div", class_="today-pitcher").find("p")
            
            if away_pitcher == None:
                away_pitcher = "ㅤ"
            else:
                away_pitcher = away_pitcher.text[1:]
                
            if home_pitcher == None:
                home_pitcher = "ㅤ"
            else:
                home_pitcher = home_pitcher.text[1:]

            game_info_list = [location, time, status, away_team, home_team, away_pitcher, home_pitcher]

            
        #경기 후
        elif status == '경기종료':
            away_score = int(game.find("div", class_="team away").find_all("div", class_="score")[0].text)
            home_score = int(game.find("div", class_="team home").find_all("div", class_="score")[0].text)
            away_pitcher_p = game.find("div", class_="team away").find("div", class_="today-pitcher").find("p")
            home_pitcher_p = game.find("div", class_="team home").find("div", class_="today-pitcher").find("p")

            if (away_pitcher_p == None) and (home_pitcher_p == None):
                away_pitcher, home_pitcher = 'ㅤ', 'ㅤ'
            else:
                away_pitcher = away_pitcher_p.text[1:]
                home_pitcher = home_pitcher_p.text[1:]

                if 'DH' in location:
                    location = game.find("div", class_="top").find("ul").find_all("li")[1].text
                #else:
                    #time = game.find("div", class_="top").find("ul").find_all("li")[1].text

            game_info_list = [location, time, status, away_team, away_score, home_team, home_score, away_pitcher, home_pitcher]
        
        #경기 취소
        elif status == '경기취소':
            away_pitcher = game.find("div", class_="team away").find("div", class_="today-pitcher").find("p").text[1:]
            home_pitcher = game.find("div", class_="team home").find("div", class_="today-pitcher").find("p").text[1:]
            game_info_list = [location, time, status, away_team, home_team, away_pitcher, home_pitcher]
            #print(game_info_list)

        #경기 중
        else:
            away_team_text = game.find('div', class_='team away').get_text()
            away_score = int(away_team_text[0])
            away_name = away_team_text[1:]
            home_team_text = game.find('div', class_='team home').get_text()
            home_score = int(home_team_text[0])
            home_name = home_team_text[1:]

            game_info_list = [location, time, status, away_team, away_score, home_team, home_score, away_name, home_name]

        game_list.append(game_info_list)
        
    return game_list
    
    

#팀 순위 가져오기
def getTeamRanking():
    url = 'http://www.statiz.co.kr/league.php?opt=2023'
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # 테이블을 찾아봅니다
        tables = soup.find_all('table')
        if len(tables) >= 1:
            table = tables[2]
        else:
            print("테이블을 찾지 못했습니다.")
            return

        # 데이터를 DataFrame으로 변환합니다
        rows = table.find_all('tr')
        data = []
        for row in rows:
            cells = row.find_all('td')
            row_data = [cell.get_text(strip=True) for cell in cells]
            data.append(row_data)
        data = data[1:]
        return data
    else:
        print(f"오류 발생: {response.status_code}")


#지난 경기 결과 가져오기
def getPrevMatch(year, month, day):
    #저장된 경기 정보 가져오기
    with open ("static/data/match.json", "r") as f:
        match_df = json.load(f)
        
    if month < 10:
        month = '0' + str(month)

    if day < 10:
        day = '0' + str(day)
        
    date = str(year) + "/" + str(month) + "/" + str(day)
    
    #이미 저장된 경기라면 바로 불러오기
    if date in match_df["match_date"]:
        return match_df[date]
    
    prev_match_url = "http://www.statiz.co.kr/boxscore.php?opt=1&sopt=0&date={year}-{month}-{day}"
    prev_match = []
    
    data_url = prev_match_url.format(year=year, month=month, day=day)
    print(data_url)
    req = requests.get(data_url)
    html = req.text
    soup = BeautifulSoup(html, 'html.parser')

    #경기장 정보
    stadium_list = []
    for i in soup.find_all("h3", "box-title"):
        stadium_list.append(i.text)
    stadium_list = stadium_list[1:]
    stadium_list = [stadium.split('(')[1][:-1] for stadium in stadium_list]
    #print(stadium_list)

    #경기 정보
    match_list = []
    for game in soup.find_all("div", "box-body"):
        match_list.append(game.text.split())
    #print(match_list)

    #결과
    prev_match = []
    for i in range(1,len(match_list)):
        #오류 예외처리 (추가적인 DB 수정 필요)
        if match_list[i][0] == '패':
            match_list[i] = ['승', '수정', '(-)'] + match_list[i]
        
        if match_list[i][0] == '승' or match_list[i][0] == 'Best':
            prev_match.append(match_list[i-1] + match_list[i])
        elif match_list[i][1] == '우천취소':
            prev_match.append(match_list[i])
        else: 
            continue

    #필요없는 정보 버리고 수정하기
    for i in range(len(stadium_list)):
        prev_match[i] = [stadium_list[i]] + prev_match[i]

        #print(prev_match[i], end = " ")

        if prev_match[i][2] == '우천취소':
            continue

        #비긴 경우
        if prev_match[i][6] == prev_match[i][9]:
            # 인덱스 버리기
            remove_index = [1,2,3,5,8]
            prev_match[i] = [item for idx, item in enumerate(prev_match[i]) if idx not in remove_index]

        #승패가 결정된 경우
        else:
            # 세이브 버리기
            if prev_match[i][16]=='세':
                del prev_match[i][15:18]
                
            #print(prev_match[i])
            
            # 인덱스 버리기
            remove_index = [1,2,3,5,8,10,12,13,15]
            prev_match[i] = [item for idx, item in enumerate(prev_match[i]) if idx not in remove_index]
            
            # 선발투수 이름 순서 맞추기
            if prev_match[i][2] < prev_match[i][4]:
                prev_match[i][5], prev_match[i][6] = prev_match[i][6], prev_match[i][5]

        # 스코어 int로 바꾸기
        score_index = [2,4]
        for idx in score_index:
            prev_match[i][idx] = int(prev_match[i][idx])

    del prev_match[len(stadium_list):]
    #print(prev_match)

    match_df["match_date"].append(date)
    match_df[date] = prev_match
    #print(match_df)
    
    #새로운 데이터도 저장
    with open('static/data/match.json', 'w', encoding='utf-8') as outfile:
        json.dump(match_df, outfile, indent=4, ensure_ascii=False)
    
    return prev_match


#팀 순위 DataFrame 반환
def getRankingDF():
    ranking_now = getTeamRanking()
    ranking_now_df = pd.DataFrame(ranking_now,columns=['순위','팀명','경기','승','패','무','게임차','WPCT'])
    ranking_now_df.loc[0,'게임차']=0.0
    
    # 2018~2022 실제순위, 2023 현재순위, 2023 예측순위를 모두 포함한 최종 순위 df
    df_rank_final = pd.concat([ranking_df, ranking_now_df[['팀명','순위','WPCT']]], axis=0, ignore_index=True)
    df_rank_final['year'].fillna('2023(현재)', inplace=True)
    df_rank_final = df_rank_final[['팀명','year','WPCT','순위']]
    df_rank_final = df_rank_final.astype({'순위': 'int'})
    
    return df_rank_final


#팀 순위 그래프 삭제
def delTeamRankingPlot():
    dir_path = "static/ranking_plot"
    if os.path.exists(dir_path):
        for file in os.scandir(dir_path):
            os.remove(file)      
    return


#팀 5개년 순위 그래프
def plot_team_ranking_1(df_rank_final):
    file_path = "static/ranking_plot/team_ranking_1.html"
    
    # 2023년도 데이터만 추출
    df_2023 = df_rank_final[(df_rank_final['year'] == '2023(현재)') | (df_rank_final['year'] == '2023(예측)')]
    
    # Pivot 테이블 생성
    pivot_df = df_2023.pivot_table(index=['팀명', 'year'], values='순위', aggfunc='mean').reset_index()

    # 2023(현재) 및 '2023(예측)' 데이터를 기준으로 팀명 순서 정렬
    team_order = pivot_df[pivot_df['year'] == '2023(현재)'].sort_values(by='순위')['팀명'].tolist()

    # '2023(현재)' 및 '2023(예측)' 데이터 정렬
    pivot_df['팀명'] = pd.Categorical(pivot_df['팀명'], categories=team_order, ordered=True)
    pivot_df = pivot_df.sort_values(by=['팀명', 'year'])
    
    
    # 팀 로고 경로 리스트
    logo_url = 'https://raw.githubusercontent.com/pinkdolphin11/MY/main/' #'static/img/'
    team_logo = [logo_url+'LG.png', logo_url+'KT.png', logo_url+'NC.png', logo_url+'Doosan.png', logo_url+'KIA.png',
                 logo_url+'SSG.png', logo_url+'Lotte.png', logo_url+'Hanwha.png', logo_url+'Samsung.png', logo_url+'Kiwoom.png']
    
    # 그래프 그리기
    fig = px.line(pivot_df, x='팀명', y='순위', color='year', labels={'팀명': '팀', '순위': '순위'}, title='2023 예측&실제 순위')

    # X 축 순서 설정
    fig.update_xaxes(categoryorder='array', categoryarray=team_order)

    # Y 축 눈금 설정
    fig.update_layout(yaxis=dict(tickmode='array', tickvals=list(range(1, 11)), ticktext=list(range(1, 11))))
    fig.update_yaxes(autorange="reversed")

    # 마우스를 갖다대면 해당 팀명을 표시
    fig.update_traces(mode='lines+markers')

    # 로고 이미지 추가
    img_width = 0.15  # 이미지 너비 조절
    img_height = 0.15  # 이미지 높이 조절
    for i, img_path in enumerate(team_logo):
        x_position = i * (1 / len(team_order)) + (1 / len(team_order)) / 2  # x 위치 조정
        fig.add_layout_image(
            source=img_path,
            x=x_position,
            y=-0.12,  # 이미지가 축 아래에 표시되도록 y 값 조정
            xanchor='center',
            yanchor='bottom',
            sizex=img_width,  # 이미지 크기 조절
            sizey=img_height,
        )
        
    # 그래프 출력
    fig.update_xaxes(showticklabels=False, title_text='')
    
    # 제목 없애기
    fig.update_layout(title="")
    
    #그래프 html로 저장
    fig.write_html(file_path)
    
    return file_path


#팀 예측 vs 현재 순위 변화 그래프
def plot_team_ranking_2(df_rank_final):
    file_path = "static/ranking_plot/team_ranking_2.html"
    
    # 2023(예측) 제외한 데이터만 필터링
    filtered_df = df_rank_final[df_rank_final['year'] != '2023(예측)']


    # Pivot 테이블 생성
    pivot_df = filtered_df.pivot_table(index=['팀명', 'year'], values='순위').reset_index()

    fig = px.line(pivot_df, x='year', y='순위', color='팀명', labels={'year': '연도', '순위': '순위'},
                  title='2023 예측 vs 현재 팀별 순위 변화',
                  color_discrete_map=team_colors)

    # x축 범위
    fig.update_xaxes(type='category')

    # y축 눈금
    fig.update_layout(yaxis=dict(tickmode='array', tickvals=list(range(1, 11)), ticktext=list(range(1, 11))))
    fig.update_yaxes(autorange="reversed")

    # 마우스를 갖다대면 해당 팀명을 표시
    fig.update_traces(mode='lines+markers')
    
    # 제목 없애기
    fig.update_layout(title="")
    
    # 범례 표시 설정
    fig.update_layout(showlegend=True)
    
    #그래프 html로 저장
    fig.write_html(file_path)
    
    return file_path

#팀 순위 변화 그래프
def plot_team_ranking_3(df_rank_final):
    file_path = "static/ranking_plot/team_ranking_3.html"

    # 2023 데이터만 필터링
    filtered_df = df_rank_final[df_rank_final['year'].isin(['2023(예측)', '2023(현재)'])]

    # Pivot 테이블 생성
    pivot_df = filtered_df.pivot_table(index=['팀명', 'year'], values='순위').reset_index()

    fig = px.line(pivot_df, x='year', y='순위', color='팀명', labels={'year': '연도', '순위': '순위'},
                  title='2023 예측 vs 현재 팀별 순위 변화',
                  color_discrete_map=team_colors)

    # x축 범위
    fig.update_xaxes(type='category')

    # y축 눈금
    fig.update_layout(yaxis=dict(tickmode='array', tickvals=list(range(1, 11)), ticktext=list(range(1, 11))))
    fig.update_yaxes(autorange="reversed")

    # 마우스를 갖다대면 해당 팀명을 표시
    fig.update_traces(mode='lines+markers')
    
    # 제목 없애기
    fig.update_layout(title="")
    
    # 범례 표시 설정
    fig.update_layout(showlegend=True)

    #그래프 html로 저장
    fig.write_html(file_path)
    
    return file_path



#팀 기록 - 방사형 그래프
def plot_team(team, year):
    en_team_name = team_eng[team]
    
    path = '/workspace/GrandSlam/static/team_plot/' + en_team_name + '/'
    files = os.listdir(path)

    file_path = "static/team_plot/" + en_team_name + "/" + team + "_" + str(year) + ".html"
    file_name = team + "_" + str(year) + ".html"
    
    #이미 저장된 그래프인 경우 바로 반환
    if file_name in files:
        return file_path
    
    print("새로 그리는 중")
    
    new = team_df[['year','팀명','AVG_x','WPCT','OPS','ERA','SV','WHIP']]
    new['1/ERA'] = new['ERA'].apply(lambda x: 1/x)
    new['1/WHIP'] = new['WHIP'].apply(lambda x: 1/x)
    final = new[['AVG_x','WPCT','OPS','SV','1/ERA','1/WHIP']]
    
    scaler = MinMaxScaler()
    k = scaler.fit_transform(final)
    
    # 카테고리와 해당 값들 추출
    categories = final.columns
    values = k[list(new[(new.팀명==team)& (new.year==year)].index)[0]]

    
    # 선택한 년도의 10개 팀의 평균 기록 계산 및 스케일링
    avg_values = scaler.transform(final[new['year']==year].mean().values.reshape(1, -1))[0]

    fig = go.Figure()

    # 선택한 팀의 데이터를 방사형 그래프에 추가
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name=team,
        line=dict(color=team_colors.get(team, 'gray'))
    ))

    # 선택한 년도의 10개 팀의 평균 기록을 방사형 그래프에 추가
    fig.add_trace(go.Scatterpolar(
        r=avg_values,
        theta=categories,
        fill='toself',
        name='평균',
        line=dict(dash='dash', color='yellow')
    ))

    #그래프 html로 저장
    fig.write_html(file_path)
    
    return file_path
    
    
#팀 - 승률 변화 그래프
def plot_team_flow(team):
    en_team_name = team_eng[team]
    
    path = '/workspace/GrandSlam/static/team_plot/' + en_team_name + '/'
    files = os.listdir(path)

    new_path = path
    file_path = "static/team_plot/" + en_team_name + "/" + team + ".html"
    file_name = team + ".html"
    
    #이미 저장된 그래프인 경우 바로 반환
    if file_name in files:
        return file_path
    
    pick_team = team_df[team_df.팀명==team]
    final_df = pick_team[['year','WPCT']]

    # 팀별로 다른 색상과 굵기를 설정하여 선 그래프 그리기
    fig = px.line(final_df, x='year', y='WPCT')

    # 팀에 대응하는 색상 가져오기
    line_color = team_colors.get(team, "gray")  # 디폴트 색상은 회색

    # 그래프 선 색상 설정
    fig.update_traces(line=dict(color=line_color))

    # x축 레이아웃 조정
    fig.update_xaxes(
        tickvals=final_df.year,  # 표시할 x축 값 설정
        ticktext=final_df.year,  # 각 값에 대응하는 텍스트 설정
    )

    # 제목 없애기
    fig.update_layout(title="")
    
    # 범례를 숨김
    fig.update_layout(showlegend=False)   
    
    #그래프 html로 저장
    fig.write_html(file_path)
    
    return file_path


#선수 기록 - 투수 그래프
def plot_pitcher(team, name, year):
    df = pitcher_df[pitcher_df['이닝'] > 43]
    df.loc[:,['ERA', 'FIP', 'WHIP']] = df.loc[:,['ERA', 'FIP', 'WHIP']]*(-1)
    
    try:
        values = list(df[(df.이름==name)& (df.연도==year)].index)[0]
    except:
        print(f"Player '{name}' not found in the dataset.")
        return -1
    
    #이미 그려진 그래프인지 확인
    en_team_name = team_eng[team]
    
    path = '/workspace/GrandSlam/static/player_plot/' + en_team_name + '/pitcher/'
    files = os.listdir(path)

    file_path = "static/player_plot/" + en_team_name + "/pitcher/" + team + "_" + name + "_" + str(year) + ".html"
    file_name = team + "_" + name + "_" + str(year) + ".html"
    
    #이미 저장된 그래프인 경우 바로 반환
    if file_name in files:
        return file_path
    
    print("새로 그리는 중")
    
    
    scaler = MinMaxScaler()
    new_df = df.iloc[:,3:]
    new_df[:] = scaler.fit_transform(df.iloc[:,3:])
    try:
        data = new_df.iloc[values,:]
    except:
        print(f"Player '{name}' not found in the dataset.")
        return -1

    fig = px.line_polar(r=data, theta=pitcher_df.columns[3:], line_close=True, range_r=[0,1])
    fig.update_traces(fill='toself')
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True),
        ),
        showlegend=False
    )
    
    #그래프 html로 저장
    fig.write_html(file_path)

    
#선수 기록 - 공격 그래프
def plot_hitter(team, name, year):
    hitter_df['연도'] = hitter_df['연도'].apply(lambda x: int('20'+str(x)))
    df = hitter_df
    df.loc[:,'병살율'] = df.loc[:,'병살율']*(-1)
    
    try:
        values = list(df[(df.이름==name)& (df.연도==year)].index)[0]
    except:
        print(f"Player '{name}' not found in the dataset.")
        return -1
    
    
    #이미 그려진 그래프인지 확인
    en_team_name = team_eng[team]
    
    path = '/workspace/GrandSlam/static/player_plot/' + en_team_name + '/hitter/'
    files = os.listdir(path)

    file_path = "static/player_plot/" + en_team_name + "/hitter/" + team + "_" + name + "_" + str(year) + ".html"
    file_name = team + "_" + name + "_" + str(year) + ".html"
    
    #이미 저장된 그래프인 경우 바로 반환
    if file_name in files:
        return file_path
    
    

    scaler = MinMaxScaler()
    new_df = df.iloc[:,4:]
    new_df[:] = scaler.fit_transform(df.iloc[:,4:])
    data = new_df.iloc[values,:]

    fig = px.line_polar(r=data, theta=hitter_df.columns[4:], line_close=True, range_r=[0,1])
    fig.update_traces(fill='toself')
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True),
        ),
        showlegend=False
    )
    
    #그래프 html로 저장
    fig.write_html(file_path)
    

#선수 기록 - 수비 그래프
def plot_defense(team, name, year):  #포수, 외야수, 나머지
    try:
        value = list(defense_df[(defense_df.이름==name)& (defense_df.연도==year)].index)[0]
    except:
        print(f"Player '{name}' not found in the dataset.")
        return -1
    
    
    #이미 그려진 그래프인지 확인
    en_team_name = team_eng[team]
    
    path = '/workspace/GrandSlam/static/player_plot/' + en_team_name + '/defense/'
    files = os.listdir(path)

    file_path = "static/player_plot/" + en_team_name + "/defense/" + team + "_" + name + "_" + str(year) + ".html"
    file_name = team + "_" + name + "_" + str(year) + ".html"
    
    #이미 저장된 그래프인 경우 바로 반환
    if file_name in files:
        return file_path
    
    position = defense_df.loc[value, '포지션']
    
    if position == 'C':
        cols = range(4,12)
    elif (position == 'LF')|(position == 'RF')|(position == 'CF'):
        cols = [4,5,6,7,8,9,-1]
    else:
        cols = range(4,10)
    
    df = defense_df.iloc[:,cols]
    scaler = MinMaxScaler()
    new_df = df
    new_df[:] = scaler.fit_transform(df)
    data = new_df.iloc[value,:]

    fig = px.line_polar(r=data, theta=df.columns, line_close=True, range_r=[0,1])
    fig.update_traces(fill='toself')

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True),
        ),
        showlegend=False
    )

    #그래프 html로 저장
    fig.write_html(file_path)


''' 페이지 라우팅 '''

@application.route("/")
def index():
    game = getTodayMatch()
    game_cnt = len(game)
    if game_cnt < 5:
        width_size = game_cnt
    else:
        width_size = 5

    team_rank = getTeamRanking()

    return render_template("index.html", game_cnt=game_cnt, width_size=width_size, match_list=game, rank=team_rank)


#일정/결과 페이지
@application.route("/match", methods=['GET','POST'])
def match():
    date = today - timedelta(1)
    year = date.year; month = date.month; day=date.day; #어제
    
    #경기 정보 가져오기
    game = getPrevMatch(year, month, day)
    game_cnt = len(game) #경기 개수
    
    if request.method == 'POST':
        button_type = request.form.get('button_type')  # 버튼 타입 가져오기
        now_date = request.form.get('now_date')  # 날짜 정보 가져오기
        now_date = datetime.strptime(now_date.split(" ")[0], '%Y-%m-%d')
        
        #전날로 이동
        if button_type == 'prev':
            date = now_date - timedelta(1);
        #다음날로 이동
        elif button_type == 'next':
            date = now_date + timedelta(1);

        year = date.year; month = date.month; day=date.day; #새로운 날짜
        #print("새로운 날짜: {0}년 {1}월 {2}일".format(year, month, day))
        #경기 정보 가져오기
        game = getPrevMatch(year, month, day)
        game_cnt = len(game) #경기 개수

        return render_template("match.html", today=today, date=date, game_cnt=game_cnt, match_list=game)
    
    return render_template("match.html", today=today, date=date, game_cnt=game_cnt, match_list=game)

    

#순위 페이지
@application.route("/ranking")
def ranking():
    delTeamRankingPlot() #팀 순위 그래프 삭제
    
    df_rank_final = getRankingDF()
    plot1_path = plot_team_ranking_1(df_rank_final)
    plot2_path = plot_team_ranking_2(df_rank_final)
    plot3_path = plot_team_ranking_3(df_rank_final)
    return render_template("ranking.html", plot1_path=plot1_path, plot2_path=plot2_path, plot3_path=plot3_path)


''' 팀 기록 페이지 '''
#팀 기록 - 팀 선택 페이지
@application.route("/team_select", methods=['GET','POST'])
def team_select():
    if request.method == 'POST':
        selected_team = request.form.get('team')
        session['selected_team'] = selected_team
        return redirect("team_page")
    return render_template("team_select.html")

#팀 기록 - 팀 페이지
@application.route("/team_page", methods=['GET','POST'])
def team_page():
    #팀 선택을 완료했는지 확인
    selected_team = session.get('selected_team')
    if selected_team == None:
        return render_template("team_page.html", team=selected_team)
    
    selected_team_info = team_info[team_info['team'] == selected_team].values[0]
    team_plot_path = plot_team_flow(selected_team)
    
    my_team = 0
    #로그인이 되어있는 경우
    if session.get('UserId'):
        my_team_list = DB.get_my_team_by_user(session['UserId'])
        if selected_team in my_team_list:
            print("My Team에 있음")
            my_team = 1
    
    selected_year = request.args.get('selected_year')  # 넘어온 selected_year 값을 받아옴

    if selected_year:
        team_year_plot_path = plot_team(selected_team, int(selected_year))
    else:
        selected_year = "2022"
        team_year_plot_path = plot_team(selected_team, 2022)  # default
    return render_template("team_page.html", team=selected_team,  year=selected_year, team_info=selected_team_info, my_team=my_team, team_plot_path=team_plot_path, team_year_plot_path=team_year_plot_path)


@application.route("/team_year_record", methods=['GET','POST'])
def team_year_record():
    selected_team = session.get('selected_team')
    selected_year = request.form.get('year')
    return redirect(url_for("team_page", selected_year=selected_year))


''' 선수 기록 페이지 '''

#선수 기록 - 팀 선택 페이지
@application.route("/player_team_select", methods=['GET','POST'])
def player_team_select():
    if request.method == 'POST':
        selected_team = request.form.get('team')
        session['selected_team'] = selected_team
        return redirect("player_select")
    return render_template("player_team_select.html")

#선수 기록 - 선수 선택 페이지
@application.route("/player_select", methods=['GET','POST'])
def player_select():
    selected_team = session.get('selected_team')
    team_player = player_df[player_df['team'] == selected_team].values
    
    if request.method == 'POST':
        selected_player = request.form.get('player')
        session['selected_player'] = selected_player
        return redirect("player_page")
    return render_template("player_select.html", team=selected_team, team_player=team_player)


#선수 기록 - 선수 페이지
@application.route("/player_page", methods=['GET','POST'])
def player_page():
    #선수 선택을 완료했는지 확인
    selected_team = session.get('selected_team')
    selected_player = session.get('selected_player')
    
    if selected_player == None:
        return render_template("player_page.html", player=selected_player)
    
    selected_team_info = team_info[team_info['team'] == selected_team].values[0]
    selected_player_info = player_df[(player_df['team'] == selected_team) & (player_df['number'] == selected_player)].values[0]
    selected_player_name = selected_player_info[0].strip()
    
    my_player = 0
    #로그인이 되어있는 경우
    if session.get('UserId'):
        my_player_list = DB.get_my_player_by_user(session['UserId'])
        selected_team_player = [selected_team, selected_player]
        
        if selected_team_player in my_player_list:
            print("My Player에 있음")
            my_player = 1
    
    selected_year = request.args.get('selected_year')  # 넘어온 selected_year 값을 받아옴
    selected_position = request.args.get('selected_position') 
    
    
    player_plot = 0
    if (not selected_year) | (not selected_position):
        return render_template("player_page.html", team=selected_team, team_info=selected_team_info, player=selected_player, player_info=selected_player_info, my_player=my_player, player_plot=player_plot)
    
    if selected_position == '투수':
        player_plot_path = plot_pitcher(selected_team, selected_player_name, int(selected_year))
        if player_plot_path == -1:
            player_plot = -1
        else:
            player_plot = 1

    elif selected_position == '공격':
        player_plot_path = plot_hitter(selected_team, selected_player_name, int(selected_year))
        if player_plot_path == -1:
            player_plot = -1
        else:
            player_plot = 2
        
    
    elif selected_position == '수비':
        player_plot_path = plot_defense(selected_team, selected_player_name, int(selected_year))
        if player_plot_path == -1:
            player_plot = -1
        else:
            player_plot = 3
    
    return render_template("player_page.html", team=selected_team, year=selected_year, team_info=selected_team_info, player=selected_player, player_info=selected_player_info, my_player=my_player, player_plot=player_plot, player_plot_path=player_plot_path)

@application.route("/player_year_position_record", methods=['GET','POST'])
def player_year_position_record():
    selected_team = session.get('selected_team')
    selected_player = session.get('selected_player')
    selected_year = request.form.get('year')
    selected_position = request.form.get('position')
    return redirect(url_for("player_page", selected_year=selected_year, selected_position=selected_position))


''' DB 연동'''
#MyTeam 설정
@application.route("/submit_my_team", methods=['POST'])	
def submit_my_team():	
    if request.method == 'POST':
        userId = session.get('UserId')
        selected_team = session.get('selected_team')
        my_team_state = request.form.get('like')
        print("현재 팀 상태: " + str(my_team_state))
        
        if my_team_state == "0":
            print(selected_team + " My Team 취소")
        else:
            print(selected_team + " My Team 설정")
        
        DB.change_my_team(userId, selected_team, my_team_state)
        print("상태 바꿈")
        return redirect('team_page')

#MyPlayer 설정
@application.route("/submit_my_player", methods=['POST'])	
def submit_my_player():	
    if request.method == 'POST':
        userId = session.get('UserId')
        selected_team = session.get('selected_team')
        selected_player = session.get('selected_player')
        
        
        selected_team_player = [selected_team, selected_player]
        print("selected_player: ")
        print(selected_player)
        
        my_player_state = request.form.get('like')
        print("현재 선수 상태: " + str(my_player_state))
        
        if my_player_state == "0":
            print(selected_player + " My Player 취소")
        else:
            print(selected_player + " My Player 설정")
        
        DB.change_my_player(userId, selected_team_player, my_player_state)
        print("상태 바꿈")
        return redirect('player_page')


#My Page에서 Team Page로 이동
@application.route("/my_team_select", methods=['GET','POST'])
def my_team_select():
    if request.method == 'POST':
        selected_team = request.form.get('team')
        session['selected_team'] = selected_team
        return redirect("team_page")
    return render_template("team_select.html")
    
#My Page에서 Player Page로 이동
@application.route("/my_player_select", methods=['GET','POST'])
def my_player_select():
    if request.method == 'POST':
        selected_team = request.form.get("player_team")
        selected_player = request.form.get('player')
        session['selected_team'] = selected_team
        session['selected_player'] = selected_player
        return redirect("player_page")
    return render_template("player_select.html", team=selected_team, team_player=team_player)

    
    



#로그인 페이지 - 기본
@application.route("/login")
def login():
    return render_template("login.html")

#회원가입 페이지 - 기본
@application.route("/signup")
def signup():
    return render_template("signup.html")

#로그인 페이지 - 입력 후
@application.route("/submit_login", methods=['POST'])	
def submit_login():	
    user_id = request.form.get("id")	
    user_pw = request.form.get("password")	
    user_pw_hash = hashlib.sha256(user_pw.encode('utf-8')).hexdigest()	
    
    if DB.user_login(user_id, user_pw_hash):	
        session['UserId'] = user_id	
        session['my_team'] = DB.get_my_team_by_user(str(user_id))
        session['my_player'] = DB.get_my_player_by_user(str(user_id))
        return redirect(url_for('index'))
    
    elif (user_id and user_pw):	
        flash("아이디나 패스워드를 확인해주세요")	
        return render_template("login.html")
    
#로그아웃
@application.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

#회원가입 페이지 - 입력 후
@application.route("/submit_signup", methods=['POST'])
def submit_signup():
    ID = request.form.get("id")
    password = request.form.get('password')
    check_password = request.form.get('check_password')
    password_hash = hashlib.sha256(password.encode('utf8')).hexdigest()
    
    data = {"UserId": ID,
            "UserPassword": password_hash}
    
    if not (ID and password and check_password) :
        flash("모두 입력해주세요")
    elif (len(password) < 6):
        flash("비밀번호는 6자 이상이어야 합니다")
    elif password != check_password:
        flash("비밀번호를 확인해주세요")
    elif DB.insert_account(ID, data):
        flash("가입 완료되었습니다")
        return render_template("login.html", data=data)
    else: 
        flash("이미 가입된 계정입니다")
    return render_template("signup.html", data=data)

# 탈퇴하기
@application.route("/delete_account")
def delete_user():
    if DB.delete_account(session['UserId']):
        session.clear()
    return redirect(url_for('index'))


#마이페이지	
@application.route("/mypage")	
def mypage():
    if session['UserId'] == None:
        flash("로그인 후 이용가능한 페이지입니다. 로그인하시겠습니까?")
        return render_template("login.html")
    
    #My 팀 불러오기
    my_team_list = DB.get_my_team_by_user(session['UserId'])
    my_team_num = len(my_team_list)
    team_box_height = 1
    team_box_width = my_team_num
    if my_team_num > 5:
        team_box_height = 2
        team_box_width = 5
    
    #My 선수 불러오기
    my_player_list = DB.get_my_player_by_user(session['UserId']) #[[팀1, 번호1], [팀2, 번호2]]
    my_player_num = len(my_player_list)
    player_box_height = 1
    player_box_width = my_player_num
    if my_player_num > 5:
        player_box_height = int(my_player_num / 5) + 1
        player_box_width = 5
    
    my_player_detail_list = []
    
    for i in range(my_player_num):
        player_detail = player_df[(player_df['team'] == my_player_list[i][0]) & (player_df['number'] == my_player_list[i][1])].values[0]
        my_player_detail_list.append(player_detail)
    
    return render_template("mypage.html", my_team_list=my_team_list, my_player_list=my_player_detail_list, my_team_num=my_team_num, my_player_num=my_player_num, team_box_height=team_box_height, team_box_width=team_box_width, player_box_height=player_box_height, player_box_width=player_box_width)


if __name__ == "__main__":
    application.run(host='0.0.0.0', debug=True)

    
# 브라우저 종료
driver.quit()

