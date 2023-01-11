#!/bin/bash
set -xe

# sender default
FLIP_MODE=2

if [ -z "$1" ]; then
   echo >&2 "$0 SENSOR_ID"
   exit 1
fi

SENSOR_ID=$1
V4L2LOOPBACK_DEV=/dev/video1
#V4L2LOOPBACK_DEV=/dev/video${V4L2LOOPBACK_MAP[$SENSOR_ID]}
V4L2LOOPBACK_DEV_0=/dev/video3
V4L2LOOPBACK_DEV_1=/dev/video4
V4L2LOOPBACK_DEV_2=/dev/video5
V4L2LOOPBACK_DEV_3=/dev/video6
#: ${FILP_MODE:=0}

: ${SOURCE_WIDTH:=3264}
: ${SOURCE_HEIGHT:=2464}
: ${SOURCE_FPS:=21/1}
: ${HIGHFPS_FPS:=5/1}

# V4L2LOOPBACK_DEV_0 (center large part of camera)
: ${DEV_0_TOP:=862}
: ${DEV_0_BOTTOM:=1601}
: ${DEV_0_LEFT:=816}
: ${DEV_0_RIGHT:=2448}
: ${DEV_0_WIDTH:=$(( ${DEV_0_RIGHT} - ${DEV_0_LEFT}))}
: ${DEV_0_HEIGHT:=$(( ${DEV_0_BOTTOM} - ${DEV_0_TOP}))}
# V4L2LOOPBACK_DEV_1 (left part of camera)
: ${DEV_1_TOP:=205}
: ${DEV_1_BOTTOM:=2259}
: ${DEV_1_LEFT:=272}
: ${DEV_1_RIGHT:=816}
: ${DEV_1_WIDTH:=$(( ${DEV_1_RIGHT} - ${DEV_1_LEFT}))}
: ${DEV_1_HEIGHT:=$(( ${DEV_1_BOTTOM} - ${DEV_1_TOP}))}
# V4L2LOOPBACK_DEV_2 (center part of camera)
: ${DEV_2_TOP:=205}
: ${DEV_2_BOTTOM:=2259}
: ${DEV_2_LEFT:=1360}
: ${DEV_2_RIGHT:=1904}
: ${DEV_2_WIDTH:=$(( ${DEV_2_RIGHT} - ${DEV_2_LEFT}))}
: ${DEV_2_HEIGHT:=$(( ${DEV_2_BOTTOM} - ${DEV_2_TOP}))}
# V4L2LOOPBACK_DEV_3 (right part of camera)
: ${DEV_3_TOP:=205}
: ${DEV_3_BOTTOM:=2259}
: ${DEV_3_LEFT:=2448}
: ${DEV_3_RIGHT:=2992}
: ${DEV_3_WIDTH:=$(( ${DEV_3_RIGHT} - ${DEV_3_LEFT}))}
: ${DEV_3_HEIGHT:=$(( ${DEV_3_BOTTOM} - ${DEV_3_TOP}))}

gst-launch-1.0 nvarguscamerasrc sensor-id=${SENSOR_ID} ! \
    "video/x-raw(memory:NVMM), width=(int)${SOURCE_WIDTH}, height=(int)${SOURCE_HEIGHT}, format=(string)NV12, framerate=(fraction)${SOURCE_FPS}" ! \
    tee name=t ! \
    queue ! \
        nvvidconv flip-method=${FLIP_MODE} ! \
        "video/x-raw(memory:NVMM), format=(string)I420, width=$(( ${SOURCE_WIDTH} / 1 )), height=$(( ${SOURCE_HEIGHT} / 1 ))" ! \
        videorate ! \
        "video/x-raw(memory:NVMM), framerate=${HIGHFPS_FPS}" ! \
        nvvidconv \
	top=${DEV_0_TOP} left=${DEV_0_LEFT} right=${DEV_0_RIGHT} bottom=${DEV_0_BOTTOM} ! \
        "video/x-raw, width=${DEV_0_WIDTH}, height=${DEV_0_HEIGHT}" ! \
	identity drop-allocation=1 ! \
        v4l2sink device=${V4L2LOOPBACK_DEV_0} t. ! \
    queue ! \
        nvvidconv flip-method=${FLIP_MODE} ! \
        "video/x-raw(memory:NVMM), format=(string)I420, width=$(( ${SOURCE_WIDTH} / 1 )), height=$(( ${SOURCE_HEIGHT} / 1 ))" ! \
        videorate ! \
        "video/x-raw(memory:NVMM), framerate=${HIGHFPS_FPS}" ! \
        nvvidconv \
	top=${DEV_1_TOP} left=${DEV_1_LEFT} right=${DEV_1_RIGHT} bottom=${DEV_1_BOTTOM} ! \
        "video/x-raw, width=${DEV_1_WIDTH}, height=${DEV_1_HEIGHT}" ! \
	identity drop-allocation=1 ! \
        v4l2sink device=${V4L2LOOPBACK_DEV_1} t. ! \
    queue ! \
        nvvidconv flip-method=${FLIP_MODE} ! \
        "video/x-raw(memory:NVMM), format=(string)I420, width=$(( ${SOURCE_WIDTH} / 1 )), height=$(( ${SOURCE_HEIGHT} / 1 ))" ! \
        videorate ! \
        "video/x-raw(memory:NVMM), framerate=${HIGHFPS_FPS}" ! \
        nvvidconv \
	top=${DEV_2_TOP} left=${DEV_2_LEFT} right=${DEV_2_RIGHT} bottom=${DEV_2_BOTTOM} ! \
        "video/x-raw, width=${DEV_2_WIDTH}, height=${DEV_2_HEIGHT}" ! \
	identity drop-allocation=1 ! \
        v4l2sink device=${V4L2LOOPBACK_DEV_2} t. ! \
    queue ! \
        nvvidconv flip-method=${FLIP_MODE} ! \
        "video/x-raw(memory:NVMM), format=(string)I420, width=$(( ${SOURCE_WIDTH} / 1 )), height=$(( ${SOURCE_HEIGHT} / 1 ))" ! \
        videorate ! \
        "video/x-raw(memory:NVMM), framerate=${HIGHFPS_FPS}" ! \
        nvvidconv \
	top=${DEV_3_TOP} left=${DEV_3_LEFT} right=${DEV_3_RIGHT} bottom=${DEV_3_BOTTOM} ! \
        "video/x-raw, width=${DEV_3_WIDTH}, height=${DEV_3_HEIGHT}" ! \
	identity drop-allocation=1 ! \
        v4l2sink device=${V4L2LOOPBACK_DEV_3} t. ! \
    queue ! \
        nvvidconv flip-method=${FLIP_MODE} ! \
        "video/x-raw(memory:NVMM), format=(string)I420, width=$(( ${SOURCE_WIDTH} / 1 )), height=$(( ${SOURCE_HEIGHT} / 1 ))" ! \
        videorate ! \
        "video/x-raw(memory:NVMM), framerate=${HIGHFPS_FPS}" ! \
        nvvidconv ! \
        "video/x-raw" ! \
	identity drop-allocation=1 ! \
        v4l2sink device=${V4L2LOOPBACK_DEV}
