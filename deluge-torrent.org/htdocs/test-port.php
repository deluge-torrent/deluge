<?php
error_reporting(0);
$host = $_SERVER['REMOTE_ADDR'];
if (is_numeric($_GET['port'])){
$i = $_GET['port'];
$fp = fsockopen("$host",$i,$errno,$errstr,10);
if($fp){
echo "TCP port " . $i . " open on " . $host . "<br><br>Yay! :-)";
fclose($fp);
}
else{
echo "TCP port " . $i . " closed on " . $host . "\n";
}
flush();
}
?> 

