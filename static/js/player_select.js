// Flask에서 세션 값 확인
var teamName = document.getElementById("team_name").textContent;

console.log(teamName);

// 세션 값이 없는 경우 알람 띄우고 페이지 이동
if (teamName == 'None') {
    alert("팀을 선택하세요.");
    window.location.href = "/player_team_select"; // 이동할 페이지의 URL로 수정
}



// 이미지 클릭 시의 동작 설정
$(".player").click(function() {
    // 선택한 선수의 요소 가져오기
    var playerNum = $(this).find("label").data("player");

    // 클릭한 선수의 라디오 버튼을 선택하도록 설정
    $(this).siblings("input[type=radio]").prop("checked", true);
    
    // 폼을 자동으로 제출
    $("#playerForm").submit();
});