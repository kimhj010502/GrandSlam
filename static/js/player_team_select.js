function validateForm() {
    var teamSelect = document.getElementsByName("team")[0]; // 팀 선택 요소

    if (teamSelect.value === "none" || yearSelect.value === "none") {
        alert("팀을 선택하세요."); // 경고 메시지
        return false; // 폼 서밋을 취소하고 페이지 이동을 막음
    }
}


// 이미지 클릭 시의 동작 설정
$(".team").click(function() {
    // 선택한 팀의 요소 가져오기
    var teamName = $(this).find("label").data("team");

    // 클릭한 팀의 라디오 버튼을 선택하도록 설정
    $(this).siblings("input[type=radio]").prop("checked", true);
    
    // 폼을 자동으로 제출
    $("#teamForm").submit();
});