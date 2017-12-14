

execute_and

# ===================
# Quicker boot:
# sudo vim /boot/grub/grub.cfg
#   find and replace
#       set timeout=2
#   with
#       set timeout=2
# ===================

cd ~/
mkdir .ssh
# before start, install RSA key to ~/.ssh/trix_node_rsa

echo '-----BEGIN RSA PRIVATE KEY-----' >.ssh/trix_node_rsa
echo 'MIIEowIBAAKCAQEAofvMFhxoik7MXnNMy5wePysIiKiji7QfTbJeEGOhMc48j2Fr' >>.ssh/trix_node_rsa
echo 'idP8a1l+P4K5XiagP1cwS35Dj9Wf6RWCtOhkCdfaJ/Ta/415U+fAdPuwpEtsGfb1' >>.ssh/trix_node_rsa
echo 'UdGuQwDAHOYNbOuQiT1MCu9dLaEkEGQeMJA5IQuOF2Qp2wIBql+e648cuOvxDNrf' >>.ssh/trix_node_rsa
echo 'N4aWwmRxXF8EXQ/bLHilkWNBpBssneQJnrtXb6Q7QadZ8dQtLbpELMgT5sRCV6uy' >>.ssh/trix_node_rsa
echo 'VXvno53NmiyaEF2dD99O9xRWjYdnBWdbKcsG2LB2MMydDWI6x+7ZLINXe7pcmI03' >>.ssh/trix_node_rsa
echo 'XKjNYOodaNDE4sdC3O7Rga08/pmBQkek6Wzc1wIDAQABAoIBAAjYkmWmuYLMGNcT' >>.ssh/trix_node_rsa
echo 'nt8DsJcsh3PHGd9YP9ljY0Wr2zK4G5CM9m15eTB3m7BmOC9PFrM+1LFavN/O/8Of' >>.ssh/trix_node_rsa
echo '3Bp7EnODKTPDaG5KUJTndBgvYo8mW0nztaP5OnYIRXWOjq8jEiqcgVmbhtAmG60V' >>.ssh/trix_node_rsa
echo 'epyWU7hdRC481xhRvLuMK0ab8yqaCbcUVL+Bs3IlQkSfrVh4k8DqCDT/xQGhjOE1' >>.ssh/trix_node_rsa
echo 'Wu8GbakYWzdEQFHkb/rXm4gVoCboANxmf2d7NY6VkM8xjRF6GU25F754yS5n3+Cp' >>.ssh/trix_node_rsa
echo 'tGaK+yyh3CciWcVDrGbHU5NDIo3rrY3MHQ3SjInkV8PqG0+9Vg7Gk4VIzTvFLGIJ' >>.ssh/trix_node_rsa
echo 'mI0dL7kCgYEA02z+oFcNhxo9HKGGAZ+8mdG5lfW3Ely1avRnlKBkDNJnXcN8QK4z' >>.ssh/trix_node_rsa
echo '5r0RKrKx/MS8/1teds8WPgXRRx3TiFryxr1HImbuTWs4aAxkgallJ1QCvXuDTDXT' >>.ssh/trix_node_rsa
echo 'InyZw6Vxe1FAHnwaWCe/1Lt+Hk5fogGyyHBPiLJWmuenOk9mNJk+s6sCgYEAxCJT' >>.ssh/trix_node_rsa
echo 'I1mcHQsrhYVG4WWQwO0Jg2kIPcU/YXlCXaXn8b0REU5s7zH51npq/HVaq004axWG' >>.ssh/trix_node_rsa
echo 'imwaMolVQmhv8IR64BAwESCZE/4cegjZSX9MNvQeCVIvAAricwgLK4QoZ5IbASKN' >>.ssh/trix_node_rsa
echo 'a2gnGoTiiyMtdEob3DIREJk9awsdeCUqpEN3j4UCgYB/F/IoqKv1HwzFfUN1DnTt' >>.ssh/trix_node_rsa
echo 'cmlBgCfA3gIgfTMW4SPDoWeJsc2rhAynE9iR9kGQVSPXzTEH8ozIU+7t9TwHp8Rx' >>.ssh/trix_node_rsa
echo 'O67bO0zdNSr/QRPZ7d5kude719ehpGl7PbOhLH7/RmRo7ulXPO3QD7VMuog6dxLl' >>.ssh/trix_node_rsa
echo '8r2cyrfM/pxELR6fV8+daQKBgBYt137w3DGAmNxRdPF6HcNjSqcckn0BuCgaoUGb' >>.ssh/trix_node_rsa
echo 'yD3S5oIxfyoRWbJCR6Ti1Gz4n3+kgIFYtiGu3ABVdQsawBZkXjshl43mN2wpYgDo' >>.ssh/trix_node_rsa
echo 'r0KrmlXtgDkeAfuGFlVGbZdAs2MOeDWEIp/iFQgs4y/6TWo6EynwWjynlh6G/Wpz' >>.ssh/trix_node_rsa
echo '4qpNAoGBAIyOl7bfJg0SZht9RwjtX5JCSrXpn5fbd5L9V/mn054cPq0jKXarrTqG' >>.ssh/trix_node_rsa
echo 'MqneRc+pefCE7wkFyimflkanhhR9Jrj5sCIzdqTBOAfl6sy+8pWBp5EFHcPHBby/' >>.ssh/trix_node_rsa
echo '/BNUwrQd0PbxIHruEMhxzFXSeiclnPhqWJuwi4rqvZ2k5WVhIlth' >>.ssh/trix_node_rsa
echo '-----END RSA PRIVATE KEY-----' >>.ssh/trix_node_rsa

chmod 400 .ssh/trix_node_rsa

echo 'host gitlab.dev.ivi.ru' >.ssh/config
echo '  hostname gitlab.dev.ivi.ru' >>.ssh/config
echo '  IdentityFile ~/.ssh/trix_node_rsa' >>.ssh/config
echo '  User tim'  >>.ssh/config

git clone -b master git@gitlab.dev.ivi.ru:tlansen/trix.git
mkdir .ssh
cp trix/backend/keys/trix_node_rsa .ssh/
chmod 400 .ssh/trix_node_rsa
sudo cp trix/nvenc_sdk_include/* /usr/include/

sudo cp /etc/apt/sources.list /etc/apt/sources.list.backup
sudo sed -i '/# deb-src/s/^#//g' /etc/apt/sources.list

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
sudo apt-get build-dep ffmpeg
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


