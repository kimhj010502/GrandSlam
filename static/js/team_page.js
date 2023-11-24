// Flask에서 세션 값 확인
var teamName = document.getElementById("team_name").textContent;

// 세션 값이 없는 경우 알람 띄우고 페이지 이동
if (teamName == 'None') {
    alert("팀을 선택하세요.");
    window.location.href = "/team_select"; // 이동할 페이지의 URL로 수정
}


function validateForm() {
    var yearSelect = document.getElementsByName("year")[0]; // 팀 선택 요소

    if (yearSelect.value == "none") {
        alert("연도를 선택하세요."); // 경고 메시지
        return false; // 폼 서밋을 취소하고 페이지 이동을 막음
    }
}



function click_my_team(){
    var my_team_img = document.getElementById("my_team");
    var my_team_state = document.getElementById("like");
    
    my_team_state.value = my_team_img.value;
    
    console.log(my_team_state.value);
    
    if (my_team_img.value == "1") {
        my_team_img.src = "/static/img/unlike.png";
        my_team_img.value = "0";
        my_team_state.value = "0";
    }
    else {
        my_team_img.src = "/static/img/like.png";
        my_team_img.value = "1";
        my_team_state.value = "1";
    }
}

//MyTeam 실패
function fail_my_team(){
    event.preventDefault();
    
    var result = confirm("My 팀 설정 기능은 로그인 후 이용가능합니다. 로그인하시겠습니까?");
        
    if(result) {
        window.location.href='/login';
    }
    else {
        window.location.href='/team_page';
    } 
}
