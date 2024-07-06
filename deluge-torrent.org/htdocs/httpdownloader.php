<?php

function test_cookie() {
   header("Content-Type: text/plain");
   setcookie("password", "deluge");
   if (isset($_COOKIE["password"])) {
      if ($_COOKIE["password"] == "deluge") {
         echo "COOKIE MONSTER!";
      } else {
         echo $_COOKIE["password"];
      }
   } else {
      echo "Password cookie not set!";
   }
}

function test_rename() {
   if (isset($_REQUEST["filename"])) {
      $filename = $_REQUEST["filename"];
   } else {
      $filename = "renamed_file";
   }
   header("Content-Type: text/plain");
   header("Content-Disposition: attachment; filename=".$filename);
   echo "This file should be called ".$filename;
}

function test_gzip_decoding() {
   $msg = (isset($_REQUEST["msg"])) ? $_REQUEST["msg"] : "EFFICIENCY!";
   header("Content-Type: text/plain");
   header("Content-Encoding: gzip");
   echo gzencode($msg);
}

function test_redirect() {
   header("HTTP/1.1 307 Temporary Redirect");
   header("Location: http://deluge-torrent.org");
}

function print_message() {
   header("Content-Type: text/html");
   echo "<html>";
   echo "<head>";
   echo "<title>Testing 123</title>";
   echo "</head>";
   echo "<body>";
   echo "<h1>Nothing to see here</h1>";
   echo "<p>This page is purely for testing purposes<br>";
   echo "<br>Have a nice day :)</p>";
   echo "</body>";
   echo "</html>";
}

$tests = array (
   "cookie" => test_cookie,
   "rename" => test_rename,
   "gzip" => test_gzip_decoding,
   "redirect" => test_redirect
);

if (isset($_SERVER["HTTP_USER_AGENT"]) && strpos($_SERVER["HTTP_USER_AGENT"], "Deluge") !== false) {
   if (isset($_REQUEST["test"])) {
      $test = $_REQUEST["test"];
      if (isset($tests[$test])) {
         $tests[$test]();
      } else {
         header("Content-Type: text/plain");
         echo "Unknown test: ".$test;
      }
   } else {
      header("Content-Type: text/plain");
      echo "Hello ".$_SERVER["HTTP_USER_AGENT"];
   }
} else {
   print_message();
}
?>
