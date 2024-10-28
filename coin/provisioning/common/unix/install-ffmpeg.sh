#!/usr/bin/env bash
# Copyright (C) 2023 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

# This script will build and install FFmpeg static libs
set -ex

source "${BASH_SOURCE%/*}/../unix/ffmpeg-installation-utils.sh"

os="$1"
build_type=$(get_ffmpeg_build_type "$2")

ffmpeg_source_dir=$(download_ffmpeg)
ffmpeg_name=$(basename $ffmpeg_source_dir)
ffmpeg_config_options=$(get_ffmpeg_config_options $build_type)

install_ff_nvcodec_headers() {
  local nv_codec_version="11.1" # use 11.1 to ensure compatibility with 470 nvidia drivers; might be upated to 12.0
  local nv_codec_url_public="https://github.com/FFmpeg/nv-codec-headers/archive/refs/heads/sdk/$nv_codec_version.zip"
  local nv_codec_url_cached="http://ci-files01-hki.ci.qt.io/input/ffmpeg/nv-codec-headers/nv-codec-headers-sdk-$nv_codec_version.zip"
  local nv_codec_sha1="ceb4966ab01b2e41f02074675a8ac5b331bf603e"
  #nv_codec_sha1="4f30539f8dd31945da4c3da32e66022f9ca59c08" // 12.0
  local target_dir="$HOME"
  local nv_codec_dir="$target_dir/nv-codec-headers-sdk-$nv_codec_version"

  if [ ! -d  "$nv_codec_dir" ]; then
    source "${BASH_SOURCE%/*}/../unix/InstallFromCompressedFileFromURL.sh"
    InstallFromCompressedFileFromURL "$nv_codec_url_cached" "$nv_codec_url_public" "$nv_codec_sha1" "$target_dir" ""
  fi

  sudo make -C "$nv_codec_dir" install -j

  # Might be not detected by default on RHEL
  export PKG_CONFIG_PATH="$PKG_CONFIG_PATH:/usr/local/lib/pkgconfig"
}

fix_openssl3_pc_files() {
  # On RHEL 8, openssl3 pc files are libopenssl3.pc, libssl3.pc, libcrypto3.pc,
  # and FFmpeg cannot find them. Instead, it finds FFmpeg 1.x.x if it's installed.
  # The function fixes the files with copying them to a custom directory

  local openssl3_pcfiledir=$(pkg-config --variable=pcfiledir openssl3)
  if [ ! -n  "$openssl3_pcfiledir" ]; then
    return
  fi

  local pcfiles=("libssl" "libcrypto" "openssl")

  for pcfile in ${pcfiles[@]}; do
    if [ ! -f "$openssl3_pcfiledir/${pcfile}3.pc" ]; then
      echo "pkgconfig has found openssl3 but the file $openssl3_pcfiledir/${pcfile}3.pc does't exist"
      return
    fi
  done

  local new_pkgconfig_dir="$ffmpeg_source_dir/openssl3_pkgconfig"
  mkdir -p $new_pkgconfig_dir

  for pcfile in ${pcfiles[@]}; do
    sed -E '/^Requires(\.private)?:/s/ (libssl|libcrypto)3/ \1/g;' "$openssl3_pcfiledir/${pcfile}3.pc" > "$new_pkgconfig_dir/${pcfile}.pc"
  done

  export PKG_CONFIG_PATH="$new_pkgconfig_dir:$PKG_CONFIG_PATH"
}

build_ffmpeg() {
  local arch="$1"
  local prefix="$2"
  local build_dir="$ffmpeg_source_dir/build/$arch"
  mkdir -p "$build_dir"
  pushd "$build_dir"

  if [ -z  "$prefix" ]
  then prefix="/usr/local/$ffmpeg_name"
  fi

  if [ -n "$arch" ]
  then cc="clang -arch $arch"
  fi

  # shellcheck disable=SC2086
  if [ -n "$arch" ]
  then "$ffmpeg_source_dir/configure" $ffmpeg_config_options --prefix="$prefix" --enable-cross-compile --arch="$arch" --cc="$cc"
  else "$ffmpeg_source_dir/configure" $ffmpeg_config_options --prefix="$prefix"
  fi
  make install DESTDIR="$build_dir/installed" -j4
  popd
}

if [ "$os" == "linux" ]; then
  install_ff_nvcodec_headers

  ffmpeg_config_options+=" --enable-openssl"
  fix_openssl3_pc_files
  echo "pkg-config openssl version: $(pkg-config --modversion openssl)"

  build_ffmpeg

  output_dir="$ffmpeg_source_dir/build/installed/usr/local/$ffmpeg_name"

  if [ "$build_type" == "shared" ]; then
    fix_dependencies="${BASH_SOURCE%/*}/../shared/fix_ffmpeg_dependencies.sh"
    "$fix_dependencies" "$output_dir"
  fi

  sudo mv "$output_dir" "/usr/local"

elif [ "$os" == "macos" ] || [ "$os" == "macos-universal" ]; then
  brew install yasm
  export MACOSX_DEPLOYMENT_TARGET=12
  fix_relative_dependencies="${BASH_SOURCE%/*}/../macos/fix_relative_dependencies.sh"

  if [ "$os" == "macos"  ]; then
    build_ffmpeg
    install_dir="$ffmpeg_source_dir/build/installed"
    "$fix_relative_dependencies" "$install_dir/usr/local/$ffmpeg_name/lib"
    sudo mv "$install_dir/usr/local/$ffmpeg_name" "/usr/local"
  else
    build_ffmpeg "arm64"
    build_ffmpeg "x86_64"

    arm64_install_dir="$ffmpeg_source_dir/build/arm64/installed"
    x86_64_install_dir="$ffmpeg_source_dir/build/x86_64/installed"

    "$fix_relative_dependencies" "$arm64_install_dir/usr/local/$ffmpeg_name/lib"
    "$fix_relative_dependencies" "$x86_64_install_dir/usr/local/$ffmpeg_name/lib"

    sudo "${BASH_SOURCE%/*}/../macos/makeuniversal.sh" "$arm64_install_dir" "$x86_64_install_dir"
  fi
fi

set_ffmpeg_dir_env_var "FFMPEG_DIR" "/usr/local/$ffmpeg_name"

