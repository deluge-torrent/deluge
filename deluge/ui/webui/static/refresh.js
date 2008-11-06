/*
(c) Martijn Voncken mvoncken@gmail.com
License : GPLv3

quick and dirty auto-refresh timer.
Our users have waited too long for a new auto-refresh.
I need to get things done (even if it's not pretty). ;with the least dependencies for a backport to 1.05
*/
var seconds=0;
var refresh_secs = 10;
var prc = 0;
var timer_active = 0;
function continue_timer(){
    if (!timer_active) {
        return;
    }
    seconds+=0.1;
    if (seconds > refresh_secs){
        timer_active = 0;
        do_refresh();
     }
     prc = ((seconds / refresh_secs) * 100 );
     el("timer_bar").style.width = prc + "%";
     setTimeout("continue_timer()",100)
}

function do_refresh(){
   location.reload(true);
}

function start_timer(){
    timer_active = 1;
    continue_timer();
    el("timer_pause").style.display = "none";
    el("timer_start").style.display = "inline";
    el("timer_outer").title = "Auto refresh:Active; click here to pause";
    setCookie('auto_refresh',"1");
}
function stop_timer(){
    timer_active = 0;
    el("timer_pause").style.display = "inline";
    el("timer_start").style.display = "none";
    el("timer_outer").title = "Auto refresh:Paused; click here to start";
    setCookie('auto_refresh',"0");
}


function toggle_timer() {
    if (timer_active) {
        stop_timer();
    }
    else {
        start_timer();
    }
}

