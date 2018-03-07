# -*- coding: utf-8 -*-
#!/usr/bin/env python3.6


class Param:
    def __init__(self, name, has_value=True, default=None, value=None):
        self.name = name
        self.has_value = has_value
        self.value = value
        self.default = default

    def __str__(self):
        if self.has_value:
            if self.value is None:
                return ''
            if isinstance(self.value, str) and ' ' in self.value:
                return '{} "{}"'.format(self.name, self.value)
            return '{} {}'.format(self.name, self.value)
        if self.default or not self.value:
            return ''
        return self.name


class Executable:
    def __init__(self, exe):
        self.executable = exe

    def __str__(self):
        s = self.executable
        d = self.__dict__
        for k in d:
            e = d[k]
            if isinstance(e, Param):
                es = str(e)
                if len(es) == 0:
                    continue
                s += ' {}'.format(es)
        return s


class X265Params(Executable):

    def __init__(self):
        super().__init__('x265')
        """

Syntax: x265 [options] infile [-o] outfile
    infile can be YUV or Y4M
    outfile is raw HEVC bitstream

Executable Options:
-h/--help                        Show this help text and exit
   --fullhelp                    Show all options and exit
-V/--version                     Show version info and exit

Output Options:
-o/--output <filename>           Bitstream output file name
-D/--output-depth 8|10|12        Output bit depth (also internal bit depth). Default 8
   --log-level <string>          Logging level: none error warning info debug full. Default full
   --no-progress                 Disable CLI progress reports
   --csv <filename>              Comma separated log file, if csv-log-level > 0 frame level statistics, else one line per run
   --csv-log-level <integer>     Level of csv logging, if csv-log-level > 0 frame level statistics, else one line per run: 0-2

Input Options:
   --input <filename>            Raw YUV or Y4M input file name. `-` for stdin
   --y4m                         Force parsing of input stream as YUV4MPEG2 regardless of file extension
   --fps <float|rational>        Source frame rate (float or num/denom), auto-detected if Y4M
   --input-res WxH               Source picture size [w x h], auto-detected if Y4M
   --input-depth <integer>       Bit-depth of input file. Default 8
   --input-csp <string>          Chroma subsampling, auto-detected if Y4M
                                 0 - i400 (4:0:0 monochrome)
                                 1 - i420 (4:2:0 default)
                                 2 - i422 (4:2:2)
                                 3 - i444 (4:4:4)
   --dhdr10-info <filename>      JSON file containing the Creative Intent Metadata to be encoded as Dynamic Tone Mapping
   --[no-]dhdr10-opt             Insert tone mapping SEI only for IDR frames and when the tone mapping information changes. Default disabled
-f/--frames <integer>            Maximum number of frames to encode. Default all
   --seek <integer>              First frame to encode
   --[no-]interlace <bff|tff>    Indicate input pictures are interlace fields in temporal order. Default progressive
   --dither                      Enable dither if downscaling to 8 bit pixels. Default disabled
   --[no-]copy-pic               Copy buffers of input picture in frame. Default enabled
        """
        # Output Options:
        self.output = Param('--output', value=os.devnull)
        self.output_depth = Param('--output-depth')
        self.log_level = Param('--log-level')
        self.no_progress = Param('--no-progress', has_value=False)
        self.csv = Param('--csv')
        self.csv_log_level = Param('--csv-log-level')
        # Input Options:
        self.input = Param('--input', value='-')
        self.y4m = Param('--y4m', has_value=False)
        self.fps = Param('--fps')
        self.input_res = Param('--input-res')
        self.input_depth = Param('--input-depth')
        self.input_csp = Param('--input-csp')
        self.dhdr10_info = Param('--dhdr10-info')
        self.dhdr10_opt = Param('--dhdr10-opt', has_value=False, default=False)
        self.no_dhdr10_opt = Param('--no-dhdr10-opt', has_value=False, default=True)
        self.frames = Param('--frames')
        self.seek = Param('--seek')
        self.interlace = Param('--interlace')
        self.no_interlace = Param('--no-interlace', has_value=False, default=True)
        """
Quality reporting metrics:
   --[no-]ssim                   Enable reporting SSIM metric scores. Default disabled
   --[no-]psnr                   Enable reporting PSNR metric scores. Default disabled

Profile, Level, Tier:
-P/--profile <string>            Enforce an encode profile: main, main10, mainstillpicture
   --level-idc <integer|float>   Force a minimum required decoder level (as '5.0' or '50')
   --[no-]high-tier              If a decoder level is specified, this modifier selects High tier of that level
   --uhd-bd                      Enable UHD Bluray compatibility support
   --[no-]allow-non-conformance  Allow the encoder to generate profile NONE bitstreams. Default disabled

Threading, performance:
   --pools <integer,...>         Comma separated thread count per thread pool (pool per NUMA node)
                                 '-' implies no threads on node, '+' implies one thread per core on node
-F/--frame-threads <integer>     Number of concurrently encoded frames. 0: auto-determined by core count
   --[no-]wpp                    Enable Wavefront Parallel Processing. Default enabled
   --[no-]slices <integer>       Enable Multiple Slices feature. Default 1
   --[no-]pmode                  Parallel mode analysis. Default disabled
   --[no-]pme                    Parallel motion estimation. Default disabled
   --[no-]asm <bool|int|string>  Override CPU detection. Default: auto
        """
        # Quality reporting metrics
        self.ssim = Param('--ssim', has_value=False, default=False)
        self.no_ssim = Param('--no-ssim', has_value=False, default=True)
        self.psnr = Param('--psnr', has_value=False, default=False)
        self.no_psnr = Param('--no-psnr', has_value=False, default=True)

        # Profile, Level, Tier
        self.profile = Param('--profile')
        self.level_idc = Param('--level-idc')
        self.high_tier = Param('--high-tier', has_value=False, default=False)
        self.no_high_tier = Param('--no-high-tier', has_value=False, default=True)
        self.uhd_bd = Param('--uhd-bd', has_value=False, default=False)
        self.allow_non_conformance = Param('--allow-non-conformance', has_value=False, default=False)
        self.no_allow_non_conformance = Param('--no-allow-non-conformance', has_value=False, default=True)

        # Threading, performance
        self.pools = Param('--pools')
        self.frame_threads = Param('--frame-threads')
        self.wpp = Param('--wpp', has_value=False, default=True)
        self.no_wpp = Param('--no-wpp', has_value=False, default=False)
        self.slices = Param('--slices', default=1)
        self.no_slices = Param('--no-slices', has_value=False, default=False)
        self.pmode = Param('--pmode', has_value=False, default=False)
        self.no_pmode = Param('--no-pmode', has_value=False, default=True)
        self.pme = Param('--pme', has_value=False, default=False)
        self.no_pme = Param('--no-pme', has_value=False, default=True)
        self.asm = Param('--asm', default='auto')
        self.no_asm = Param('--no-asm', has_value=False, default=False)

        """
Presets:
-p/--preset <string>             Trade off performance for compression efficiency. Default medium
                                 ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow, or placebo
-t/--tune <string>               Tune the settings for a particular type of source or situation:
                                 psnr, ssim, grain, zerolatency, fastdecode
        """
        self.preset = Param('--preset', default='medium')
        self.tune = Param('--tune')
        """
Quad-Tree size and depth:
-s/--ctu <64|32|16>              Maximum CU size (WxH). Default 64
   --min-cu-size <64|32|16|8>    Minimum CU size (WxH). Default 8
   --max-tu-size <32|16|8|4>     Maximum TU size (WxH). Default 32
   --tu-intra-depth <integer>    Max TU recursive depth for intra CUs. Default 1
   --tu-inter-depth <integer>    Max TU recursive depth for inter CUs. Default 1
   --limit-tu <0..4>             Enable early exit from TU recursion for inter coded blocks. Default 0

Analysis:
   --rd <1..6>                   Level of RDO in mode decision 1:least....6:full RDO. Default 3
   --[no-]psy-rd <0..5.0>        Strength of psycho-visual rate distortion optimization, 0 to disable. Default 2.0
   --[no-]rdoq-level <0|1|2>     Level of RDO in quantization 0:none, 1:levels, 2:levels & coding groups. Default 0
   --[no-]psy-rdoq <0..50.0>     Strength of psycho-visual optimization in RDO quantization, 0 to disable. Default 0.0
   --dynamic-rd <0..4.0>         Strength of dynamic RD, 0 to disable. Default 0.00
   --[no-]ssim-rd                Enable ssim rate distortion optimization, 0 to disable. Default disabled
   --[no-]rd-refine              Enable QP based RD refinement for rd levels 5 and 6. Default disabled
   --[no-]early-skip             Enable early SKIP detection. Default disabled
   --[no-]rskip                  Enable early exit from recursion. Default enabled
   --[no-]tskip-fast             Enable fast intra transform skipping. Default disabled
   --[no-]splitrd-skip           Enable skipping split RD analysis when sum of split CU rdCost larger than none split CU rdCost for Intra CU. Default disabled
   --nr-intra <integer>          An integer value in range of 0 to 2000, which denotes strength of noise reduction in intra CUs. Default 0
   --nr-inter <integer>          An integer value in range of 0 to 2000, which denotes strength of noise reduction in inter CUs. Default 0
   --ctu-info <integer>          Enable receiving ctu information asynchronously and determine reaction to the CTU information (0, 1, 2, 4, 6) Default 0
                                    - 1: force the partitions if CTU information is present
                                    - 2: functionality of (1) and reduce qp if CTU information has changed
                                    - 4: functionality of (1) and force Inter modes when CTU Information has changed, merge/skip otherwise
                                    Enable this option only when planning to invoke the API function x265_encoder_ctu_info to copy ctu-info asynchronously
        """

        """
Coding tools:
-w/--[no-]weightp                Enable weighted prediction in P slices. Default enabled
   --[no-]weightb                Enable weighted prediction in B slices. Default disabled
   --[no-]cu-lossless            Consider lossless mode in CU RDO decisions. Default disabled
   --[no-]signhide               Hide sign bit of one coeff per TU (rdo). Default enabled
   --[no-]tskip                  Enable intra 4x4 transform skipping. Default disabled

Temporal / motion search options:
   --max-merge <1..5>            Maximum number of merge candidates. Default 2
   --ref <integer>               max number of L0 references to be allowed (1 .. 16) Default 3
   --limit-refs <0|1|2|3>        Limit references per depth (1) or CU (2) or both (3). Default 3
   --me <string>                 Motion search method dia hex umh star full. Default 1
-m/--subme <integer>             Amount of subpel refinement to perform (0:least .. 7:most). Default 2
   --merange <integer>           Motion search range. Default 57
   --[no-]rect                   Enable rectangular motion partitions Nx2N and 2NxN. Default disabled
   --[no-]amp                    Enable asymmetric motion partitions, requires --rect. Default disabled
   --[no-]limit-modes            Limit rectangular and asymmetric motion predictions. Default 0
   --[no-]temporal-mvp           Enable temporal MV predictors. Default enabled

Spatial / intra options:
   --[no-]strong-intra-smoothing Enable strong intra smoothing for 32x32 blocks. Default enabled
   --[no-]constrained-intra      Constrained intra prediction (use only intra coded reference pixels) Default disabled
   --[no-]b-intra                Enable intra in B frames in veryslow presets. Default disabled
   --[no-]fast-intra             Enable faster search method for angular intra predictions. Default disabled
   --rdpenalty <0..2>            penalty for 32x32 intra TU in non-I slices. 0:disabled 1:RD-penalty 2:maximum. Default 0

Slice decision options:
   --[no-]open-gop               Enable open-GOP, allows I slices to be non-IDR. Default enabled
-I/--keyint <integer>            Max IDR period in frames. -1 for infinite-gop. Default 250
-i/--min-keyint <integer>        Scenecuts closer together than this are coded as I, not IDR. Default: auto
   --gop-lookahead <integer>     Extends gop boundary if a scenecut is found within this from keyint boundary. Default 0
   --no-scenecut                 Disable adaptive I-frame decision
   --scenecut <integer>          How aggressively to insert extra I-frames. Default 40
   --scenecut-bias <0..100.0>    Bias for scenecut detection. Default 5.00
   --radl <integer>              Number of RADL pictures allowed in front of IDR. Default 0
   --intra-refresh               Use Periodic Intra Refresh instead of IDR frames
   --rc-lookahead <integer>      Number of frames for frame-type lookahead (determines encoder latency) Default 20
   --lookahead-slices <0..16>    Number of slices to use per lookahead cost estimate. Default 8
   --lookahead-threads <integer> Number of threads to be dedicated to perform lookahead only. Default 0
-b/--bframes <0..16>             Maximum number of consecutive b-frames. Default 4
   --bframe-bias <integer>       Bias towards B frame decisions. Default 0
   --b-adapt <0..2>              0 - none, 1 - fast, 2 - full (trellis) adaptive B frame scheduling. Default 2
   --[no-]b-pyramid              Use B-frames as references. Default enabled
   --qpfile <string>             Force frametypes and QPs for some or all frames
                                 Format of each line: framenumber frametype QP
                                 QP is optional (none lets x265 choose). Frametypes: I,i,K,P,B,b.
                                 QPs are restricted by qpmin/qpmax.
   --force-flush <integer>       Force the encoder to flush frames. Default 0
                                 0 - flush the encoder only when all the input pictures are over.
                                 1 - flush all the frames even when the input is not over. Slicetype decision may change with this option.
                                 2 - flush the slicetype decided frames only.

Rate control, Adaptive Quantization:
   --bitrate <integer>           Target bitrate (kbps) for ABR (implied). Default 0
-q/--qp <integer>                QP for P slices in CQP mode (implied). --ipratio and --pbration determine other slice QPs
   --crf <float>                 Quality-based VBR (0-51). Default 28.0
   --[no-]lossless               Enable lossless: bypass transform, quant and loop filters globally. Default disabled
   --crf-max <float>             With CRF+VBV, limit RF to this value. Default 0.000000
                                 May cause VBV underflows!
   --crf-min <float>             With CRF+VBV, limit RF to this value. Default 0.000000
                                 this specifies a minimum rate factor value for encode!
   --vbv-maxrate <integer>       Max local bitrate (kbit/s). Default 0
   --vbv-bufsize <integer>       Set size of the VBV buffer (kbit). Default 0
   --vbv-init <float>            Initial VBV buffer occupancy (fraction of bufsize or in kbits). Default 0.90
   --vbv-end <float>             Final VBV buffer emptiness (fraction of bufsize or in kbits). Default 0 (disabled)
   --vbv-end-fr-adj <float>      Frame from which qp has to be adjusted to achieve final decode buffer emptiness. Default 0
   --pass                        Multi pass rate control.
                                   - 1 : First pass, creates stats file
                                   - 2 : Last pass, does not overwrite stats file
                                   - 3 : Nth pass, overwrites stats file
   --[no-]multi-pass-opt-analysis   Refine analysis in 2 pass based on analysis information from pass 1
   --[no-]multi-pass-opt-distortion Use distortion of CTU from pass 1 to refine qp in 2 pass
   --stats                       Filename for stats file in multipass pass rate control. Default x265_2pass.log
   --[no-]analyze-src-pics       Motion estimation uses source frame planes. Default disable
   --[no-]slow-firstpass         Enable a slow first pass in a multipass rate control mode. Default enabled
   --[no-]strict-cbr             Enable stricter conditions and tolerance for bitrate deviations in CBR mode. Default disabled
   --analysis-save <filename>    Dump analysis info into the specified file. Default Disabled
   --analysis-load <filename>    Load analysis buffers from the file specified. Default Disabled
   --analysis-reuse-file <filename>    Specify file name used for either dumping or reading analysis data. Deault x265_analysis.dat
   --analysis-reuse-level <1..10>      Level of analysis reuse indicates amount of info stored/reused in save/load mode, 1:least..10:most. Default 5
   --refine-mv-type <string>     Reuse MV information received through API call. Supported option is avc. Default disabled - 0
   --scale-factor <int>          Specify factor by which input video is scaled down for analysis save mode. Default 0
   --refine-intra <0..3>         Enable intra refinement for encode that uses analysis-load.
                                    - 0 : Forces both mode and depth from the save encode.
                                    - 1 : Functionality of (0) + evaluate all intra modes at min-cu-size's depth when current depth is one smaller than min-cu-size's depth.
                                    - 2 : Functionality of (1) + irrespective of size evaluate all angular modes when the save encode decides the best mode as angular.
                                    - 3 : Functionality of (1) + irrespective of size evaluate all intra modes.
                                Default:0
   --refine-inter <0..3>         Enable inter refinement for encode that uses analysis-load.
                                    - 0 : Forces both mode and depth from the save encode.
                                    - 1 : Functionality of (0) + evaluate all inter modes at min-cu-size's depth when current depth is one smaller than
                                          min-cu-size's depth. When save encode decides the current block as skip(for all sizes) evaluate skip/merge.
                                    - 2 : Functionality of (1) + irrespective of size restrict the modes evaluated when specific modes are decided as the best mode by the save encode.
                                    - 3 : Functionality of (1) + irrespective of size evaluate all inter modes.
                                Default:0
   --[no-]refine-mv              Enable mv refinement for load mode. Default disabled
   --aq-mode <integer>           Mode for Adaptive Quantization - 0:none 1:uniform AQ 2:auto variance 3:auto variance with bias to dark scenes. Default 1
   --aq-strength <float>         Reduces blocking and blurring in flat and textured areas (0 to 3.0). Default 1.00
   --[no-]aq-motion              Adaptive Quantization based on the relative motion of each CU w.r.t., frame. Default disabled
   --qg-size <int>               Specifies the size of the quantization group (64, 32, 16, 8). Default 32
   --[no-]cutree                 Enable cutree for Adaptive Quantization. Default enabled
   --[no-]rc-grain               Enable ratecontrol mode to handle grains specifically. turned on with tune grain. Default disabled
   --ipratio <float>             QP factor between I and P. Default 1.40
   --pbratio <float>             QP factor between P and B. Default 1.30
   --qcomp <float>               Weight given to predicted complexity. Default 0.60
   --qpstep <integer>            The maximum single adjustment in QP allowed to rate control. Default 4
   --qpmin <integer>             sets a hard lower limit on QP allowed to ratecontrol. Default 0
   --qpmax <integer>             sets a hard upper limit on QP allowed to ratecontrol. Default 69
   --[no-]const-vbv              Enable consistent vbv. turned on with tune grain. Default disabled
   --cbqpoffs <integer>          Chroma Cb QP Offset [-12..12]. Default 0
   --crqpoffs <integer>          Chroma Cr QP Offset [-12..12]. Default 0
   --scaling-list <string>       Specify a file containing HM style quant scaling lists or 'default' or 'off'. Default: off
   --zones <zone0>/<zone1>/...   Tweak the bitrate of regions of the video
                                 Each zone is of the form
                                   <start frame>,<end frame>,<option>
                                   where <option> is either
                                       q=<integer> (force QP)
                                   or  b=<float> (bitrate multiplier)
   --lambda-file <string>        Specify a file containing replacement values for the lambda tables
                                 MAX_MAX_QP+1 floats for lambda table, then again for lambda2 table
                                 Blank lines and lines starting with hash(#) are ignored
                                 Comma is considered to be white-space

Loop filters (deblock and SAO):
   --[no-]deblock                Enable Deblocking Loop Filter, optionally specify tC:Beta offsets Default enabled
   --[no-]sao                    Enable Sample Adaptive Offset. Default enabled
   --[no-]sao-non-deblock        Use non-deblocked pixels, else right/bottom boundary areas skipped. Default disabled
   --[no-]limit-sao              Limit Sample Adaptive Offset types. Default disabled

VUI options:
   --sar <width:height|int>      Sample Aspect Ratio, the ratio of width to height of an individual pixel.
                                 Choose from 0=undef, 1=1:1("square"), 2=12:11, 3=10:11, 4=16:11,
                                 5=40:33, 6=24:11, 7=20:11, 8=32:11, 9=80:33, 10=18:11, 11=15:11,
                                 12=64:33, 13=160:99, 14=4:3, 15=3:2, 16=2:1 or custom ratio of <int:int>. Default 0
   --display-window <string>     Describe overscan cropping region as 'left,top,right,bottom' in pixels
   --overscan <string>           Specify whether it is appropriate for decoder to show cropped region: undef, show or crop. Default undef
   --videoformat <string>        Specify video format from undef, component, pal, ntsc, secam, mac. Default undef
   --range <string>              Specify black level and range of luma and chroma signals as full or limited Default limited
   --colorprim <string>          Specify color primaries from  bt709, unknown, reserved, bt470m, bt470bg, smpte170m,
                                 smpte240m, film, bt2020, smpte428, smpte431, smpte432. Default undef
   --transfer <string>           Specify transfer characteristics from bt709, unknown, reserved, bt470m, bt470bg, smpte170m,
                                 smpte240m, linear, log100, log316, iec61966-2-4, bt1361e, iec61966-2-1,
                                 bt2020-10, bt2020-12, smpte2084, smpte428, arib-std-b67. Default undef
   --colormatrix <string>        Specify color matrix setting from undef, bt709, fcc, bt470bg, smpte170m,
                                 smpte240m, GBR, YCgCo, bt2020nc, bt2020c, smpte2085, chroma-derived-nc, chroma-derived-c, ictcp. Default undef
   --chromaloc <integer>         Specify chroma sample location (0 to 5). Default of 0
   --master-display <string>     SMPTE ST 2086 master display color volume info SEI (HDR)
                                    format: G(x,y)B(x,y)R(x,y)WP(x,y)L(max,min)
   --max-cll <string>            Emit content light level info SEI as "cll,fall" (HDR)
   --[no-]hdr                    Control dumping of HDR SEI packet. If max-cll or master-display has non-zero values, this is enabled. Default disabled
   --[no-]hdr-opt                Add luma and chroma offsets for HDR/WCG content. Default disabled
   --min-luma <integer>          Minimum luma plane value of input source picture
   --max-luma <integer>          Maximum luma plane value of input source picture

Bitstream options:
   --[no-]repeat-headers         Emit SPS and PPS headers at each keyframe. Default disabled
   --[no-]info                   Emit SEI identifying encoder and parameters. Default enabled
   --[no-]hrd                    Enable HRD parameters signaling. Default disabled
   --[no-]temporal-layers        Enable a temporal sublayer for unreferenced B frames. Default disabled
   --[no-]aud                    Emit access unit delimiters at the start of each access unit. Default disabled
   --hash <integer>              Decoded Picture Hash SEI 0: disabled, 1: MD5, 2: CRC, 3: Checksum. Default 0
   --log2-max-poc-lsb <integer>  Maximum of the picture order count
   --[no-]vui-timing-info        Emit VUI timing information in the bistream. Default enabled
   --[no-]vui-hrd-info           Emit VUI HRD information in the bistream. Default enabled
   --[no-]opt-qp-pps             Dynamically optimize QP in PPS (instead of default 26) based on QPs in previous GOP. Default disabled
   --[no-]opt-ref-list-length-pps  Dynamically set L0 and L1 ref list length in PPS (instead of default 0) based on values in last GOP. Default disabled
   --[no-]multi-pass-opt-rps     Enable storing commonly used RPS in SPS in multi pass mode. Default disabled
   --[no-]opt-cu-delta-qp        Optimize to signal consistent CU level delta QPs in frame. Default disabled

Reconstructed video options (debugging):
-r/--recon <filename>            Reconstructed raw image YUV or Y4M output file name
   --recon-depth <integer>       Bit-depth of reconstructed raw image file. Defaults to input bit depth, or 8 if Y4M
   --recon-y4m-exec <string>     pipe reconstructed frames to Y4M viewer, ex:"ffplay -i pipe:0 -autoexit"
   --lowpass-dct                 Use low-pass subband dct approximation. Default disabled

Executable return codes:
    0 - encode successful
    1 - unable to parse command line
    2 - unable to open encoder
    3 - unable to generate stream headers
    4 - encoder abort


Complete documentation may be found at http://x265.readthedocs.org/en/default/cli.html

        """

