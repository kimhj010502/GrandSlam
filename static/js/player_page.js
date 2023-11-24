// Flask에서 세션 값 확인
var playerName = document.getElementById("player_name").textContent;

// 세션 값이 없는 경우 알람 띄우고 페이지 이동
if (playerName == 'None') {
    alert("팀과 선수를 선택하세요.");
    window.location.href = "/player_select"; // 이동할 페이지의 URL로 수정
}


var player_plot = document.getElementById('player_plot').textContent;
console.log(player_plot);

if (player_plot == '-1') {
    alert("해당 연도, 포지션에 선수의 데이터가 없습니다. 다시 선택해주세요.")
    window.location.href = "/player_page"; // 이동할 페이지의 URL로 수정

}


function validateForm() {
    var yearSelect = document.getElementsByName("year")[0]; // 연도 선택 요소
    var positionSelect = document.getElementsByName("position")[0]; // 포지션 선택 요소

    if (yearSelect.value == "none" || positionSelect.value == "none") {
        alert("연도와 포지션을 선택하세요."); // 경고 메시지
        return false; // 폼 서밋을 취소하고 페이지 이동을 막음
    }
}



function click_my_player(){
    var my_player_img = document.getElementById("my_player");
    var my_player_state = document.getElementById("like");
    
    my_player_state.value = my_player_img.value;
    
    console.log(my_player_state.value);
    
    if (my_player_img.value == "1") {
        my_player_img.src = "/static/img/unlike.png";
        my_player_img.value = "0";
        my_player_state.value = "0";
    }
    else {
        my_player_img.src = "/static/img/like.png";
        my_player_img.value = "1";
        my_player_state.value = "1";
    }
}

//MyPlayer 실패
function fail_my_player(){
    event.preventDefault();
    
    var result = confirm("My 선수 설정 기능은 로그인 후 이용가능합니다. 로그인하시겠습니까?");
        
    if(result) {
        window.location.href='/login';
    }
    else {
        window.location.href='/player_page';
    } 
}
