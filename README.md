# rt-smart canaan porting

## 测试过的板子

- K230-evb

## 下载依赖的软件包

在软件包无需变更的情况下只须执行一次
```
source ~/.env/env.sh
pkgs --update
```

## 编译器

通用版(rv64imafdc-lp64):
https://download.rt-thread.org/download/rt-smart/toolchains/riscv64gc-linux-musleabi_for_x86_64-pc-linux-gnu_222725-8a397096c1.tar.bz2

V指令版(rv64imafdcv-lp64d):
https://download.rt-thread.org/rt-smart/riscv64/riscv64-unknown-linux-musl-rv64imafdcv-lp64d-20230608.tar.bz2


## 将根文件系统编译进内核

`备注`：省略此步骤任然可以观察到内核启动，且能执行其他文件系统(自己挂载SD卡)中的静态编译程序。
如果不想自己制作也可以解压`prebuild/cromfs_data.zip`到`applications`目录中，然后编译内核即可。

为了方便测试，这里将根文件系统制作成CROMFS格式转换成C代码编译进内核。

1. 在 https://github.com/RT-Thread/userapps 页面下载riscv64预编译镜像
2. 解压后将其中的ext4.img挂载到一个目录中
```
sudo mount ext4.img dir
```
3. 删除其中一些不必要的文件以减小内核体积
```
cd dir
du -ha                              # 查看文件大小
sudo rm -rf www usr/share/fonts tc

```
4. 生成cromfs文件
工具位于 https://github.com/RT-Thread/userapps/tree/main/tools/cromfs
```
sudo ./cromfs-tool-x64 dir crom.img ./            # 将生成的cromfs_data.c放入applications目录
```

## 编译

### 一步完成
```
export RTT_ROOT=../rt-thread # 如果本目录不放在rt-thread/bsp下，请设置此环境变量
export RTT_EXEC_PATH=/mnt/e/tools/riscv64gc/bin # 你自己的编译器路径

scons -j8 all=1
```

### 分步完成
* 1. 编译RT-Thread
```
export RTT_EXEC_PATH=/mnt/e/tools/riscv64gc/bin # 你自己的编译器路径

scons -j8

```

* 2. 编译opensbi & 生成烧录文件
```
./mkfm.sh /mnt/e/tools/riscv64gc/bin/riscv64-unknown-linux-musl- # 你自己的编译器
```
此处会把`rtthread.bin`编译进opensbi

### 自定义-march与-mabi参数

默认-march=rv64imafdc,-mabi=lp64。
如果你想修改他们可以在执行scons时传入参数，如:
```
export RTT_EXEC_PATH=~/.tools/gnu_gcc/riscv64-linux-musleabi_for_x86_64-pc-linux-gnu/bin

scons -j8 march=rv64imafdcv mabi=lp64d all=1
```
备注：使用V扩展需要使用`scons --menuconfig`开启内核对它的支持
```
    RT-Thread online packages  --->
    Drivers Configuration  --->
[*] Enable RISCV Vector
```

## 烧录rtt_system.bin

1. 参照 https://github.com/kendryte/k230_sdk 烧入预编译镜像
2. 通过另一个核上运行的linux烧录rtt
```
ifconfig eth0 up;ifconfig eth0 192.168.2.2;cd /tmp;tftp -r rtt_system.bin -g 192.168.2.20;dd if=rtt_system.bin of=/dev/mmcblk1p1;reboot

```

## 用uboot从sd卡fat分区加载rtt_system.bin

在`快起`特性关闭的情况下，从小核控制台进入uboot操作界面，输入如下命令：
```
fatload mmc 1:4 $ramdisk_addr rtt_system.bin;k230_boot mem $ramdisk_addr 0x$filesize

```

存为环境变量,可使用`run rtt`启动
```
setenv rtt 'fatload mmc 1:4 $ramdisk_addr rtt_system.bin;k230_boot mem $ramdisk_addr 0x$filesize'
saveenv

```


`备注`: 随后RT-Thread启动界面显示在大核控制台。

## 注意事项
* 1. `#define KERNEL_VADDR_START 0xFFFFFFC000220000`这个地址和运行的物理地址有关，修改需谨慎。
* 2. 确保`#define ARCH_REMAP_KERNEL`这个定义存在。
* 3. 双系统运行时，启动设备(SD卡)被linux直接访问，默认rt-thread未开启sdio驱动，要想在rt-thread中直接访问SD卡，请开启sdio驱动后用uboot手动启动rt-thread。
