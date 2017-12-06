# ===================
# Quicker boot:
# sudo vim /boot/grub/grub.cfg
#   find and replace
#       set timeout=2
#   with
#       set timeout=2
# ===================
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
sudo vim /etc/fuse.conf

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

# ===================
# Tools
# ===================
sudo apt-get install -y ffmpeg
sudo apt-get install -y mediainfo
sudo apt-get install -y sox
sudo apt-get install gpac
# ===================
# x265
# ===================

cd ~/
hg clone https://bitbucket.org/multicoreware/x265
cd x265/build/linux
./make-Makefiles.bash
# NATIVE_BUILD=ON
# STATIC_LINK_CRT=ON
# ENABLE_SHARED=OFF
make
sudo mv x265 /usr/local/bin/x265.08
./make-Makefiles.bash
# HIGH_BIT_DEPTH=ON
make
sudo mv x265 /usr/local/bin/x265.10
./make-Makefiles.bash
# MAIN12=ON
make
sudo mv x265 /usr/local/bin/x265.12

# ===================
# x264
# ===================

cd ~/
sudo apt-get install -y autoconf autogen
wget http://www.nasm.us/pub/nasm/releasebuilds/2.13.01/nasm-2.13.01.tar.bz2
tar xjvf nasm-2.13.01.tar.bz2
cd nasm-2.13.01
./autogen.sh
./configure
make
sudo make install

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


