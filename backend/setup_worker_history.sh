    1  sudo vim /etc/network/interfaces
    2  ip a
    3  sudo /etc/init.d/networking restart
    4  ip a
    5  sudo shutdown -P 0
    6  ip a
    7  sudo vim /etc/network/interfaces
    8  sudo /etc/init.d/networking restart
    9  ip a
   10  sudo vim /etc/hosts
   11  sudo vim /etc/hostname
   12  sudo vim /etc/network/interfaces
   13  sudo /etc/init.d/networking restart
   14  sudo add-apt-repository ppa:jonathonf/python-3.6
   15  sudo apt-get update
   16  sudo apt-get install python3.6
   17  sudo apt-get install python3-pip
   18  python3.6 -m pip install --upgrade pip
   19  sudo python3.6 -m pip install psycopg2
   20  sudo -H python3.6 -m pip install Unidecode
   21  sudo -H python3.6 -m pip install python_slugify
   22  sudo apt-get install ffmpeg
   23  sudo apt-get install mediainfo
   24  sudo apt-get install sox
   25  sudo apt-get install mercurial cmake cmake-curses-gui build-essential
   26  hg clone https://bitbucket.org/multicoreware/x265
   27  find x265/build/linux
   28  cd x265/build/linux
   29  ./make-Makefiles.bash
   30  ls
   31  sudo apt-get install yasm
   32  cd ../../..
   33  find x265/build/linux
   34  vim x265/build/linux/make-Makefiles.bash
   35  cd x265/build/linux
   36  ./make-Makefiles.bash
   37  make
   38  sudo mv x265 /usr/local/bin/x265.08
   39  x265.08
   40  ./make-Makefiles.bash
   41  make
   42  sudo mv x265 /usr/local/bin/x265.10
   43  ./make-Makefiles.bash
   44  make
   45  sudo mv x265 /usr/local/bin/x265.12
   46  cd ~/
   47  sudo apt-get install -y autoconf autogen
   48  ls
   49  wget http://www.nasm.us/pub/nasm/releasebuilds/2.13.01/nasm-2.13.01.tar.bz2
   50  tar xjvf nasm-2.13.01.tar.bz2
   51  cd nasm-2.13.01/
   52  ./autogen.sh
   53  ./configure
   54  make
   55  sudo make install
   56  cd ..
   57  git clone http://git.videolan.org/git/x264.git
   58  cd x264/
   59  ./configure --disable-interlaced --bit-depth=8 --disable-avs --disable-swscale --disable-lavf --disable-ffms --disable-gpac --disable-lsmash
   60  make
   61  sudo mv x264 /usr/local/bin/x264.08
   62  ./configure --disable-interlaced --bit-depth=10 --disable-avs --disable-swscale --disable-lavf --disable-ffms --disable-gpac --disable-lsmash
   63  make
   64  sudo mv x264 /usr/local/bin/x264.10
   65  cd ..
   66  rm nasm-2.13.01.tar.bz2
   67  rm -rf nasm-2.13.01/
   68  ls
   69  rm -rf x26*
   70  ls
   71  history
   72  history >history.sh
   73  mkdir -p trix/backend
   74  git clone http://gitlab.dev.ivi.ru/tlansen/trix.git
   75  rm -rf trix/backend
   76  git clone http://gitlab.dev.ivi.ru/tlansen/trix.git

   92  sudo apt-get install libavutil-dev
   85  mkdir -p /home/tim/trix/tools/trim/obj/x64/Debug/
   86  g++ -c -x c++ /home/tim/trix/tools/trim/crc_pattern.cpp -g2 -gdwarf-2 -o "/home/tim/trix/tools/trim/obj/x64/Debug/crc_pattern.o" -Wall -Wswitch -W"no-deprecated-declarations" -W"empty-body" -Wconversion -W"return-type" -Wparentheses -W"no-format" -Wuninitialized -W"unreachable-code" -W"unused-function" -W"unused-value" -W"unused-variable" -O0 -fno-strict-aliasing -fno-omit-frame-pointer -DLINUX -D__STDC_CONSTANT_MACROS -DDEBUG -fthreadsafe-statics -fexceptions -frtti -std=c++11 -W"no-write-strings"
   87  g++ -c -x c++ /home/tim/trix/tools/trim/support.cpp -g2 -gdwarf-2 -o "/home/tim/trix/tools/trim/obj/x64/Debug/support.o" -Wall -Wswitch -W"no-deprecated-declarations" -W"empty-body" -Wconversion -W"return-type" -Wparentheses -W"no-format" -Wuninitialized -W"unreachable-code" -W"unused-function" -W"unused-value" -W"unused-variable" -O0 -fno-strict-aliasing -fno-omit-frame-pointer -DLINUX -D__STDC_CONSTANT_MACROS -DDEBUG -fthreadsafe-statics -fexceptions -frtti -std=c++11 -W"no-write-strings"
   90  g++ -c -x c++ /home/tim/trix/tools/trim/trim.cpp -g2 -gdwarf-2 -o "/home/tim/trix/tools/trim/obj/x64/Debug/trim.o" -Wall -Wswitch -W"no-deprecated-declarations" -W"empty-body" -Wconversion -W"return-type" -Wparentheses -W"no-format" -Wuninitialized -W"unreachable-code" -W"unused-function" -W"unused-value" -W"unused-variable" -O0 -fno-strict-aliasing -fno-omit-frame-pointer -DLINUX -D__STDC_CONSTANT_MACROS -DDEBUG -fthreadsafe-statics -fexceptions -frtti -std=c++11 -W"no-write-strings"
   93  g++ -c -x c++ /home/tim/trix/tools/trim/trim.cpp -g2 -gdwarf-2 -o "/home/tim/trix/tools/trim/obj/x64/Debug/trim.o" -Wall -Wswitch -W"no-deprecated-declarations" -W"empty-body" -Wconversion -W"return-type" -Wparentheses -W"no-format" -Wuninitialized -W"unreachable-code" -W"unused-function" -W"unused-value" -W"unused-variable" -O0 -fno-strict-aliasing -fno-omit-frame-pointer -DLINUX -D__STDC_CONSTANT_MACROS -DDEBUG -fthreadsafe-statics -fexceptions -frtti -std=c++11 -W"no-write-strings"
   95  g++ -o trim.out -Wl,--no-undefined -Wl,-z,relro -Wl,-z,now -Wl,-z,noexecstack /home/tim/trix/tools/trim/obj/x64/Debug/crc_pattern.o /home/tim/trix/tools/trim/obj/x64/Debug/support.o /home/tim/trix/tools/trim/obj/x64/Debug/trim.o -lavutil
   97  sudo mv trim.out /usr/local/bin/
