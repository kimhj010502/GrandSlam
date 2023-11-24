//팀 클릭
function click_my_team(team){
    var my_team = document.getElementById("team");
    
    my_team.value = team;
    
    console.log(my_team.value);
}


//선수 팀 클릭
function click_my_player(player_team, player){
    var my_player_team = document.getElementById("player_team");
    var my_player = document.getElementById("player");
    
    my_player_team.value = player_team;
    my_player.value = player;
    
    console.log(my_player_team.value);
    console.log(my_player.value);
}