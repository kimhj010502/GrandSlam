function fail_mypage(){
    var result = confirm("로그인 후 이용가능한 페이지입니다. 로그인하시겠습니까?");
        
    if(result)
    {
        location.href='/login';
    }
    else
    {
        location.href='/index';
    }
}