#!/bin/bash

# Flash a hasseb DALI Master in USB In-System programming mode.  To
# enter this mode, short JP1 and plug the device in and run
# "sudo bash update_firmware.sh"

# If only one device is plugged in, it appears as a volume with ID
# usb-NXP_LPC134X_IFLASH_ISP000000000-0:0

set -e

dev=/dev/disk/by-id/usb-NXP_LPC134X_IFLASH_ISP000000000-0:0

if test -L $dev ; then

  if umount $dev ; then
    echo Unmounted $dev
  fi

  dd bs=512 seek=4 oflag=sync if=new_firmware.bin of=$dev

  echo Firmware updated succesfully

else
  echo Device not present
fi
