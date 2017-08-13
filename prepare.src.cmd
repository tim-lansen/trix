@echo off
setlocal enabledelayedexpansion

set "src_AV=%~1"
set "src_A=%~2"
set "tmp=C:\temp"
set "lstv=!tmp!\lstv.lst"
set "lsta=!tmp!\lsta.lst"
del "!lstv!"
del "!lsta!"
set "dst=%~3"

set "params=-pix_fmt yuv420p -vf fps=25/1,scale=960:400,pad=1024:768:32:184 -c:v libx264 -b:v 5000k -preset veryslow -aspect 1024:768 -g 125 -refs 3"


::ffmpeg -y -loglevel error -stats -f lavfi -i color=color=black:duration=30 !params! "!tmp!\part0.0.h264"
::ffmpeg -y -loglevel error -stats -f lavfi -i smptebars=duration=10         !params! "!tmp!\part0.1.h264"
::ffmpeg -y -loglevel error -stats -f lavfi -i color=color=black:duration=10 !params! "!tmp!\part0.2.h264"
echo file part0.0.h264 >>"!lstv!"
echo file part0.1.h264 >>"!lstv!"
echo file part0.2.h264 >>"!lstv!"
ffmpeg -y -loglevel error -stats -f lavfi -i "anullsrc=channel_layout=stereo:sample_rate=48000" -t 30  -c:a pcm_s16le "!tmp!\part0.0.wav"
ffmpeg -y -loglevel error -stats -f lavfi -i "sine=frequency=1000:sample_rate=48000:duration=10" -ac 2 -c:a pcm_s16le "!tmp!\part0.1.wav"
ffmpeg -y -loglevel error -stats -f lavfi -i "anullsrc=channel_layout=stereo:sample_rate=48000" -t 10  -c:a pcm_s16le "!tmp!\part0.2.wav"
echo file part0.0.wav >>"!lsta!"
echo file part0.1.wav >>"!lsta!"
echo file part0.2.wav >>"!lsta!"

::ffmpeg -y -loglevel error -stats               -i "!src_AV!" -map v -t 120 !params! "!tmp!\part1.0.h264"
::ffmpeg -y -loglevel error -stats -ss 1:14:00.0 -i "!src_AV!" -map v -t 300 !params! "!tmp!\part1.1.h264"
::ffmpeg -y -loglevel error -stats -ss 1:46:00.0 -i "!src_AV!" -map v        !params! "!tmp!\part1.2.h264"
echo file part1.0.h264 >>"!lstv!"
echo file part1.1.h264 >>"!lstv!"
echo file part1.2.h264 >>"!lstv!"
ffmpeg -y -loglevel error               -i "!src_AV!" -map a -t 120 -c:a pcm_s16le -r 48k "!tmp!\part1.0.wav"
ffmpeg -y -loglevel error -ss 1:14:00.0 -i "!src_AV!" -map a -t 300 -c:a pcm_s16le -r 48k "!tmp!\part1.1.wav"
ffmpeg -y -loglevel error -ss 1:46:00.0 -i "!src_AV!" -map a        -c:a pcm_s16le -r 48k "!tmp!\part1.2.wav"
echo file part1.0.wav >>"!lsta!"
echo file part1.1.wav >>"!lsta!"
echo file part1.2.wav >>"!lsta!"

::ffmpeg -y -loglevel error -stats -f lavfi -i color=color=black -t 30 !params! "!tmp!\part2.0.h264"
::ffmpeg -y -loglevel error -stats -ss 1:02:00.0 -i "!src_AV!" -map v -t 15 !params!    "!tmp!\part2.1.h264"
::ffmpeg -y -loglevel error -stats -f lavfi -i color=color=black -t 10 !params! "!tmp!\part2.2.h264"
::ffmpeg -y -loglevel error -stats -ss 1:04:00.0 -i "!src_AV!" -map v -t 15 !params!    "!tmp!\part2.3.h264"
::ffmpeg -y -loglevel error -stats -f lavfi -i color=color=black -t 10 !params! "!tmp!\part2.4.h264"
echo file part2.0.h264 >>"!lstv!"
echo file part2.1.h264 >>"!lstv!"
echo file part2.2.h264 >>"!lstv!"
echo file part2.3.h264 >>"!lstv!"
echo file part2.4.h264 >>"!lstv!"
ffmpeg -y -loglevel error -f lavfi -i "anullsrc=channel_layout=stereo:sample_rate=48000" -t 80  -c:a pcm_s16le "!tmp!\part2.all.wav"
echo file part2.all.wav >>"!lsta!"

cd /d "!tmp!"
ffmpeg -loglevel error -stats -y -f concat -i "!lsta!" -c copy audio.wav
::ffmpeg -loglevel error -stats -y           -i audio.wav -c aac -strict -2 -b:a 320k audio.mp4
ffmpeg -loglevel error -stats -y -f concat -i "!lstv!" -i audio.mp4 -c copy -metadata:s:a:0 language=rus "!dst!"

endlocal
