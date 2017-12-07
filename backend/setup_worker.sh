# ===================
# Quicker boot:
# sudo vim /boot/grub/grub.cfg
#   find and replace
#       set timeout=2
#   with
#       set timeout=2
# ===================
cd ~/
git clone -b master http://gitlab.dev.ivi.ru/tlansen/trix.git
sudo cp trix/nvenc_sdk_include/* /usr/include/

sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup
sudo sed -i '/#deb-src/s/^#//g' /etc/apt/sources.list

sudo cp trix/sources.list /etc/apt/
sudo apt-get update
# ===================
# CIFS support (needed for hostname resolving)
# ===================
sudo apt-get install cifs-utils
# ===================
# SSHFS support
# ===================
sudo apt-get install sshfs

# uncomment 'user_allow_other'
sudo sed -i '/user_allow_other/s/^#//g' /etc/fuse.conf

# ===================
# Python: psycopg2, Unidecode, python_slugify
# ===================
sudo apt-get install -y python3-pip
sudo python3.5 -m pip install --upgrade pip
sudo python3.5 -m pip install psycopg2
sudo python3.5 -m pip install Unidecode
sudo python3.5 -m pip install python_slugify
sudo python3.5 -m pip install psutil
# content.7.txt
# ===================
# NVIDIA CUDA 9.0
# ===================
wget http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/cuda-repo-ubuntu1604_9.0.176-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu1604_9.0.176-1_amd64.deb
sudo apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/7fa2af80.pub
sudo apt-get update
sudo apt-get install cuda-9-0
# ffmpeg + nvenc
sudo apt-get build-dep libav
sudo apt-get install -y libfdk-aac-dev libopencv-dev libopenjp2-7-dev
git clone https://git.ffmpeg.org/ffmpeg.git
mkdir ffmpeg_build
cd ffmpeg_build
../ffmpeg/configure --extra-version=ivi.ru --disable-debug\
 --enable-nonfree --enable-libopenjpeg --enable-libwavpack --enable-libx265 --enable-libopencore-amrwb --enable-libvorbis --enable-libpulse --enable-libtwolame --enable-gnutls --enable-zlib\
 --enable-iconv --enable-bzlib --enable-avisynth --enable-fontconfig --enable-libmp3lame --enable-libxvid --enable-libwebp --enable-libtheora --enable-libcdio --enable-version3 --enable-libbluray --enable-libgsm\
 --enable-nvenc --enable-libopencore-amrnb --enable-swscale --enable-libopencv --enable-libvo-amrwbenc --cpu=native --enable-libopus --enable-libdc1394 --enable-libvpx --enable-librtmp --enable-gpl\
 --enable-libx264 --enable-libsnappy --enable-cuvid --enable-libcaca --enable-libfdk-aac --enable-libspeex --enable-pthreads --enable-libfreetype --enable-libgme --enable-libsoxr --enable-vaapi --enable-libbs2b\
 --enable-lzma --enable-cuda --enable-libmodplug --enable-vdpau --enable-libass --enable-frei0r
make
sudo make install
# ===================
# Tools
# ===================
#sudo apt-get install -y ffmpeg
sudo apt-get install -y mediainfo
sudo apt-get install -y sox
sudo apt-get install gpac

cd ~/
sudo apt-get install -y autoconf autogen
wget http://www.nasm.us/pub/nasm/releasebuilds/2.13.01/nasm-2.13.01.tar.bz2
tar xjvf nasm-2.13.01.tar.bz2
cd nasm-2.13.01
./autogen.sh
./configure
make
sudo make install

# ===================
# x265
# ===================

cd ~/
hg clone https://bitbucket.org/multicoreware/x265
cd x265/build/linux

cmake -G "Unix Makefiles" -D NATIVE_BUILD=ON -D STATIC_LINK_CRT=ON -D ENABLE_SHARED=OFF HIGH_BIT_DEPTH=OFF ../../source
make
sudo mv x265 /usr/local/bin/x265.08

cmake -G "Unix Makefiles" -D NATIVE_BUILD=ON -D STATIC_LINK_CRT=ON -D ENABLE_SHARED=OFF HIGH_BIT_DEPTH=ON MAIN12=OFF ../../source
make
sudo mv x265 /usr/local/bin/x265.10

cmake -G "Unix Makefiles" -D NATIVE_BUILD=ON -D STATIC_LINK_CRT=ON -D ENABLE_SHARED=OFF HIGH_BIT_DEPTH=ON MAIN12=ON ../../source
make
sudo mv x265 /usr/local/bin/x265.12

#./make-Makefiles.bash
# NATIVE_BUILD=ON
# STATIC_LINK_CRT=ON
# ENABLE_SHARED=OFF
#make
#sudo mv x265 /usr/local/bin/x265.08
#./make-Makefiles.bash
# HIGH_BIT_DEPTH=ON
#make
#sudo mv x265 /usr/local/bin/x265.10
#./make-Makefiles.bash
# MAIN12=ON
#make
#sudo mv x265 /usr/local/bin/x265.12

# ===================
# x264
# ===================

cd ~/
git clone http://git.videolan.org/git/x264.git
cd x264/
./configure --disable-interlaced --bit-depth=8 --disable-avs --disable-swscale --disable-lavf --disable-ffms --disable-gpac --disable-lsmash
make
sudo mv x264 /usr/local/bin/x264.08
./configure --disable-interlaced --bit-depth=10 --disable-avs --disable-swscale --disable-lavf --disable-ffms --disable-gpac --disable-lsmash
make
sudo mv x264 /usr/local/bin/x264.10

# ===================
# cleanup
# ===================
cd ~/
rm nasm-2.13.01.tar.bz2
rm -rf nasm-2.13.01 x264  x265

# ===================
# conform code to Python 3.5
# ===================
sudo mkdir -p /www/trix/bin/backend
sudo python3.5 ~/trix/backend/conform_to_python3.5.py /www/trix/bin/backend


