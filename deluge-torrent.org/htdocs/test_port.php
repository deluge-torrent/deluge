<?php
error_reporting(0);
$host = $_SERVER['REMOTE_ADDR'];
if (is_numeric($_GET['port'])){
$i = $_GET['port'];
$fp = fsockopen("$host",$i,$errno,$errstr,5);
if($fp){
echo 1;
fclose($fp);
}
else{
echo 0;
}
flush();
}
?> 

