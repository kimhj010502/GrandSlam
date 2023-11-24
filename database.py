#DB 연결
import pyrebase
import json

class DBhandler:
    def __init__(self):
        with open('authentication/firebase_auth.json') as f:
            config=json.load(f )
        firebase = pyrebase.initialize_app(config)
        self.db = firebase.database()
        
    #회원가입 - 계정 생성
    def insert_account(self, ID, data):	
        #저장할 데이터 생성	
        account_info = {	
            "UserId": data['UserId'],	
            "UserPassword": data['UserPassword'],	
            "my_team": [],
            "my_player": []
        }	
        
        if self.account_duplicate_check(ID):	
            self.db.child("account").child(ID).set(account_info)	
            return True	
        else:	
            return False
    
    #회원가입 - 계정 중복체크용 함수 (아이디가 등록되어 있으면 False)
    def account_duplicate_check(self, name):
        accounts = self.db.child("account").get()

        if accounts.each() == None:
            return True
        
        for acc in accounts.each():
            if acc.key() == name:
                return False
        return True
    
    #로그인
    def user_login(self, ID, PW):
        accounts = self.db.child("account").get()
        target_value = []
        for acc in accounts.each():
            value = acc.val()
            if value['UserId'] == ID and value['UserPassword'] == PW:
                return True
        return False
        
    #회원 탈퇴
    def delete_account(self, ID):
        self.db.child("account").child(ID).remove()
        return True
    
    #My Team 가져오기	
    def get_my_team_by_user(self, userId):	
        my_team_list = self.db.child("account").child(userId).child("my_team").get().val()	
        if my_team_list == None:
            return []
        return my_team_list	
    
    #My Player 가져오기	
    def get_my_player_by_user(self, userId):	
        my_player_list = self.db.child("account").child(userId).child("my_player").get().val()	
        if my_player_list == None:
            return []
        return my_player_list	
    
    
    #My 팀 설정/해제	
    def change_my_team(self, userId, selected_team, my_team_state):	
        my_team_list = self.get_my_team_by_user(userId)	
        
        if my_team_state == "1":	
            if selected_team not in my_team_list:	
                my_team_list.append(selected_team)	
                
        elif my_team_state == "0":	
            if selected_team in my_team_list:	
                my_team_list.remove(selected_team)	
        self.db.child("account").child(userId).update({"my_team": my_team_list})	
        return 
    
    #My 선수 설정/해제	
    def change_my_player(self, userId, selected_team_player, my_player_state):	
        my_player_list = self.get_my_player_by_user(userId)	
        
        if my_player_state == "1":	
            if selected_team_player not in my_player_list:	
                my_player_list.append(selected_team_player)	
                
        elif my_player_state == "0":	
            if selected_team_player in my_player_list:	
                my_player_list.remove(selected_team_player)	
        self.db.child("account").child(userId).update({"my_player": my_player_list})	
        return 